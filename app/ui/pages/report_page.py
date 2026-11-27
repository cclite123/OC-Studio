"""Step 1: Hardware report import/export and compatibility overview page."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    FluentIcon,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    StrongBodyLabel,
    SubtitleLabel,
    TitleLabel,
)

from app.i18n import Translator


class DropReportCard(CardWidget):
    """Card supporting drag-and-drop for Report.json or SysReport folder."""

    path_dropped = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if urls:
            local = urls[0].toLocalFile()
            if local:
                self.path_dropped.emit(local)


class ReportPage(ScrollArea):
    """Step 1 page: collect/import hardware report & visualize compatibility."""

    export_requested = Signal()
    import_requested = Signal(str)
    acpi_requested = Signal(str)
    next_requested = Signal()

    def __init__(self, translator: Translator, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.tr_mgr = translator
        self._last_snapshot: Optional[Dict[str, Any]] = None
        self._last_os_name_fn: Any = None
        self.setObjectName("reportPage")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.container = QWidget(self)
        self.setWidget(self.container)
        self.enableTransparentBackground()

        self.root_layout = QVBoxLayout(self.container)
        self.root_layout.setContentsMargins(28, 24, 28, 28)
        self.root_layout.setSpacing(16)

        # Header
        self.title_label = TitleLabel("", self.container)
        self.desc_label = BodyLabel("", self.container)
        self.desc_label.setWordWrap(True)
        self.root_layout.addWidget(self.title_label)
        self.root_layout.addWidget(self.desc_label)

        # Action & Drop Card
        self.action_card = DropReportCard(self.container)
        self.action_card.path_dropped.connect(self.import_requested.emit)
        action_layout = QVBoxLayout(self.action_card)
        action_layout.setContentsMargins(20, 18, 20, 18)
        action_layout.setSpacing(12)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.export_btn = PrimaryPushButton(FluentIcon.SEARCH, "", self.action_card)
        self.export_btn.clicked.connect(self.export_requested.emit)
        if os.name != "nt":
            self.export_btn.setEnabled(False)

        self.import_btn = PushButton(FluentIcon.DOCUMENT, "", self.action_card)
        self.import_btn.clicked.connect(self._browse_report)

        self.acpi_btn = PushButton(FluentIcon.FOLDER, "", self.action_card)
        self.acpi_btn.clicked.connect(self._browse_acpi)
        self.acpi_btn.setEnabled(False)

        btn_row.addWidget(self.export_btn)
        btn_row.addWidget(self.import_btn)
        btn_row.addWidget(self.acpi_btn)
        btn_row.addStretch(1)
        action_layout.addLayout(btn_row)

        self.hint_label = CaptionLabel("", self.action_card)
        self.hint_label.setWordWrap(True)
        action_layout.addWidget(self.hint_label)

        self.report_path_label = CaptionLabel("", self.action_card)
        self.report_path_label.setWordWrap(True)
        self.acpi_status_label = CaptionLabel("", self.action_card)
        self.acpi_status_label.setWordWrap(True)
        action_layout.addWidget(self.report_path_label)
        action_layout.addWidget(self.acpi_status_label)

        self.root_layout.addWidget(self.action_card)

        # Compatibility Summary Section
        summary_header = QHBoxLayout()
        self.summary_title = SubtitleLabel("", self.container)
        self.next_btn = PrimaryPushButton(FluentIcon.RIGHT_ARROW, "", self.container)
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self.next_requested.emit)
        summary_header.addWidget(self.summary_title)
        summary_header.addStretch(1)
        summary_header.addWidget(self.next_btn)
        self.root_layout.addLayout(summary_header)

        # Notices banner
        self.notice_card = CardWidget(self.container)
        notice_layout = QVBoxLayout(self.notice_card)
        notice_layout.setContentsMargins(16, 12, 16, 12)
        self.notice_title = StrongBodyLabel("", self.notice_card)
        self.notice_body = BodyLabel("", self.notice_card)
        self.notice_body.setWordWrap(True)
        notice_layout.addWidget(self.notice_title)
        notice_layout.addWidget(self.notice_body)
        self.notice_card.hide()
        self.root_layout.addWidget(self.notice_card)

        # Dynamic hardware cards container
        self.cards_host = QWidget(self.container)
        self.cards_layout = QVBoxLayout(self.cards_host)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)

        self.empty_label = BodyLabel("", self.cards_host)
        self.cards_layout.addWidget(self.empty_label)

        self.root_layout.addWidget(self.cards_host)
        self.root_layout.addStretch(1)
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        t = self.tr_mgr.t
        self.title_label.setText(t("report.title"))
        self.desc_label.setText(t("report.desc"))
        self.export_btn.setText(t("report.export_btn"))
        self.import_btn.setText(t("report.import_btn"))
        self.acpi_btn.setText(t("report.acpi_btn"))
        self.hint_label.setText(t("report.drop_hint") if os.name == "nt" else t("report.win_only_hint"))
        self.summary_title.setText(t("report.summary_title"))
        self.next_btn.setText(t("report.next_btn"))
        self.notice_title.setText(t("report.notice_title"))
        if self._last_snapshot and self._last_os_name_fn:
            self.update_state(self._last_snapshot, self._last_os_name_fn)
        else:
            self.report_path_label.setText(t("report.no_file"))
            if self.empty_label is not None:
                try:
                    self.empty_label.setText(t("report.no_data"))
                except RuntimeError:
                    pass

    def _browse_report(self) -> None:
        title = "选择 Hardware Sniffer 导出的 Report.json" if self.tr_mgr.is_zh else "Select Report.json"
        file_path, _ = QFileDialog.getOpenFileName(
            self, title, "", "JSON (*.json);;All Files (*.*)"
        )
        if file_path:
            self.import_requested.emit(file_path)

    def _browse_acpi(self) -> None:
        title = "选择 ACPI 表所在目录（含 DSDT.aml）" if self.tr_mgr.is_zh else "Select ACPI Folder"
        folder = QFileDialog.getExistingDirectory(self, title)
        if folder:
            self.acpi_requested.emit(folder)

    def set_busy(self, busy: bool) -> None:
        self.export_btn.setEnabled((not busy) and os.name == "nt")
        self.import_btn.setEnabled(not busy)
        self.acpi_btn.setEnabled((not busy) and self.next_btn.isEnabled())

    def _clear_cards(self) -> None:
        self.empty_label = None
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _format_compat_badge(
        self, compat: Any, oclp_compat: Any, os_name_fn: Any
    ) -> tuple[str, str]:
        zh = self.tr_mgr.is_zh
        if oclp_compat and isinstance(oclp_compat, (tuple, list)) and oclp_compat[0]:
            max_o = os_name_fn(oclp_compat[0]) or oclp_compat[0]
            if compat and compat[0]:
                max_n = os_name_fn(compat[0]) or compat[0]
                return (
                    f"原生最高 {max_n}（OCLP 可至 {max_o}）" if zh else f"Native up to {max_n} (OCLP: {max_o})",
                    "warn",
                )
            return (f"需 OCLP 补丁（最高 {max_o}）" if zh else f"OCLP Required (up to {max_o})", "warn")
        if not compat:
            return ("未检测" if zh else "Unchecked", "muted")
        if not compat[0]:
            return ("不支持" if zh else "Unsupported", "err")
        min_name = os_name_fn(compat[-1]) or compat[-1]
        max_name = os_name_fn(compat[0]) or compat[0]
        if min_name == max_name:
            return (f"支持 {max_name}" if zh else f"Supports {max_name}", "ok")
        return (f"支持 {min_name} ～ {max_name}" if zh else f"{min_name} to {max_name}", "ok")

    def update_state(self, snapshot: Dict[str, Any], os_name_fn: Any) -> None:
        self._last_snapshot = snapshot
        self._last_os_name_fn = os_name_fn
        report = snapshot.get("hardware_report")
        report_path = snapshot.get("report_path")
        acpi_loaded = snapshot.get("acpi_loaded", False)
        acpi_dir = snapshot.get("acpi_dir")

        if not report:
            return

        t = self.tr_mgr.t
        zh = self.tr_mgr.is_zh
        short_report = self._shorten_path(str(report_path or ""))
        self.report_path_label.setText(f"{t('report.file_prefix')}{short_report}")
        self.report_path_label.setToolTip(str(report_path or ""))
        if acpi_loaded:
            short_acpi = self._shorten_path(str(acpi_dir or "Loaded"))
            self.acpi_status_label.setText(t("report.acpi_loaded", path=short_acpi))
            self.acpi_status_label.setToolTip(str(acpi_dir or ""))
            self.acpi_status_label.setStyleSheet("color: #16a34a; font-weight: 600;")
        else:
            self.acpi_status_label.setText(t("report.acpi_missing"))
            self.acpi_status_label.setToolTip("")
            self.acpi_status_label.setStyleSheet("color: #dc2626; font-weight: 600;")

        self.acpi_btn.setEnabled(True)
        self.next_btn.setEnabled(True)

        notices = snapshot.get("notices") or []
        if notices:
            self.notice_body.setText("\n\n".join(notices))
            self.notice_card.show()
        else:
            self.notice_card.hide()

        self._clear_cards()

        mb = report.get("Motherboard", {})
        bios = report.get("BIOS", {})
        cpu = report.get("CPU", {})

        overview_card = CardWidget(self.cards_host)
        ov_layout = QVBoxLayout(overview_card)
        ov_layout.setContentsMargins(18, 14, 18, 14)
        ov_layout.setSpacing(6)
        ov_layout.addWidget(StrongBodyLabel(t("report.platform_title"), overview_card))
        if zh:
            mb_line = f"主板：{mb.get('Name', '未知')}  |  芯片组：{mb.get('Chipset', '未知')}  |  形态：{mb.get('Platform', '未知')}"
            bios_line = f"BIOS 固件：{bios.get('Firmware Type', '未知')}  |  安全启动 (Secure Boot)：{bios.get('Secure Boot', '未知')}"
            cpu_sub = f"代号：{cpu.get('Codename', '未知')}  |  核心数：{cpu.get('Core Count', '?')}"
        else:
            mb_line = f"Motherboard: {mb.get('Name', 'Unknown')}  |  Chipset: {mb.get('Chipset', 'Unknown')}  |  Platform: {mb.get('Platform', 'Unknown')}"
            bios_line = f"Firmware: {bios.get('Firmware Type', 'Unknown')}  |  Secure Boot: {bios.get('Secure Boot', 'Unknown')}"
            cpu_sub = f"Codename: {cpu.get('Codename', 'Unknown')}  |  Cores: {cpu.get('Core Count', '?')}"

        mb_lbl = BodyLabel(mb_line, overview_card)
        mb_lbl.setWordWrap(True)
        bios_lbl = BodyLabel(bios_line, overview_card)
        bios_lbl.setWordWrap(True)
        ov_layout.addWidget(mb_lbl)
        ov_layout.addWidget(bios_lbl)
        cpu_text, cpu_level = self._format_compat_badge(
            cpu.get("Compatibility"), None, os_name_fn
        )
        ov_layout.addWidget(
            self._make_device_row(
                overview_card,
                f"CPU: {cpu.get('Processor Name', 'Unknown')}",
                cpu_sub,
                cpu_text,
                cpu_level,
            )
        )
        self.cards_layout.addWidget(overview_card)

        categories = [
            "GPU",
            "Network",
            "Sound",
            "Storage Controllers",
            "Bluetooth",
            "SD Controller",
            "Biometric",
        ]
        for cat in categories:
            devices = report.get(cat)
            if not devices or not isinstance(devices, dict):
                continue
            card = CardWidget(self.cards_host)
            lay = QVBoxLayout(card)
            lay.setContentsMargins(18, 14, 18, 14)
            lay.setSpacing(8)
            lay.addWidget(StrongBodyLabel(self.tr_mgr.category(cat), card))

            for dev_name, props in devices.items():
                if not isinstance(props, dict):
                    continue
                sub_parts = []
                if props.get("Device ID"):
                    sub_parts.append(f"ID: {props['Device ID']}")
                if props.get("Codename"):
                    sub_parts.append(("架构: " if zh else "Codename: ") + str(props["Codename"]))
                if props.get("Device Type"):
                    sub_parts.append(props["Device Type"])
                if props.get("Bus Type"):
                    sub_parts.append(("总线: " if zh else "Bus: ") + str(props["Bus Type"]))
                if props.get("Disk Drives"):
                    sub_parts.append(("硬盘: " if zh else "Drives: ") + ", ".join(props["Disk Drives"]))

                badge_text, level = self._format_compat_badge(
                    props.get("Compatibility"),
                    props.get("OCLP Compatibility"),
                    os_name_fn,
                )
                lay.addWidget(
                    self._make_device_row(
                        card, dev_name, "  |  ".join(sub_parts), badge_text, level
                    )
                )
            self.cards_layout.addWidget(card)

    @staticmethod
    def _shorten_path(path_str: str, max_len: int = 58) -> str:
        if len(path_str) <= max_len:
            return path_str
        head = max_len // 2 - 2
        tail = max_len - head - 3
        return f"{path_str[:head]}...{path_str[-tail:]}"

    def _make_device_row(
        self, parent: QWidget, name: str, subtitle: str, badge_text: str, level: str
    ) -> QFrame:
        row = QFrame(parent)
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 4, 0, 4)
        h.setSpacing(12)

        left = QVBoxLayout()
        left.setSpacing(2)
        name_lbl = BodyLabel(name, row)
        name_lbl.setWordWrap(True)
        left.addWidget(name_lbl)
        if subtitle:
            sub_lbl = CaptionLabel(subtitle, row)
            sub_lbl.setWordWrap(True)
            left.addWidget(sub_lbl)
        h.addLayout(left, 1)

        color_map = {
            "ok": "#16a34a",
            "warn": "#ea580c",
            "err": "#dc2626",
            "muted": "#888888",
        }
        badge_lbl = CaptionLabel(badge_text, row)
        badge_lbl.setWordWrap(True)
        badge_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        badge_lbl.setStyleSheet(
            f"color: {color_map.get(level, '#888888')}; font-weight: 600;"
        )
        h.addWidget(badge_lbl, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return row
