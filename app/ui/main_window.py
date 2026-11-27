"""Main FluentWindow orchestrating all OC-Studio pages and background workers."""

from __future__ import annotations

import os
from typing import Any, Dict, List

from PySide6.QtCore import Qt
from qfluentwidgets import (
    FluentIcon,
    FluentWindow,
    InfoBar,
    InfoBarPosition,
    MessageBox,
    NavigationItemPosition,
    Theme,
    isDarkTheme,
    setTheme,
)

from app import APP_NAME, APP_VERSION
from app.config import AppSettings
from app.core_adapter import CoreAdapter, CoreEventBridge, PromptRequest
from app.core_updater import (
    CoreVersionInfo,
    check_upstream_core_update,
    get_local_core_info,
    sync_upstream_core,
)
from app.i18n import Translator
from app.ui.dialogs import CorePromptDialog, DetailErrorDialog
from app.ui.pages.build_page import BuildPage
from app.ui.pages.customize_page import CustomizePage
from app.ui.pages.home_page import HomePage
from app.ui.pages.macos_page import MacOSPage
from app.ui.pages.report_page import ReportPage
from app.ui.pages.settings_page import SettingsPage
from app.ui.widgets.config_diff_viewer import ConfigDiffDialog
from app.workers import TaskWorker, UiEventRelay


def apply_theme(theme_name: str) -> None:
    mapping = {
        "light": Theme.LIGHT,
        "dark": Theme.DARK,
        "auto": Theme.AUTO,
    }
    setTheme(mapping.get(theme_name, Theme.AUTO), lazy=False)


class MainWindow(FluentWindow):
    """Top-level Fluent window for OC-Studio."""

    def __init__(self) -> None:
        self.settings = AppSettings.load()
        self.tr_mgr = Translator(self.settings.language)
        # Apply saved theme BEFORE initializing FluentWindow so titlebar/Mica match immediately
        apply_theme(self.settings.theme)

        super().__init__()

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1120, 760)
        self.setMinimumSize(900, 640)
        self.navigationInterface.setExpandWidth(200)

        # Bridge & Core adapter
        self.relay = UiEventRelay(self)
        self.bridge = CoreEventBridge()
        self.bridge.on_log = self.relay.log_received.emit
        self.bridge.on_build_progress = self.relay.build_progress.emit
        self.bridge.on_download_progress = self.relay.download_progress.emit
        self.bridge.on_prompt = self.relay.ask_user_blocking

        self.adapter = CoreAdapter(self.settings, self.bridge)
        self._active_workers: List[TaskWorker] = []

        # Pages
        self.home_page = HomePage(self.tr_mgr, self)
        self.report_page = ReportPage(self.tr_mgr, self)
        self.macos_page = MacOSPage(self.tr_mgr, self)
        self.customize_page = CustomizePage(self.tr_mgr, self)
        self.build_page = BuildPage(self.tr_mgr, self)
        self.settings_page = SettingsPage(self.settings, self.tr_mgr, self)

        self._init_navigation()
        self._connect_signals()
        self._sync_window_theme()

        # Load initial local core version info
        local_info = get_local_core_info()
        self.home_page.update_core_info(local_info)
        self.settings_page.update_core_info(local_info)

    def _init_navigation(self) -> None:
        self.addSubInterface(self.home_page, FluentIcon.HOME, self.tr_mgr.t("nav.home"))
        self.addSubInterface(self.report_page, FluentIcon.DOCUMENT, self.tr_mgr.t("nav.report"))
        self.addSubInterface(self.macos_page, FluentIcon.APPLICATION, self.tr_mgr.t("nav.macos"))
        self.addSubInterface(self.customize_page, FluentIcon.DEVELOPER_TOOLS, self.tr_mgr.t("nav.customize"))
        self.addSubInterface(self.build_page, FluentIcon.PLAY, self.tr_mgr.t("nav.build"))
        self.addSubInterface(
            self.settings_page,
            FluentIcon.SETTING,
            self.tr_mgr.t("nav.settings"),
            NavigationItemPosition.BOTTOM,
        )

    def _connect_signals(self) -> None:
        # Relay signals (background -> UI)
        self.relay.log_received.connect(self.build_page.append_log)
        self.relay.build_progress.connect(self.build_page.on_build_progress)
        self.relay.download_progress.connect(self.build_page.on_download_progress)
        self.relay.prompt_requested.connect(self._handle_core_prompt)

        # Home page
        self.home_page.start_requested.connect(lambda: self.switchTo(self.report_page))
        self.home_page.open_diff_requested.connect(self._on_open_diff_viewer)
        self.home_page.open_settings_requested.connect(lambda: self.switchTo(self.settings_page))

        # Page 1: Report
        self.report_page.export_requested.connect(self._on_export_report)
        self.report_page.import_requested.connect(self._on_import_report)
        self.report_page.acpi_requested.connect(self._on_load_acpi)
        self.report_page.next_requested.connect(lambda: self.switchTo(self.macos_page))

        # Page 2: macOS
        self.macos_page.version_applied.connect(self._on_apply_macos_version)
        self.macos_page.next_requested.connect(lambda: self.switchTo(self.customize_page))

        # Page 3: Customize
        self.customize_page.acpi_toggled.connect(self._on_acpi_toggled)
        self.customize_page.kext_toggled.connect(self._on_kext_toggled)
        self.customize_page.smbios_selected.connect(self._on_smbios_selected)
        self.customize_page.smbios_restore_requested.connect(self._on_smbios_restore)
        self.customize_page.audio_layout_selected.connect(self._on_audio_layout_selected)
        self.customize_page.audio_layout_restore_requested.connect(self._on_audio_layout_restore)
        self.customize_page.next_requested.connect(lambda: self.switchTo(self.build_page))

        # Page 4: Build
        self.build_page.build_requested.connect(self._on_start_build)
        self.build_page.open_result_requested.connect(self._open_folder)
        self.build_page.open_diff_requested.connect(self._on_open_diff_viewer)

        # Settings
        self.settings_page.theme_changed.connect(self._on_theme_changed)
        self.settings_page.language_changed.connect(self._on_language_changed)
        self.settings_page.settings_changed.connect(self._on_settings_saved)
        self.settings_page.check_core_requested.connect(self._on_check_core_update)
        self.settings_page.sync_core_requested.connect(self._on_sync_core)

    # ------------------------------------------------------------------
    # Live Theme & Language Switching
    # ------------------------------------------------------------------
    def _sync_window_theme(self) -> None:
        """Ensure FluentWindow backdrop, Mica/DWM dark mode, and transparent scroll areas repaint immediately."""
        # Disable Mica on Windows so switching Light/Dark gives an unmistakable solid Fluent canvas
        if os.name == "nt" and hasattr(self, "setMicaEffectEnabled"):
            self.setMicaEffectEnabled(False)
        if hasattr(self, "_updateBackgroundColor"):
            self._updateBackgroundColor()
        for scroll_page in (
            self.home_page,
            self.report_page,
            self.macos_page,
            self.build_page,
            self.settings_page,
            self.customize_page.acpi_scroll,
            self.customize_page.kext_scroll,
            self.customize_page.smbios_scroll,
            self.customize_page.audio_scroll,
        ):
            scroll_page.enableTransparentBackground()
        self.update()
        self.repaint()

    def _on_theme_changed(self, theme_name: str) -> None:
        apply_theme(theme_name)
        self._sync_window_theme()
        zh = self.tr_mgr.is_zh
        mode_text = (
            "深色模式" if isDarkTheme() else "浅色模式"
        ) if zh else ("Dark theme" if isDarkTheme() else "Light theme")
        self._toast("主题已切换" if zh else "Theme Updated", mode_text, "success")

    def _on_language_changed(self, lang_code: str) -> None:
        self.tr_mgr.set_language(lang_code)
        self._retranslate_all()
        zh = self.tr_mgr.is_zh
        self._toast(
            "语言已切换" if zh else "Language Switched",
            "已切换为简体中文" if zh else "Switched to English",
            "success",
        )

    def _retranslate_all(self) -> None:
        t = self.tr_mgr.t
        # Update navigation sidebar item titles
        nav_labels = {
            self.home_page.objectName(): t("nav.home"),
            self.report_page.objectName(): t("nav.report"),
            self.macos_page.objectName(): t("nav.macos"),
            self.customize_page.objectName(): t("nav.customize"),
            self.build_page.objectName(): t("nav.build"),
            self.settings_page.objectName(): t("nav.settings"),
        }
        for route_key, label in nav_labels.items():
            nav_item = self.navigationInterface.widget(route_key)
            if nav_item is not None and hasattr(nav_item, "setText"):
                nav_item.setText(label)

        # Retranslate every page live
        self.home_page.retranslate_ui()
        self.report_page.retranslate_ui()
        self.macos_page.retranslate_ui()
        self.customize_page.retranslate_ui()
        self.build_page.retranslate_ui()
        self.settings_page.retranslate_ui()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _toast(self, title: str, content: str, kind: str = "info") -> None:
        fn = {
            "success": InfoBar.success,
            "warning": InfoBar.warning,
            "error": InfoBar.error,
        }.get(kind, InfoBar.info)
        fn(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3500,
            parent=self,
        )

    def _set_workflow_busy(self, busy: bool) -> None:
        self.report_page.set_busy(busy)
        self.macos_page.set_busy(busy)
        self.build_page.set_busy(busy)

    def _run_bg(self, fn: Any, *args: Any, on_ok: Any, on_err: Any = None, lock_ui: bool = True) -> None:
        if lock_ui:
            self._set_workflow_busy(True)
        worker = TaskWorker(fn, *args, parent=self)
        self._active_workers.append(worker)

        def _cleanup() -> None:
            if worker in self._active_workers:
                self._active_workers.remove(worker)
            if lock_ui:
                self._set_workflow_busy(False)
            worker.deleteLater()

        def _ok(res: Any) -> None:
            _cleanup()
            on_ok(res)

        def _fail(title: str, detail: str) -> None:
            _cleanup()
            if on_err:
                on_err(title, detail)
            else:
                dlg = DetailErrorDialog(title, detail, self)
                dlg.exec()

        worker.finished_ok.connect(_ok)
        worker.failed.connect(_fail)
        worker.start()

    def _handle_core_prompt(self, req: PromptRequest) -> None:
        dlg = CorePromptDialog(req, self)
        if dlg.exec():
            answer = dlg.get_answer()
        else:
            answer = req.default_value
        self.relay.submit_prompt_answer(answer)

    def _refresh_all_pages(self) -> None:
        snap = self.adapter.get_state_snapshot()
        self.report_page.update_state(snap, self.adapter.os_data.get_macos_name_by_darwin)
        self.macos_page.update_state(self.adapter.get_available_macos_versions(), snap)
        self.customize_page.update_state(self.adapter)
        self.build_page.update_state(snap, self.adapter.result_dir)

    def refresh_customize_page(self) -> None:
        self.customize_page.update_state(self.adapter)

    def _open_folder(self, path: str) -> None:
        if path and os.path.exists(path):
            self.adapter.u.open_folder(path)
        else:
            self._toast("目录不存在" if self.tr_mgr.is_zh else "Folder Not Found", path or "", "warning")

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    def _on_export_report(self) -> None:
        zh = self.tr_mgr.is_zh
        self._toast(
            "正在采集硬件" if zh else "Exporting Hardware Report",
            "正在调用 Hardware Sniffer 导出本机硬件与 ACPI 表..." if zh else "Running Hardware Sniffer...",
            "info",
        )
        self._run_bg(
            self.adapter.export_hardware_report_windows,
            on_ok=self._after_report_loaded,
        )

    def _on_import_report(self, path: str) -> None:
        zh = self.tr_mgr.is_zh
        self._toast(
            "正在解析报告" if zh else "Loading Report",
            "正在校验硬件报告并分析 macOS 兼容性..." if zh else "Validating report and checking compatibility...",
            "info",
        )
        self._run_bg(
            self.adapter.load_hardware_report,
            path,
            on_ok=self._after_report_loaded,
        )

    def _after_report_loaded(self, snapshot: Dict[str, Any]) -> None:
        self._refresh_all_pages()
        zh = self.tr_mgr.is_zh
        self._toast(
            "硬件报告已就绪" if zh else "Hardware Report Ready",
            (f"已自动匹配推荐版本：{snapshot.get('macos_name') or '未知'}" if zh else f"Recommended: {snapshot.get('macos_name') or 'Unknown'}"),
            "success",
        )

    def _on_load_acpi(self, folder: str) -> None:
        def _ok(loaded: bool) -> None:
            self._refresh_all_pages()
            zh = self.tr_mgr.is_zh
            if loaded:
                self._toast(
                    "ACPI 加载成功" if zh else "ACPI Loaded",
                    "已读取 DSDT 并重新匹配推荐 ACPI 补丁。" if zh else "DSDT loaded and ACPI patches updated.",
                    "success",
                )
            else:
                self._toast(
                    "ACPI 加载失败" if zh else "ACPI Load Failed",
                    "所选目录未发现有效 DSDT.aml 文件。" if zh else "No valid DSDT.aml found.",
                    "warning",
                )

        self._run_bg(self.adapter.load_acpi_tables, folder, on_ok=_ok)

    def _on_apply_macos_version(self, target_darwin: str) -> None:
        zh = self.tr_mgr.is_zh
        self._toast(
            "正在重新匹配" if zh else "Recalculating",
            "正在按新系统版本重新计算驱动和机型..." if zh else "Updating kexts and SMBIOS for selected version...",
            "info",
        )

        def _ok(snapshot: Dict[str, Any]) -> None:
            self._refresh_all_pages()
            self._toast(
                "版本已切换" if zh else "Version Applied",
                f"{snapshot.get('macos_name')}  |  SMBIOS: {snapshot.get('smbios_model')}",
                "success",
            )

        self._run_bg(self.adapter.apply_macos_version, target_darwin, on_ok=_ok)

    def _on_acpi_toggled(self, index: int, checked: bool) -> None:
        self.adapter.set_acpi_patch_checked(index, checked)
        self.customize_page.update_state(self.adapter)
        self.build_page.update_state(self.adapter.get_state_snapshot(), self.adapter.result_dir)

    def _on_kext_toggled(self, index: int, checked: bool) -> None:
        ok, msg = self.adapter.toggle_kext(index, checked, force_load=False)
        if not ok and msg == "NEED_FORCE_CONFIRM":
            kext_name = self.adapter.k.kexts[index].name
            zh = self.tr_mgr.is_zh
            box = MessageBox(
                "确认强制加载驱动" if zh else "Confirm Force Load",
                (
                    f"驱动 {kext_name} 官方标注不兼容当前 macOS 版本。\n强制加载可能会导致不稳定或崩溃，确定要开启吗？"
                    if zh
                    else f"{kext_name} is marked incompatible with this macOS version.\nForce loading may cause instability. Continue?"
                ),
                self,
            )
            box.yesButton.setText("仍然开启" if zh else "Force Enable")
            box.cancelButton.setText("取消" if zh else "Cancel")
            if box.exec():
                ok, msg = self.adapter.toggle_kext(index, True, force_load=True)
            else:
                self.customize_page.update_state(self.adapter)
                return

        if not ok:
            self._toast("无法切换驱动" if self.tr_mgr.is_zh else "Cannot Toggle Kext", msg, "warning")
        self.customize_page.update_state(self.adapter)
        self.build_page.update_state(self.adapter.get_state_snapshot(), self.adapter.result_dir)

    def _on_smbios_selected(self, model_name: str) -> None:
        self.adapter.set_smbios_model(model_name)
        self.customize_page.update_state(self.adapter)
        self.build_page.update_state(self.adapter.get_state_snapshot(), self.adapter.result_dir)
        self._toast(
            "SMBIOS 已更新" if self.tr_mgr.is_zh else "SMBIOS Updated",
            model_name,
            "success",
        )

    def _on_smbios_restore(self) -> None:
        model = self.adapter.restore_default_smbios()
        if model:
            self.customize_page.update_state(self.adapter)
            self.build_page.update_state(self.adapter.get_state_snapshot(), self.adapter.result_dir)
            self._toast(
                "已恢复推荐机型" if self.tr_mgr.is_zh else "Default SMBIOS Restored",
                model,
                "success",
            )

    def _on_audio_layout_selected(self, layout_id: int) -> None:
        self.adapter.set_audio_layout_id(layout_id)
        self.customize_page.update_state(self.adapter)
        snap = self.adapter.get_state_snapshot()
        self.macos_page.update_state(self.adapter.get_available_macos_versions(), snap)
        self.build_page.update_state(snap, self.adapter.result_dir)
        self._toast(
            "声卡 Layout ID 已更新" if self.tr_mgr.is_zh else "Audio Layout ID Updated",
            f"alcid={layout_id}",
            "success",
        )

    def _on_audio_layout_restore(self) -> None:
        info = self.adapter.get_audio_codec_info()
        if info:
            self._on_audio_layout_selected(info["default_id"])

    def _on_open_diff_viewer(self) -> None:
        dlg = ConfigDiffDialog(
            self.adapter.last_original_config,
            self.adapter.last_generated_config,
            self,
        )
        dlg.exec()

    def _on_start_build(self) -> None:
        zh = self.tr_mgr.is_zh
        if not self.adapter.has_loaded_dsdt():
            box = MessageBox(
                "未检测到 ACPI 表" if zh else "No ACPI Tables Loaded",
                (
                    "你还没有加载 DSDT/ACPI 表，继续生成会跳过需要 DSDT 的 ACPI 补丁。\n\n建议先回到「1. 硬件报告」加载 ACPI 目录，确认仍要继续吗？"
                    if zh
                    else "No DSDT/ACPI tables are loaded. DSDT-based ACPI patches will be skipped.\n\nContinue building anyway?"
                ),
                self,
            )
            box.yesButton.setText("继续生成" if zh else "Continue")
            box.cancelButton.setText("返回加载" if zh else "Go Back")
            if not box.exec():
                self.switchTo(self.report_page)
                return

        if self.adapter.needs_oclp:
            box = MessageBox(
                self.tr_mgr.t("build.oclp_warn_title"),
                self.tr_mgr.t("build.oclp_warn_body"),
                self,
            )
            box.yesButton.setText("了解风险，继续生成" if zh else "Continue")
            box.cancelButton.setText("取消" if zh else "Cancel")
            if not box.exec():
                return

        self.build_page.clear_logs()
        self.build_page.append_log(
            "开始执行 OpenCore EFI 构建流程..." if zh else "Starting OpenCore EFI build..."
        )

        def _ok(res: Dict[str, Any]) -> None:
            self.build_page.show_build_result(res)
            self._toast(
                "EFI 生成成功" if zh else "EFI Built Successfully",
                str(res.get("result_dir")),
                "success",
            )

        self._run_bg(self.adapter.build_efi, on_ok=_ok)

    def _on_settings_saved(self, new_settings: AppSettings) -> None:
        self.settings = new_settings
        self.adapter.update_settings(new_settings)
        self.build_page.update_state(self.adapter.get_state_snapshot(), self.adapter.result_dir)
        zh = self.tr_mgr.is_zh
        self._toast(
            "设置已保存" if zh else "Settings Saved",
            "下载加速与输出路径已更新。" if zh else "Network and output path updated.",
            "success",
        )

    def _on_check_core_update(self) -> None:
        self.settings_page.set_core_busy(True)

        def _ok(info: CoreVersionInfo) -> None:
            self.settings_page.set_core_busy(False)
            self.settings_page.update_core_info(info)
            zh = self.tr_mgr.is_zh
            if info.error:
                self._toast("检查失败" if zh else "Check Failed", info.error, "warning")
            elif info.has_update:
                self._toast(
                    "发现新版内核" if zh else "Core Update Available",
                    info.short_remote_sha,
                    "info",
                )
            else:
                self._toast(
                    "已是最新" if zh else "Up to Date",
                    info.short_local_sha,
                    "success",
                )

        def _err(title: str, detail: str) -> None:
            self.settings_page.set_core_busy(False)
            self._toast(title, detail, "error")

        self._run_bg(
            check_upstream_core_update,
            self.settings,
            on_ok=_ok,
            on_err=_err,
            lock_ui=False,
        )

    def _on_sync_core(self) -> None:
        self.settings_page.set_core_busy(True)

        def _ok(res: tuple[bool, str]) -> None:
            self.settings_page.set_core_busy(False)
            ok, msg = res
            local_info = get_local_core_info()
            self.home_page.update_core_info(local_info)
            self.settings_page.update_core_info(local_info)
            self._toast(
                "内核同步结果" if self.tr_mgr.is_zh else "Core Sync",
                msg,
                "success" if ok else "warning",
            )

        def _err(title: str, detail: str) -> None:
            self.settings_page.set_core_busy(False)
            self._toast(title, detail, "error")

        self._run_bg(sync_upstream_core, on_ok=_ok, on_err=_err, lock_ui=False)
