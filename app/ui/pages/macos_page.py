"""Step 2: Target macOS version selection page."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    FluentIcon,
    PrimaryPushButton,
    PushButton,
    RadioButton,
    ScrollArea,
    StrongBodyLabel,
    SubtitleLabel,
    TitleLabel,
)

from app.i18n import Translator


class MacOSPage(ScrollArea):
    """Step 2 page: select target macOS version and review hardware selection."""

    version_applied = Signal(str)
    next_requested = Signal()

    def __init__(self, translator: Translator, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.tr_mgr = translator
        self._last_versions: List[Dict[str, Any]] = []
        self._last_snapshot: Optional[Dict[str, Any]] = None
        self.setObjectName("macosPage")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.container = QWidget(self)
        self.setWidget(self.container)
        self.enableTransparentBackground()

        self.root_layout = QVBoxLayout(self.container)
        self.root_layout.setContentsMargins(28, 24, 28, 28)
        self.root_layout.setSpacing(16)

        self.title_label = TitleLabel("", self.container)
        self.desc_label = BodyLabel("", self.container)
        self.desc_label.setWordWrap(True)
        self.root_layout.addWidget(self.title_label)
        self.root_layout.addWidget(self.desc_label)

        self.empty_label = BodyLabel("", self.container)
        self.root_layout.addWidget(self.empty_label)

        # Versions list card
        self.versions_card = CardWidget(self.container)
        self.versions_layout = QVBoxLayout(self.versions_card)
        self.versions_layout.setContentsMargins(20, 16, 20, 16)
        self.versions_layout.setSpacing(10)
        self.versions_card.hide()
        self.root_layout.addWidget(self.versions_card)

        self._btn_group = QButtonGroup(self)

        # Action row
        action_row = QHBoxLayout()
        action_row.setSpacing(12)
        self.apply_btn = PrimaryPushButton(FluentIcon.ACCEPT, "", self.container)
        self.apply_btn.clicked.connect(self._on_apply)
        self.apply_btn.hide()

        self.reselect_hw_btn = PushButton(FluentIcon.SYNC, "", self.container)
        self.reselect_hw_btn.clicked.connect(self._on_apply)
        self.reselect_hw_btn.hide()

        self.next_btn = PrimaryPushButton(FluentIcon.RIGHT_ARROW, "", self.container)
        self.next_btn.clicked.connect(self.next_requested.emit)
        self.next_btn.hide()

        action_row.addWidget(self.apply_btn)
        action_row.addWidget(self.reselect_hw_btn)
        action_row.addStretch(1)
        action_row.addWidget(self.next_btn)
        self.root_layout.addLayout(action_row)

        # Active hardware summary card
        self.active_hw_card = CardWidget(self.container)
        act_layout = QVBoxLayout(self.active_hw_card)
        act_layout.setContentsMargins(20, 16, 20, 16)
        act_layout.setSpacing(6)
        self.active_hw_title = SubtitleLabel("", self.active_hw_card)
        self.active_hw_body = BodyLabel("", self.active_hw_card)
        self.active_hw_body.setWordWrap(True)
        act_layout.addWidget(self.active_hw_title)
        act_layout.addWidget(self.active_hw_body)
        self.active_hw_card.hide()
        self.root_layout.addWidget(self.active_hw_card)

        # Disabled devices summary card
        self.disabled_card = CardWidget(self.container)
        dis_layout = QVBoxLayout(self.disabled_card)
        dis_layout.setContentsMargins(20, 16, 20, 16)
        dis_layout.setSpacing(6)
        self.disabled_title = SubtitleLabel("", self.disabled_card)
        self.disabled_body = BodyLabel("", self.disabled_card)
        self.disabled_body.setWordWrap(True)
        dis_layout.addWidget(self.disabled_title)
        dis_layout.addWidget(self.disabled_body)
        self.disabled_card.hide()
        self.root_layout.addWidget(self.disabled_card)

        self.root_layout.addStretch(1)
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        t = self.tr_mgr.t
        self.title_label.setText(t("macos.title"))
        self.desc_label.setText(t("macos.desc"))
        self.empty_label.setText(t("macos.need_report_first"))
        self.apply_btn.setText(t("macos.apply_btn"))
        self.reselect_hw_btn.setText(t("macos.reselect_btn"))
        self.next_btn.setText(t("macos.next_btn"))
        self.active_hw_title.setText(t("macos.active_hw_title"))
        self.disabled_title.setText(t("macos.disabled_title"))
        if self._last_versions and self._last_snapshot:
            self.update_state(self._last_versions, self._last_snapshot)

    def set_busy(self, busy: bool) -> None:
        self.apply_btn.setEnabled(not busy)
        self.reselect_hw_btn.setEnabled(not busy)
        self.next_btn.setEnabled(not busy)

    def _clear_versions(self) -> None:
        for btn in list(self._btn_group.buttons()):
            self._btn_group.removeButton(btn)
        while self.versions_layout.count():
            item = self.versions_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def update_state(
        self, versions: List[Dict[str, Any]], snapshot: Dict[str, Any]
    ) -> None:
        self._last_versions = versions
        self._last_snapshot = snapshot
        if not versions:
            self.empty_label.show()
            self.versions_card.hide()
            self.apply_btn.hide()
            self.reselect_hw_btn.hide()
            self.next_btn.hide()
            self.active_hw_card.hide()
            self.disabled_card.hide()
            return

        t = self.tr_mgr.t
        zh = self.tr_mgr.is_zh
        self.empty_label.hide()
        self.versions_card.show()
        self.apply_btn.show()
        self.reselect_hw_btn.show()
        self.next_btn.show()
        self.active_hw_card.show()
        self.disabled_card.show()

        self._clear_versions()
        self.versions_layout.addWidget(StrongBodyLabel(t("macos.list_title"), self.versions_card))

        for item in versions:
            row = QWidget(self.versions_card)
            h = QHBoxLayout(row)
            h.setContentsMargins(0, 4, 0, 4)
            h.setSpacing(12)

            label_text = f"{item['name']}  (Darwin {item['darwin_major']})"
            rb = RadioButton(label_text, row)
            rb.setProperty("darwin_version", item["darwin_version"])
            if item["is_selected"]:
                rb.setChecked(True)
            self._btn_group.addButton(rb)
            h.addWidget(rb)
            h.addStretch(1)

            if item["is_suggested"]:
                rec = CaptionLabel(t("macos.recommended_tag"), row)
                rec.setStyleSheet("color: #0078d4; font-weight: 600;")
                h.addWidget(rec)

            if item["requires_oclp"]:
                tag = CaptionLabel(t("macos.oclp_tag"), row)
                tag.setStyleSheet("color: #ea580c; font-weight: 600;")
            else:
                tag = CaptionLabel(t("macos.native_tag"), row)
                tag.setStyleSheet("color: #16a34a; font-weight: 600;")
            h.addWidget(tag)

            self.versions_layout.addWidget(row)

        customized = snapshot.get("customized_hardware") or {}
        active_lines: List[str] = []
        gpus = list((customized.get("GPU") or {}).keys())
        nets = list((customized.get("Network") or {}).keys())
        sounds = list((customized.get("Sound") or {}).keys())
        if gpus:
            active_lines.append(("• 显卡：" if zh else "• GPU: ") + " + ".join(gpus))
        if nets:
            active_lines.append(("• 网卡：" if zh else "• Network: ") + ", ".join(nets))
        if sounds:
            active_lines.append(("• 声卡：" if zh else "• Audio: ") + ", ".join(sounds))
        if snapshot.get("audio_layout_id") is not None:
            active_lines.append(
                f"• 声卡 Layout ID (alcid)：{snapshot['audio_layout_id']}（可在「高级定制」修改）"
                if zh
                else f"• Audio Layout ID (alcid): {snapshot['audio_layout_id']} (editable in Customize)"
            )
        self.active_hw_body.setText(
            "\n".join(active_lines) if active_lines else ("暂无已启用设备信息。" if zh else "No active hardware summary.")
        )

        disabled = snapshot.get("disabled_devices") or {}
        if disabled:
            lines = [f"• {name}" for name in disabled.keys()]
            self.disabled_body.setText("\n".join(lines))
        else:
            self.disabled_body.setText(t("macos.no_disabled"))

    def _on_apply(self) -> None:
        checked = self._btn_group.checkedButton()
        if checked is not None:
            darwin_ver = str(checked.property("darwin_version"))
            self.version_applied.emit(darwin_ver)
