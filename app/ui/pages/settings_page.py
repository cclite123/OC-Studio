"""Settings & upstream core sync page with instant theme & language switching."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    ComboBox,
    FluentIcon,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    StrongBodyLabel,
    SubtitleLabel,
    TitleLabel,
)

from app import APP_VERSION, UPSTREAM_REPO
from app.config import AppSettings
from app.core_updater import CoreVersionInfo
from app.i18n import Translator


MIRROR_KEYS = ["direct", "ghfast", "ghproxy_net", "ghproxy_cc", "custom"]
THEME_KEYS = ["auto", "light", "dark"]
LANGUAGE_OPTIONS = [
    ("zh_CN", "简体中文"),
    ("en_US", "English"),
]


class SettingsPage(ScrollArea):
    """Settings page: mirror acceleration, proxy, instant theme/language, output dir, core sync."""

    settings_changed = Signal(object)
    theme_changed = Signal(str)
    language_changed = Signal(str)
    check_core_requested = Signal()
    sync_core_requested = Signal()

    def __init__(
        self,
        settings: AppSettings,
        translator: Translator,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.settings = settings
        self.tr_mgr = translator
        self._last_core_info: Optional[CoreVersionInfo] = None
        self._syncing_controls = False
        self.setObjectName("settingsPage")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.container = QWidget(self)
        self.setWidget(self.container)
        self.enableTransparentBackground()

        root = QVBoxLayout(self.container)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(14)

        self.title_label = TitleLabel("", self.container)
        self.desc_label = BodyLabel("", self.container)
        self.desc_label.setWordWrap(True)
        root.addWidget(self.title_label)
        root.addWidget(self.desc_label)

        # --- Group 1: Network & GitHub Mirror ---
        net_card = CardWidget(self.container)
        net_lay = QVBoxLayout(net_card)
        net_lay.setContentsMargins(20, 16, 20, 16)
        net_lay.setSpacing(12)
        self.net_group_title = SubtitleLabel("", net_card)
        net_lay.addWidget(self.net_group_title)

        # Mirror selector
        m_row = QHBoxLayout()
        m_text = QVBoxLayout()
        self.mirror_title = StrongBodyLabel("", net_card)
        self.mirror_desc = CaptionLabel("", net_card)
        m_text.addWidget(self.mirror_title)
        m_text.addWidget(self.mirror_desc)
        self.mirror_combo = ComboBox(net_card)
        self.mirror_combo.setMinimumWidth(230)
        m_row.addLayout(m_text, 1)
        m_row.addWidget(self.mirror_combo)
        net_lay.addLayout(m_row)

        # Custom mirror URL
        cm_row = QHBoxLayout()
        cm_text = QVBoxLayout()
        self.custom_mirror_title = StrongBodyLabel("", net_card)
        self.custom_mirror_desc = CaptionLabel("", net_card)
        cm_text.addWidget(self.custom_mirror_title)
        cm_text.addWidget(self.custom_mirror_desc)
        self.custom_mirror_edit = LineEdit(net_card)
        self.custom_mirror_edit.setPlaceholderText("https://ghfast.top/")
        self.custom_mirror_edit.setText(settings.custom_mirror_url)
        self.custom_mirror_edit.setFixedWidth(260)
        cm_row.addLayout(cm_text, 1)
        cm_row.addWidget(self.custom_mirror_edit)
        net_lay.addLayout(cm_row)

        # HTTP Proxy
        p_row = QHBoxLayout()
        p_text = QVBoxLayout()
        self.proxy_title = StrongBodyLabel("", net_card)
        self.proxy_desc = CaptionLabel("", net_card)
        p_text.addWidget(self.proxy_title)
        p_text.addWidget(self.proxy_desc)
        self.proxy_edit = LineEdit(net_card)
        self.proxy_edit.setPlaceholderText("http://127.0.0.1:7890")
        self.proxy_edit.setText(settings.http_proxy)
        self.proxy_edit.setFixedWidth(260)
        p_row.addLayout(p_text, 1)
        p_row.addWidget(self.proxy_edit)
        net_lay.addLayout(p_row)

        root.addWidget(net_card)

        # --- Group 2: Appearance & Output ---
        app_card = CardWidget(self.container)
        app_lay = QVBoxLayout(app_card)
        app_lay.setContentsMargins(20, 16, 20, 16)
        app_lay.setSpacing(12)
        self.app_group_title = SubtitleLabel("", app_card)
        app_lay.addWidget(self.app_group_title)

        # Theme (instant apply)
        t_row = QHBoxLayout()
        t_text = QVBoxLayout()
        self.theme_title = StrongBodyLabel("", app_card)
        self.theme_desc = CaptionLabel("", app_card)
        t_text.addWidget(self.theme_title)
        t_text.addWidget(self.theme_desc)
        self.theme_combo = ComboBox(app_card)
        self.theme_combo.setMinimumWidth(180)
        t_row.addLayout(t_text, 1)
        t_row.addWidget(self.theme_combo)
        app_lay.addLayout(t_row)

        # Language (instant apply)
        lang_row = QHBoxLayout()
        lang_text = QVBoxLayout()
        self.lang_title = StrongBodyLabel("", app_card)
        self.lang_desc = CaptionLabel("", app_card)
        lang_text.addWidget(self.lang_title)
        lang_text.addWidget(self.lang_desc)
        self.lang_combo = ComboBox(app_card)
        self.lang_combo.setMinimumWidth(180)
        for key, label in LANGUAGE_OPTIONS:
            self.lang_combo.addItem(label, userData=key)
        l_idx = next((i for i, (k, _) in enumerate(LANGUAGE_OPTIONS) if k == settings.language), 0)
        self.lang_combo.setCurrentIndex(l_idx)
        lang_row.addLayout(lang_text, 1)
        lang_row.addWidget(self.lang_combo)
        app_lay.addLayout(lang_row)

        # Output dir
        o_row = QHBoxLayout()
        o_text = QVBoxLayout()
        self.output_title = StrongBodyLabel("", app_card)
        self.output_desc = CaptionLabel("", app_card)
        o_text.addWidget(self.output_title)
        o_text.addWidget(self.output_desc)
        self.output_edit = LineEdit(app_card)
        self.output_edit.setPlaceholderText(str(settings.get_effective_output_dir()))
        self.output_edit.setText(settings.output_dir)
        self.output_edit.setFixedWidth(260)
        self.browse_out_btn = PushButton(FluentIcon.FOLDER, "", app_card)
        self.browse_out_btn.clicked.connect(self._browse_output_dir)
        o_row.addLayout(o_text, 1)
        o_row.addWidget(self.output_edit)
        o_row.addWidget(self.browse_out_btn)
        app_lay.addLayout(o_row)

        save_row = QHBoxLayout()
        self.reset_btn = PushButton(FluentIcon.SYNC, "", app_card)
        self.reset_btn.clicked.connect(self._reset_defaults)
        save_row.addWidget(self.reset_btn)
        save_row.addStretch(1)
        self.save_btn = PrimaryPushButton(FluentIcon.SAVE, "", app_card)
        self.save_btn.clicked.connect(self._save_settings)
        save_row.addWidget(self.save_btn)
        app_lay.addLayout(save_row)

        root.addWidget(app_card)

        # --- Group 3: Upstream Core Management ---
        core_card = CardWidget(self.container)
        core_lay = QVBoxLayout(core_card)
        core_lay.setContentsMargins(20, 16, 20, 16)
        core_lay.setSpacing(10)
        self.core_group_title = SubtitleLabel("", core_card)
        core_lay.addWidget(self.core_group_title)

        self.core_info_label = BodyLabel("", core_card)
        self.core_info_label.setWordWrap(True)
        core_lay.addWidget(self.core_info_label)

        core_btn_row = QHBoxLayout()
        core_btn_row.setSpacing(12)
        self.check_core_btn = PushButton(FluentIcon.SYNC, "", core_card)
        self.check_core_btn.clicked.connect(self.check_core_requested.emit)
        self.sync_core_btn = PrimaryPushButton(FluentIcon.UPDATE, "", core_card)
        self.sync_core_btn.clicked.connect(self.sync_core_requested.emit)
        core_btn_row.addWidget(self.check_core_btn)
        core_btn_row.addWidget(self.sync_core_btn)
        core_btn_row.addStretch(1)
        core_lay.addLayout(core_btn_row)
        root.addWidget(core_card)

        # --- Group 4: About ---
        about_card = CardWidget(self.container)
        about_lay = QVBoxLayout(about_card)
        about_lay.setContentsMargins(20, 16, 20, 16)
        about_lay.setSpacing(6)
        self.about_group_title = SubtitleLabel("", about_card)
        self.about_body = BodyLabel("", about_card)
        self.about_body.setWordWrap(True)
        about_lay.addWidget(self.about_group_title)
        about_lay.addWidget(self.about_body)
        root.addWidget(about_card)

        root.addStretch(1)

        for desc_lbl in (
            self.mirror_desc,
            self.custom_mirror_desc,
            self.proxy_desc,
            self.theme_desc,
            self.lang_desc,
            self.output_desc,
        ):
            desc_lbl.setWordWrap(True)

        # Populate translated texts first, then connect instant-apply signals
        self.retranslate_ui()
        self.theme_combo.currentIndexChanged.connect(self._on_theme_combo_changed)
        self.lang_combo.currentIndexChanged.connect(self._on_lang_combo_changed)

    def retranslate_ui(self) -> None:
        t = self.tr_mgr.t
        self._syncing_controls = True
        try:
            self.title_label.setText(t("settings.title"))
            self.desc_label.setText(t("settings.desc"))
            self.net_group_title.setText(t("settings.network_group"))
            self.mirror_title.setText(t("settings.mirror_title"))
            self.mirror_desc.setText(t("settings.mirror_desc"))
            self.custom_mirror_title.setText(t("settings.custom_mirror_title"))
            self.custom_mirror_desc.setText(t("settings.custom_mirror_desc"))
            self.proxy_title.setText(t("settings.proxy_title"))
            self.proxy_desc.setText(t("settings.proxy_desc"))
            self.app_group_title.setText(t("settings.appearance_group"))
            self.theme_title.setText(t("settings.theme_title"))
            self.theme_desc.setText(t("settings.theme_desc"))
            self.lang_title.setText(t("settings.lang_title"))
            self.lang_desc.setText(t("settings.lang_desc"))
            self.output_title.setText(t("settings.output_title"))
            self.output_desc.setText(t("settings.output_desc"))
            self.browse_out_btn.setText(t("settings.browse_btn"))
            self.reset_btn.setText(t("settings.reset_btn"))
            self.save_btn.setText(t("settings.save_btn"))
            self.core_group_title.setText(t("settings.core_group"))
            self.check_core_btn.setText(t("settings.core_check_btn"))
            self.sync_core_btn.setText(t("settings.core_sync_btn"))
            self.about_group_title.setText(t("settings.about_group"))
            self.about_body.setText(
                t("settings.about_body", ver=APP_VERSION, repo=UPSTREAM_REPO)
            )

            # Rebuild Mirror & Theme ComboBox labels while preserving selection
            self.mirror_combo.clear()
            for key in MIRROR_KEYS:
                self.mirror_combo.addItem(t(f"settings.mirror_{key}"), userData=key)
            m_idx = MIRROR_KEYS.index(self.settings.mirror_mode) if self.settings.mirror_mode in MIRROR_KEYS else 0
            self.mirror_combo.setCurrentIndex(m_idx)

            self.theme_combo.clear()
            for key in THEME_KEYS:
                self.theme_combo.addItem(t(f"settings.theme_{key}"), userData=key)
            t_idx = THEME_KEYS.index(self.settings.theme) if self.settings.theme in THEME_KEYS else 0
            self.theme_combo.setCurrentIndex(t_idx)

            l_idx = next((i for i, (k, _) in enumerate(LANGUAGE_OPTIONS) if k == self.settings.language), 0)
            self.lang_combo.setCurrentIndex(l_idx)
        finally:
            self._syncing_controls = False

        if self._last_core_info is not None:
            self.update_core_info(self._last_core_info)

    def _on_theme_combo_changed(self, _index: int) -> None:
        if self._syncing_controls:
            return
        theme = self.theme_combo.currentData() or "auto"
        self.settings.theme = theme
        self.settings.save()
        self.theme_changed.emit(theme)

    def _on_lang_combo_changed(self, _index: int) -> None:
        if self._syncing_controls:
            return
        lang = self.lang_combo.currentData() or "zh_CN"
        self.settings.language = lang
        self.settings.save()
        self.language_changed.emit(lang)

    def _browse_output_dir(self) -> None:
        title = "选择 EFI 输出目录" if self.tr_mgr.is_zh else "Select EFI Output Folder"
        folder = QFileDialog.getExistingDirectory(self, title)
        if folder:
            self.output_edit.setText(folder)

    def _save_settings(self) -> None:
        self.settings.mirror_mode = self.mirror_combo.currentData() or "direct"
        self.settings.custom_mirror_url = self.custom_mirror_edit.text().strip()
        self.settings.http_proxy = self.proxy_edit.text().strip()
        self.settings.theme = self.theme_combo.currentData() or "auto"
        self.settings.language = self.lang_combo.currentData() or "zh_CN"
        self.settings.output_dir = self.output_edit.text().strip()
        self.settings.save()
        self.settings_changed.emit(self.settings)

    def _reset_defaults(self) -> None:
        defaults = AppSettings()
        self.settings.mirror_mode = defaults.mirror_mode
        self.settings.custom_mirror_url = defaults.custom_mirror_url
        self.settings.http_proxy = defaults.http_proxy
        self.settings.theme = defaults.theme
        self.settings.language = defaults.language
        self.settings.output_dir = defaults.output_dir
        self.settings.save()

        self._syncing_controls = True
        try:
            self.mirror_combo.setCurrentIndex(0)
            self.custom_mirror_edit.clear()
            self.proxy_edit.clear()
            self.theme_combo.setCurrentIndex(0)
            self.lang_combo.setCurrentIndex(0)
            self.output_edit.clear()
        finally:
            self._syncing_controls = False

        self.theme_changed.emit(self.settings.theme)
        self.language_changed.emit(self.settings.language)
        self.settings_changed.emit(self.settings)

    def set_core_busy(self, busy: bool) -> None:
        self.check_core_btn.setEnabled(not busy)
        self.sync_core_btn.setEnabled(not busy)

    def update_core_info(self, info: CoreVersionInfo) -> None:
        self._last_core_info = info
        zh = self.tr_mgr.is_zh
        if zh:
            lines = [
                f"• 本地内核提交：{info.short_local_sha}  （日期：{info.local_date or '未知'}）",
                f"• 最新提交说明：{info.local_subject or '无'}",
            ]
            if info.remote_sha:
                status = "🎉 已是最新！" if info.has_update is False else "🔔 发现上游新版本，可点击「同步最新内核」"
                lines.append(f"• 上游最新提交：{info.short_remote_sha}  （日期：{info.remote_date or '未知'}）")
                lines.append(f"• 状态：{status}")
            elif info.error:
                lines.append(f"• 提示：{info.error}")
        else:
            lines = [
                f"• Local Core Commit: {info.short_local_sha}  (Date: {info.local_date or 'Unknown'})",
                f"• Latest Commit Message: {info.local_subject or 'N/A'}",
            ]
            if info.remote_sha:
                status = "🎉 Up to date!" if info.has_update is False else "🔔 Update available — click 'Sync Latest Core'"
                lines.append(f"• Upstream Commit: {info.short_remote_sha}  (Date: {info.remote_date or 'Unknown'})")
                lines.append(f"• Status: {status}")
            elif info.error:
                lines.append(f"• Note: {info.error}")

        self.core_info_label.setText("\n".join(lines))
        self.sync_core_btn.setEnabled(info.is_git_repo)
