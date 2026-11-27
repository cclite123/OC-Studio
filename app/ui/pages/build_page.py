"""Step 4: Build OpenCore EFI page with live progress, download status, and logs."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    FluentIcon,
    PlainTextEdit,
    PrimaryPushButton,
    ProgressBar,
    PushButton,
    ScrollArea,
    StrongBodyLabel,
    SubtitleLabel,
    TitleLabel,
)

from app.i18n import Translator


class BuildPage(ScrollArea):
    """Step 4 page: confirm summary, run build, watch progress and logs."""

    build_requested = Signal()
    open_result_requested = Signal(str)
    open_diff_requested = Signal()

    def __init__(self, translator: Translator, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.tr_mgr = translator
        self._last_snapshot: Optional[Dict[str, Any]] = None
        self._last_output_dir: str = ""
        self._last_result_dir: str = ""
        self._last_result: Optional[Dict[str, Any]] = None
        self._ready_flag: bool = False
        self.setObjectName("buildPage")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.container = QWidget(self)
        self.setWidget(self.container)
        self.enableTransparentBackground()

        self.root_layout = QVBoxLayout(self.container)
        self.root_layout.setContentsMargins(28, 24, 28, 28)
        self.root_layout.setSpacing(14)

        self.title_label = TitleLabel("", self.container)
        self.desc_label = BodyLabel("", self.container)
        self.desc_label.setWordWrap(True)
        self.root_layout.addWidget(self.title_label)
        self.root_layout.addWidget(self.desc_label)

        # Summary card
        self.summary_card = CardWidget(self.container)
        sum_layout = QVBoxLayout(self.summary_card)
        sum_layout.setContentsMargins(20, 16, 20, 16)
        sum_layout.setSpacing(6)
        self.summary_title = StrongBodyLabel("", self.summary_card)
        self.summary_label = BodyLabel("", self.summary_card)
        self.summary_label.setWordWrap(True)
        sum_layout.addWidget(self.summary_title)
        sum_layout.addWidget(self.summary_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        self.start_btn = PrimaryPushButton(FluentIcon.PLAY, "", self.summary_card)
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.build_requested.emit)

        self.open_btn = PushButton(FluentIcon.FOLDER, "", self.summary_card)
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self._on_open_result)

        self.diff_btn = PushButton(FluentIcon.DOCUMENT, "", self.summary_card)
        self.diff_btn.clicked.connect(self.open_diff_requested.emit)

        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.open_btn)
        btn_row.addWidget(self.diff_btn)
        btn_row.addStretch(1)
        sum_layout.addLayout(btn_row)
        self.root_layout.addWidget(self.summary_card)

        # Progress card
        self.progress_card = CardWidget(self.container)
        prog_layout = QVBoxLayout(self.progress_card)
        prog_layout.setContentsMargins(20, 16, 20, 16)
        prog_layout.setSpacing(8)
        self.progress_title = StrongBodyLabel("", self.progress_card)
        self.step_label = BodyLabel("", self.progress_card)
        self.step_label.setWordWrap(True)
        self.step_bar = ProgressBar(self.progress_card)
        self.step_bar.setRange(0, 100)
        self.step_bar.setValue(0)

        self.download_label = CaptionLabel("", self.progress_card)
        self.download_label.setWordWrap(True)
        self.download_bar = ProgressBar(self.progress_card)
        self.download_bar.setRange(0, 100)
        self.download_bar.setValue(0)

        prog_layout.addWidget(self.progress_title)
        prog_layout.addWidget(self.step_label)
        prog_layout.addWidget(self.step_bar)
        prog_layout.addWidget(self.download_label)
        prog_layout.addWidget(self.download_bar)
        self.root_layout.addWidget(self.progress_card)

        # Post-build checklist card
        self.checklist_card = CardWidget(self.container)
        chk_layout = QVBoxLayout(self.checklist_card)
        chk_layout.setContentsMargins(20, 16, 20, 16)
        chk_layout.setSpacing(6)
        self.checklist_title = SubtitleLabel("", self.checklist_card)
        self.checklist_body = BodyLabel("", self.checklist_card)
        self.checklist_body.setWordWrap(True)
        chk_layout.addWidget(self.checklist_title)
        chk_layout.addWidget(self.checklist_body)
        self.checklist_card.hide()
        self.root_layout.addWidget(self.checklist_card)

        # Live log card
        log_card = CardWidget(self.container)
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(20, 14, 20, 14)
        log_layout.setSpacing(8)

        log_header = QHBoxLayout()
        self.log_title = StrongBodyLabel("", log_card)
        self.clear_log_btn = PushButton(FluentIcon.DELETE, "", log_card)
        self.clear_log_btn.clicked.connect(self.clear_logs)
        log_header.addWidget(self.log_title)
        log_header.addStretch(1)
        log_header.addWidget(self.clear_log_btn)
        log_layout.addLayout(log_header)

        self.log_view = PlainTextEdit(log_card)
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(240)
        log_layout.addWidget(self.log_view)
        self.root_layout.addWidget(log_card)

        self.root_layout.addStretch(1)
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        t = self.tr_mgr.t
        self.title_label.setText(t("build.title"))
        self.desc_label.setText(t("build.desc"))
        self.summary_title.setText(t("build.summary_title"))
        self.start_btn.setText(t("build.start_btn"))
        self.open_btn.setText(t("build.open_result_btn"))
        self.diff_btn.setText(t("build.diff_btn"))
        self.progress_title.setText(t("build.progress_title"))
        self.checklist_title.setText(t("build.bios_title"))
        self.log_title.setText(t("build.log_title"))
        self.clear_log_btn.setText(t("build.clear_log_btn"))

        if self.step_bar.value() == 0:
            self.step_label.setText(t("build.waiting"))
        if self.download_bar.value() == 0:
            self.download_label.setText(t("build.no_download"))

        if self._last_snapshot:
            self.update_state(self._last_snapshot, self._last_output_dir)
        else:
            self.summary_label.setText(t("build.no_report"))

        if self._last_result:
            self.show_build_result(self._last_result)

    def _on_open_result(self) -> None:
        if self._last_result_dir:
            self.open_result_requested.emit(self._last_result_dir)

    def clear_logs(self) -> None:
        self.log_view.clear()

    def append_log(self, line: str) -> None:
        self.log_view.appendPlainText(line)
        bar = self.log_view.verticalScrollBar()
        bar.setValue(bar.maximum())

    def set_busy(self, busy: bool) -> None:
        self.start_btn.setEnabled((not busy) and self._ready_flag)
        if busy:
            self.step_label.setText(
                "正在拉取组件并构建 EFI，请耐心等待..." if self.tr_mgr.is_zh else "Downloading assets and building EFI..."
            )
            self.step_bar.setValue(5)

    def update_state(self, snapshot: Dict[str, Any], output_dir: str) -> None:
        self._last_snapshot = snapshot
        self._last_output_dir = output_dir
        report = snapshot.get("hardware_report")
        macos_name = snapshot.get("macos_name")
        smbios = snapshot.get("smbios_model")
        if not report or not macos_name:
            self._ready_flag = False
            self.start_btn.setEnabled(False)
            self.summary_label.setText(self.tr_mgr.t("build.no_report"))
            return

        self._ready_flag = True
        self.start_btn.setEnabled(True)
        zh = self.tr_mgr.is_zh

        mb = report.get("Motherboard", {}).get("Name", "Unknown")
        cpu = report.get("CPU", {}).get("Processor Name", "Unknown")
        audio_id = snapshot.get("audio_layout_id")

        if zh:
            acpi_state = "已加载" if snapshot.get("acpi_loaded") else "未加载（部分 ACPI 补丁将被跳过）"
            oclp_text = "是（需进系统后打 OCLP 补丁）" if snapshot.get("needs_oclp") else "否（纯原生配置）"
            audio_line = f"Layout ID {audio_id}" if audio_id is not None else "自动 / 不适用"
            lines = [
                f"• 主板 / CPU：{mb}  |  {cpu}",
                f"• 目标 macOS：{macos_name}（Darwin {snapshot.get('macos_version')}）",
                f"• 机型 SMBIOS：{smbios}  |  声卡注入：{audio_line}",
                f"• ACPI 表状态：{acpi_state}（已启用 {snapshot.get('checked_acpi_count', 0)} 个补丁）",
                f"• Kext 驱动数量：已启用 {snapshot.get('checked_kext_count', 0)} 个",
                f"• 是否需要 OCLP：{oclp_text}",
                f"• 输出目录：{output_dir}",
            ]
        else:
            acpi_state = "Loaded" if snapshot.get("acpi_loaded") else "Not loaded (DSDT patches skipped)"
            oclp_text = "Yes (OCLP root patches required)" if snapshot.get("needs_oclp") else "No (Native)"
            audio_line = f"Layout ID {audio_id}" if audio_id is not None else "Auto / N/A"
            lines = [
                f"• Motherboard / CPU: {mb}  |  {cpu}",
                f"• Target macOS: {macos_name} (Darwin {snapshot.get('macos_version')})",
                f"• SMBIOS: {smbios}  |  Audio: {audio_line}",
                f"• ACPI Tables: {acpi_state} ({snapshot.get('checked_acpi_count', 0)} patches enabled)",
                f"• Kexts Enabled: {snapshot.get('checked_kext_count', 0)}",
                f"• OCLP Required: {oclp_text}",
                f"• Output Folder: {output_dir}",
            ]
        self.summary_label.setText("\n".join(lines))

    def on_build_progress(
        self, title: str, steps: List[str], current_index: int, done: bool
    ) -> None:
        total = max(len(steps), 1)
        zh = self.tr_mgr.is_zh
        if done:
            self.step_bar.setValue(100)
            self.step_label.setText("✓ OpenCore EFI 构建完成！" if zh else "✓ OpenCore EFI build complete!")
        else:
            pct = int((current_index / total) * 100)
            self.step_bar.setValue(max(pct, 10))
            if 0 <= current_index < len(steps):
                step_txt = self.tr_mgr.build_step(steps[current_index])
                self.step_label.setText(
                    f"步骤 {current_index + 1}/{total}：{step_txt}..."
                    if zh
                    else f"Step {current_index + 1}/{total}: {step_txt}..."
                )

    def on_download_progress(
        self, percent: int, speed: str, downloaded_mb: float, total_mb: float
    ) -> None:
        zh = self.tr_mgr.is_zh
        if percent >= 0:
            self.download_bar.setValue(min(percent, 100))
            if total_mb > 0:
                self.download_label.setText(
                    f"下载进度：{percent}%  ({downloaded_mb:.1f} / {total_mb:.1f} MB)  速度：{speed}"
                    if zh
                    else f"Downloading: {percent}%  ({downloaded_mb:.1f} / {total_mb:.1f} MB)  Speed: {speed}"
                )
            else:
                self.download_label.setText(
                    f"已下载：{downloaded_mb:.1f} MB  速度：{speed}"
                    if zh
                    else f"Downloaded: {downloaded_mb:.1f} MB  Speed: {speed}"
                )
        else:
            self.download_label.setText(
                f"正在下载：{downloaded_mb:.1f} MB  速度：{speed}"
                if zh
                else f"Downloading: {downloaded_mb:.1f} MB  Speed: {speed}"
            )

    def show_build_result(self, result: Dict[str, Any]) -> None:
        self._last_result = result
        self._last_result_dir = result.get("result_dir", "")
        self.open_btn.setEnabled(bool(self._last_result_dir))
        zh = self.tr_mgr.is_zh
        self.step_bar.setValue(100)
        self.step_label.setText(
            f"✓ 构建完成，已保存到：{self._last_result_dir}"
            if zh
            else f"✓ Build complete: {self._last_result_dir}"
        )

        bios_reqs = result.get("bios_requirements") or []
        lines: List[str] = []
        if bios_reqs:
            lines.append("1. BIOS / UEFI 必改设置：" if zh else "1. Required BIOS / UEFI Settings:")
            for req in bios_reqs:
                lines.append(f"   • {self.tr_mgr.bios_req(req)}")
            lines.append("")

        if zh:
            lines.extend(
                [
                    "2. USB 端口定制提醒：",
                    "   • 建议使用 USBToolBox 定制本机 USB 端口并生成 UTBMap.kext。",
                    "   • 将 UTBMap.kext 放入 EFI/OC/Kexts，删除默认的 UTBDefault.kext，并用 OCAT 或 ProperTree 做一次 Snapshot 保存。",
                ]
            )
        else:
            lines.extend(
                [
                    "2. USB Port Mapping:",
                    "   • Map USB ports using USBToolBox to generate UTBMap.kext.",
                    "   • Place UTBMap.kext into EFI/OC/Kexts, remove UTBDefault.kext, and run OC Snapshot in ProperTree/OCAT.",
                ]
            )

        notices = result.get("notices") or []
        if notices:
            lines.append("")
            lines.append("3. 硬件与驱动特别提醒：" if zh else "3. Hardware & Driver Notices:")
            for n in notices:
                lines.append(f"   • {n}")

        self.checklist_body.setText("\n".join(lines))
        self.checklist_card.show()
