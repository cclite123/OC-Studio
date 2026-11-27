"""Step 3: Customize ACPI patches, Kexts, SMBIOS model, and Audio Layout ID."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    CheckBox,
    FluentIcon,
    Pivot,
    PrimaryPushButton,
    PushButton,
    RadioButton,
    ScrollArea,
    SearchLineEdit,
    StrongBodyLabel,
    TitleLabel,
)

from app.i18n import Translator


class CustomizePage(QWidget):
    """Step 3 page: tabbed customization for ACPI / Kext / SMBIOS / Audio."""

    acpi_toggled = Signal(int, bool)
    kext_toggled = Signal(int, bool)
    smbios_selected = Signal(str)
    smbios_restore_requested = Signal()
    audio_layout_selected = Signal(int)
    audio_layout_restore_requested = Signal()
    next_requested = Signal()

    def __init__(self, translator: Translator, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.tr_mgr = translator
        self._last_adapter: Any = None
        self.setObjectName("customizePage")

        self._acpi_rows: List[tuple[str, QWidget, CheckBox]] = []
        self._kext_rows: List[tuple[str, QWidget, CheckBox]] = []
        self._smbios_rows: List[tuple[str, QWidget]] = []
        self._audio_rows: List[tuple[str, QWidget]] = []
        self._tab_widgets: Dict[str, QWidget] = {}
        self._smbios_models: List[Dict[str, Any]] = []
        self._smbios_btn_group = QButtonGroup(self)
        self._audio_btn_group = QButtonGroup(self)
        self._show_all_smbios = False
        self._is_rebuilding = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        # Header
        top_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        self.title_label = TitleLabel("", self)
        self.desc_label = BodyLabel("", self)
        self.desc_label.setWordWrap(True)
        title_box.addWidget(self.title_label)
        title_box.addWidget(self.desc_label)
        top_row.addLayout(title_box, 1)

        self.next_btn = PrimaryPushButton(FluentIcon.RIGHT_ARROW, "", self)
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self.next_requested.emit)
        top_row.addWidget(self.next_btn, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(top_row)

        # Pivot tabs + Search bar
        bar_row = QHBoxLayout()
        self.pivot = Pivot(self)
        self.search_edit = SearchLineEdit(self)
        self.search_edit.setFixedWidth(260)
        self.search_edit.textChanged.connect(self._apply_filter)

        bar_row.addWidget(self.pivot)
        bar_row.addStretch(1)
        bar_row.addWidget(self.search_edit)
        layout.addLayout(bar_row)

        self.stack = QStackedWidget(self)
        layout.addWidget(self.stack, 1)

        # Tab 1: ACPI
        self.acpi_scroll, self.acpi_list_layout = self._make_scroll_tab()
        self._add_tab("acpi", "ACPI", self.acpi_scroll)

        # Tab 2: Kexts
        self.kext_scroll, self.kext_list_layout = self._make_scroll_tab()
        self._add_tab("kext", "Kexts", self.kext_scroll)

        # Tab 3: SMBIOS
        smbios_tab = QWidget(self)
        smbios_outer = QVBoxLayout(smbios_tab)
        smbios_outer.setContentsMargins(0, 6, 0, 0)
        smbios_outer.setSpacing(10)

        smbios_ctrl = QHBoxLayout()
        self.smbios_info_label = StrongBodyLabel("", smbios_tab)
        self.show_all_cb = CheckBox("", smbios_tab)
        self.show_all_cb.stateChanged.connect(self._on_show_all_changed)
        self.restore_smbios_btn = PushButton(FluentIcon.SYNC, "", smbios_tab)
        self.restore_smbios_btn.clicked.connect(self.smbios_restore_requested.emit)
        smbios_ctrl.addWidget(self.smbios_info_label)
        smbios_ctrl.addStretch(1)
        smbios_ctrl.addWidget(self.show_all_cb)
        smbios_ctrl.addWidget(self.restore_smbios_btn)
        smbios_outer.addLayout(smbios_ctrl)

        self.smbios_scroll, self.smbios_list_layout = self._make_scroll_tab()
        smbios_outer.addWidget(self.smbios_scroll, 1)
        self._add_tab("smbios", "SMBIOS", smbios_tab)

        # Tab 4: Audio Layout ID
        audio_tab = QWidget(self)
        audio_outer = QVBoxLayout(audio_tab)
        audio_outer.setContentsMargins(0, 6, 0, 0)
        audio_outer.setSpacing(10)

        audio_ctrl = QHBoxLayout()
        self.audio_info_label = StrongBodyLabel("", audio_tab)
        self.restore_audio_btn = PushButton(FluentIcon.SYNC, "", audio_tab)
        self.restore_audio_btn.clicked.connect(self.audio_layout_restore_requested.emit)
        self.restore_audio_btn.setEnabled(False)
        audio_ctrl.addWidget(self.audio_info_label, 1)
        audio_ctrl.addWidget(self.restore_audio_btn)
        audio_outer.addLayout(audio_ctrl)

        self.audio_tip_label = CaptionLabel("", audio_tab)
        self.audio_tip_label.setWordWrap(True)
        audio_outer.addWidget(self.audio_tip_label)

        self.audio_scroll, self.audio_list_layout = self._make_scroll_tab()
        audio_outer.addWidget(self.audio_scroll, 1)
        self._add_tab("audio", "Audio", audio_tab)

        self.pivot.currentItemChanged.connect(self._on_tab_changed)
        self.pivot.setCurrentItem("acpi")
        self.stack.setCurrentIndex(0)
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        t = self.tr_mgr.t
        self.title_label.setText(t("custom.title"))
        self.desc_label.setText(t("custom.desc"))
        self.next_btn.setText(t("custom.next_btn"))
        self.search_edit.setPlaceholderText(t("custom.search_placeholder"))
        self.show_all_cb.setText(t("custom.show_all_smbios"))
        self.restore_smbios_btn.setText(t("custom.restore_default"))
        self.restore_audio_btn.setText(t("custom.restore_audio"))
        self.audio_tip_label.setText(t("custom.audio_tip"))

        tab_map = {
            "acpi": t("custom.tab_acpi"),
            "kext": t("custom.tab_kext"),
            "smbios": t("custom.tab_smbios"),
            "audio": t("custom.tab_audio"),
        }
        for key, label in tab_map.items():
            item = self.pivot.widget(key)
            if item is not None:
                item.setText(label)

        if self._last_adapter is not None:
            self.update_state(self._last_adapter)
        else:
            self.smbios_info_label.setText(t("custom.smbios_current", model="-"))
            self.audio_info_label.setText(t("custom.audio_none"))

    def _on_tab_changed(self, route_key: str) -> None:
        widget = self._tab_widgets.get(route_key)
        if widget is not None:
            self.stack.setCurrentWidget(widget)

    def _make_scroll_tab(self) -> tuple[ScrollArea, QVBoxLayout]:
        area = ScrollArea(self)
        area.setWidgetResizable(True)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        inner = QWidget(area)
        area.setWidget(inner)
        area.enableTransparentBackground()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(0, 6, 8, 12)
        lay.setSpacing(8)
        lay.addStretch(1)
        return area, lay

    def _add_tab(self, route_key: str, text: str, widget: QWidget) -> None:
        self._tab_widgets[route_key] = widget
        self.stack.addWidget(widget)
        self.pivot.addItem(
            routeKey=route_key,
            text=text,
            onClick=lambda _checked=False, w=widget: self.stack.setCurrentWidget(w),
        )

    def _clear_layout(self, lay: QVBoxLayout) -> None:
        while lay.count():
            item = lay.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def update_state(self, adapter: Any) -> None:
        self._last_adapter = adapter
        if not adapter.hardware_report or not adapter.macos_version:
            self.next_btn.setEnabled(False)
            return

        self.next_btn.setEnabled(True)
        self._is_rebuilding = True
        try:
            self._render_acpi(adapter)
            self._render_kexts(adapter)
            self._render_smbios(adapter)
            self._render_audio_layouts(adapter)
        finally:
            self._is_rebuilding = False
        self._apply_filter(self.search_edit.text())

    def _render_acpi(self, adapter: Any) -> None:
        self._clear_layout(self.acpi_list_layout)
        self._acpi_rows.clear()
        parent = self.acpi_scroll.widget()

        for idx, patch in enumerate(adapter.ac.patches):
            card = CardWidget(parent)
            h = QHBoxLayout(card)
            h.setContentsMargins(16, 10, 16, 10)
            h.setSpacing(12)

            cb = CheckBox(patch.name, card)
            cb.setChecked(bool(patch.checked))
            cb.setMinimumWidth(160)
            cb.stateChanged.connect(
                lambda state, i=idx: (
                    not self._is_rebuilding
                    and self.acpi_toggled.emit(i, state == Qt.CheckState.Checked.value)
                )
            )

            desc_text = self.tr_mgr.acpi_desc(patch.name, patch.description)
            desc_lbl = CaptionLabel(desc_text, card)
            desc_lbl.setWordWrap(True)

            h.addWidget(cb)
            h.addWidget(desc_lbl, 1)
            self.acpi_list_layout.addWidget(card)
            self._acpi_rows.append((f"{patch.name} {desc_text} {patch.description}".lower(), card, cb))

        self.acpi_list_layout.addStretch(1)

    def _render_kexts(self, adapter: Any) -> None:
        self._clear_layout(self.kext_list_layout)
        self._kext_rows.clear()
        parent = self.kext_scroll.widget()
        macos_ver = adapter.macos_version
        zh = self.tr_mgr.is_zh

        status_labels = {
            "required": ("必需" if zh else "Required", "#16a34a"),
            "selected": ("已选" if zh else "Selected", "#0078d4"),
            "force_loaded": ("强制加载" if zh else "Force Loaded", "#ea580c"),
            "available": ("可选" if zh else "Available", "#888888"),
            "force_available": ("可强制加载" if zh else "Force Available", "#ea580c"),
            "not_needed": ("当前系统不需要" if zh else "Not Needed", "#888888"),
            "requires_newer": ("需更高系统版本" if zh else "Requires Newer OS", "#888888"),
        }

        last_cat = None
        for idx, kext in enumerate(adapter.k.kexts):
            if kext.category != last_cat:
                last_cat = kext.category
                cat_lbl = StrongBodyLabel(last_cat or ("其他" if zh else "Other"), parent)
                cat_lbl.setContentsMargins(4, 8, 0, 2)
                self.kext_list_layout.addWidget(cat_lbl)

            status = adapter.k.get_kext_status(kext, macos_ver)
            card = CardWidget(parent)
            h = QHBoxLayout(card)
            h.setContentsMargins(16, 10, 16, 10)
            h.setSpacing(12)

            cb = CheckBox(kext.name, card)
            cb.setChecked(bool(kext.checked))
            cb.setMinimumWidth(220)
            if status in ("required", "not_needed", "requires_newer"):
                cb.setEnabled(False)
            cb.stateChanged.connect(
                lambda state, i=idx: (
                    not self._is_rebuilding
                    and self.kext_toggled.emit(i, state == Qt.CheckState.Checked.value)
                )
            )

            desc_lbl = CaptionLabel(kext.description, card)
            desc_lbl.setWordWrap(True)

            tag_text, tag_color = status_labels.get(status, (status, "#888888"))
            tag_lbl = CaptionLabel(tag_text, card)
            tag_lbl.setStyleSheet(f"color: {tag_color}; font-weight: 600;")

            h.addWidget(cb)
            h.addWidget(desc_lbl, 1)
            h.addWidget(tag_lbl)
            self.kext_list_layout.addWidget(card)
            self._kext_rows.append((f"{kext.name} {kext.description} {kext.category}".lower(), card, cb))

        self.kext_list_layout.addStretch(1)

    def _render_smbios(self, adapter: Any) -> None:
        t = self.tr_mgr.t
        self._smbios_models = adapter.get_smbios_models(show_all=self._show_all_smbios)
        self.smbios_info_label.setText(t("custom.smbios_current", model=adapter.smbios_model or "-"))

        for btn in list(self._smbios_btn_group.buttons()):
            self._smbios_btn_group.removeButton(btn)
        self._clear_layout(self.smbios_list_layout)
        self._smbios_rows.clear()
        parent = self.smbios_scroll.widget()

        for m in self._smbios_models:
            card = CardWidget(parent)
            h = QHBoxLayout(card)
            h.setContentsMargins(16, 10, 16, 10)
            h.setSpacing(12)

            rb = RadioButton(m["name"], card)
            rb.setMinimumWidth(160)
            rb.setChecked(bool(m["is_selected"]))
            rb.toggled.connect(
                lambda checked, name=m["name"]: (
                    checked and (not self._is_rebuilding) and self.smbios_selected.emit(name)
                )
            )
            self._smbios_btn_group.addButton(rb)

            detail = f"{m['cpu']} ({m['cpu_generation']})"
            if m["discrete_gpu"]:
                detail += f"  |  {m['discrete_gpu']}"
            desc_lbl = CaptionLabel(detail, card)
            desc_lbl.setWordWrap(True)

            h.addWidget(rb)
            h.addWidget(desc_lbl, 1)

            if m["is_default"]:
                rec = CaptionLabel(t("custom.rec_badge"), card)
                rec.setStyleSheet("color: #0078d4; font-weight: 600;")
                h.addWidget(rec)
            if not m["supported"]:
                unsup = CaptionLabel(t("custom.unsup_badge"), card)
                unsup.setStyleSheet("color: #dc2626;")
                h.addWidget(unsup)

            self.smbios_list_layout.addWidget(card)
            self._smbios_rows.append((f"{m['name']} {detail}".lower(), card))

        self.smbios_list_layout.addStretch(1)

    def _render_audio_layouts(self, adapter: Any) -> None:
        t = self.tr_mgr.t
        for btn in list(self._audio_btn_group.buttons()):
            self._audio_btn_group.removeButton(btn)
        self._clear_layout(self.audio_list_layout)
        self._audio_rows.clear()
        parent = self.audio_scroll.widget()

        info = adapter.get_audio_codec_info()
        if not info:
            self.audio_info_label.setText(t("custom.audio_none"))
            self.restore_audio_btn.setEnabled(False)
            self.audio_list_layout.addWidget(BodyLabel(t("custom.audio_none_tip"), parent))
            self.audio_list_layout.addStretch(1)
            return

        self.restore_audio_btn.setEnabled(True)
        self.audio_info_label.setText(
            t("custom.audio_header", name=info["codec_name"], cid=info["codec_id"], lid=info["selected_id"])
        )

        for item in info["layouts"]:
            card = CardWidget(parent)
            h = QHBoxLayout(card)
            h.setContentsMargins(16, 10, 16, 10)
            h.setSpacing(12)

            rb = RadioButton(f"Layout ID {item['id']}", card)
            rb.setMinimumWidth(140)
            rb.setChecked(bool(item["selected"]))
            rb.toggled.connect(
                lambda checked, lid=item["id"]: (
                    checked and (not self._is_rebuilding) and self.audio_layout_selected.emit(lid)
                )
            )
            self._audio_btn_group.addButton(rb)

            comment_lbl = CaptionLabel(item["comment"], card)
            comment_lbl.setWordWrap(True)

            h.addWidget(rb)
            h.addWidget(comment_lbl, 1)

            if item["recommended"]:
                rec = CaptionLabel(t("custom.audio_rec_badge"), card)
                rec.setStyleSheet("color: #0078d4; font-weight: 600;")
                h.addWidget(rec)

            self.audio_list_layout.addWidget(card)
            self._audio_rows.append((f"{item['id']} {item['comment']}".lower(), card))

        self.audio_list_layout.addStretch(1)

    def _on_show_all_changed(self, state: int) -> None:
        self._show_all_smbios = state == Qt.CheckState.Checked.value
        parent_win = self.window()
        if hasattr(parent_win, "refresh_customize_page"):
            parent_win.refresh_customize_page()

    def _apply_filter(self, keyword: str) -> None:
        q = keyword.strip().lower()
        for text, card, _ in self._acpi_rows:
            card.setVisible((not q) or (q in text))
        for text, card, _ in self._kext_rows:
            card.setVisible((not q) or (q in text))
        for text, card in self._smbios_rows:
            card.setVisible((not q) or (q in text))
        for text, card in self._audio_rows:
            card.setVisible((not q) or (q in text))
