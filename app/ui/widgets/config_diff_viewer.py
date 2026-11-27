"""Tree-based config.plist diff viewer widget & dialog."""

from __future__ import annotations

import binascii
import plistlib
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    CheckBox,
    FluentIcon,
    PushButton,
    SearchLineEdit,
    StrongBodyLabel,
    SubtitleLabel,
)


def _format_value(val: Any) -> str:
    if val is None:
        return "—"
    if isinstance(val, bool):
        return "True" if val else "False"
    if isinstance(val, (bytes, bytearray)):
        hex_str = binascii.hexlify(val).decode("ascii").upper()
        if len(hex_str) > 40:
            hex_str = hex_str[:40] + f"... ({len(val)} bytes)"
        return f"<{hex_str}>"
    if isinstance(val, dict):
        return f"{{...}} ({len(val)} 项)"
    if isinstance(val, list):
        return f"[...] ({len(val)} 项)"
    text = str(val)
    if len(text) > 120:
        return text[:117] + "..."
    return text


def _type_name(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, bool):
        return "Boolean"
    if isinstance(val, int):
        return "Number"
    if isinstance(val, (bytes, bytearray)):
        return "Data"
    if isinstance(val, dict):
        return "Dictionary"
    if isinstance(val, list):
        return "Array"
    return "String"


def _values_equal(a: Any, b: Any) -> bool:
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        if a.keys() != b.keys():
            return False
        return all(_values_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        if len(a) != len(b):
            return False
        return all(_values_equal(x, y) for x, y in zip(a, b))
    return a == b


class ConfigDiffViewer(QWidget):
    """Interactive tree diff viewer comparing Sample.plist and generated config.plist."""

    CHANGE_COLORS = {
        "added": QColor(16, 124, 16),      # Green
        "modified": QColor(202, 80, 16),   # Orange
        "removed": QColor(197, 15, 31),    # Red
    }

    CHANGE_LABELS = {
        "added": "新增",
        "modified": "修改",
        "removed": "删除",
        "unchanged": "未变",
    }

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._original: Dict[str, Any] = {}
        self._generated: Dict[str, Any] = {}
        self._stats = {"added": 0, "modified": 0, "removed": 0}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self.only_changed_cb = CheckBox("仅显示有变动的项", self)
        self.only_changed_cb.setChecked(True)
        self.only_changed_cb.stateChanged.connect(self._rebuild_tree)

        self.search_edit = SearchLineEdit(self)
        self.search_edit.setPlaceholderText("搜索键名或值（如 boot-args、SMBIOS）...")
        self.search_edit.setFixedWidth(280)
        self.search_edit.textChanged.connect(self._apply_search)

        self.expand_btn = PushButton(FluentIcon.DOWN, "全部展开", self)
        self.expand_btn.clicked.connect(lambda: self.tree.expandAll())

        self.collapse_btn = PushButton(FluentIcon.UP, "全部折叠", self)
        self.collapse_btn.clicked.connect(lambda: self.tree.collapseAll())

        self.open_plist_btn = PushButton(FluentIcon.DOCUMENT, "打开外部 .plist", self)
        self.open_plist_btn.clicked.connect(self._open_external_plist)

        toolbar.addWidget(self.only_changed_cb)
        toolbar.addWidget(self.search_edit)
        toolbar.addStretch(1)
        toolbar.addWidget(self.expand_btn)
        toolbar.addWidget(self.collapse_btn)
        toolbar.addWidget(self.open_plist_btn)
        layout.addLayout(toolbar)

        # Stats bar
        self.stats_label = CaptionLabel("尚未加载配置对比数据。", self)
        layout.addWidget(self.stats_label)

        # Tree widget
        self.tree = QTreeWidget(self)
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels(["配置键 (Key)", "变更", "类型", "模板原值 (Sample)", "生成新值 (Final)"])
        self.tree.setAlternatingRowColors(True)
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.tree.setColumnWidth(0, 260)
        layout.addWidget(self.tree, 1)

    def load_configs(
        self, original: Optional[Dict[str, Any]], generated: Optional[Dict[str, Any]]
    ) -> None:
        self._original = original or {}
        self._generated = generated or {}
        self._rebuild_tree()

    def _open_external_plist(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "选择要查看的 config.plist 文件", "", "Property List (*.plist);;所有文件 (*.*)"
        )
        if not path:
            return
        try:
            with open(path, "rb") as fh:
                data = plistlib.load(fh)
            if isinstance(data, dict):
                self._original = {}
                self._generated = data
                self.only_changed_cb.setChecked(False)
                self._rebuild_tree()
                self.stats_label.setText(f"正在查看单个文件：{path}")
        except Exception as exc:
            self.stats_label.setText(f"读取 plist 失败：{exc}")

    def _rebuild_tree(self) -> None:
        self.tree.clear()
        self._stats = {"added": 0, "modified": 0, "removed": 0}
        only_changed = self.only_changed_cb.isChecked()

        if not self._original and not self._generated:
            self.stats_label.setText("尚未加载配置对比数据（生成 EFI 后会自动填充）。")
            return

        self._populate_dict(self.tree.invisibleRootItem(), self._original, self._generated, only_changed)

        self.stats_label.setText(
            f"变更统计：新增 {self._stats['added']} 项  |  修改 {self._stats['modified']} 项  |  删除 {self._stats['removed']} 项"
        )
        # Expand top-level sections by default for quick scanning
        for i in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(i).setExpanded(True)
        self._apply_search(self.search_edit.text())

    def _style_item(self, item: QTreeWidgetItem, change: str) -> None:
        color = self.CHANGE_COLORS.get(change)
        if color is not None:
            brush = QBrush(color)
            item.setForeground(0, brush)
            item.setForeground(1, brush)
            item.setForeground(4 if change != "removed" else 3, brush)

    def _populate_dict(
        self,
        parent: QTreeWidgetItem,
        orig: Dict[str, Any],
        gen: Dict[str, Any],
        only_changed: bool,
    ) -> bool:
        """Populate dict keys and return whether any descendant changed."""
        any_changed = False
        all_keys = sorted(set(orig.keys()) | set(gen.keys()))

        for key in all_keys:
            in_o = key in orig
            in_g = key in gen
            val_o = orig.get(key)
            val_g = gen.get(key)

            if in_o and in_g:
                if _values_equal(val_o, val_g):
                    change = "unchanged"
                else:
                    change = "modified"
            elif in_g:
                change = "added"
            else:
                change = "removed"

            if only_changed and change == "unchanged":
                continue

            if change != "unchanged":
                any_changed = True

            is_nested_dict = isinstance(val_o, dict) and isinstance(val_g, dict)
            is_nested_list = isinstance(val_o, list) and isinstance(val_g, list)
            is_single_container = (
                (in_g and not in_o and isinstance(val_g, (dict, list)))
                or (in_o and not in_g and isinstance(val_o, (dict, list)))
            )

            eff_val = val_g if in_g else val_o
            item = QTreeWidgetItem(
                [
                    str(key),
                    self.CHANGE_LABELS[change],
                    _type_name(eff_val),
                    _format_value(val_o) if in_o else "—",
                    _format_value(val_g) if in_g else "—",
                ]
            )
            self._style_item(item, change)

            if is_nested_dict:
                self._populate_dict(item, val_o, val_g, only_changed)
            elif is_nested_list:
                self._populate_list(item, val_o, val_g, only_changed)
            elif is_single_container:
                if change in self._stats:
                    self._stats[change] += 1
                if isinstance(eff_val, dict):
                    self._populate_dict(item, val_o if in_o else {}, val_g if in_g else {}, False)
                elif isinstance(eff_val, list):
                    self._populate_list(item, val_o if in_o else [], val_g if in_g else [], False)
            else:
                if change in self._stats:
                    self._stats[change] += 1

            parent.addChild(item)

        return any_changed

    def _populate_list(
        self,
        parent: QTreeWidgetItem,
        orig: List[Any],
        gen: List[Any],
        only_changed: bool,
    ) -> None:
        max_len = max(len(orig), len(gen))
        for i in range(max_len):
            in_o = i < len(orig)
            in_g = i < len(gen)
            val_o = orig[i] if in_o else None
            val_g = gen[i] if in_g else None

            if in_o and in_g:
                change = "unchanged" if _values_equal(val_o, val_g) else "modified"
            elif in_g:
                change = "added"
            else:
                change = "removed"

            if only_changed and change == "unchanged":
                continue

            eff_val = val_g if in_g else val_o
            label = f"[{i}]"
            if isinstance(eff_val, dict):
                hint = eff_val.get("BundlePath") or eff_val.get("Path") or eff_val.get("Comment")
                if hint:
                    label = f"[{i}] {hint}"

            item = QTreeWidgetItem(
                [
                    label,
                    self.CHANGE_LABELS[change],
                    _type_name(eff_val),
                    _format_value(val_o) if in_o else "—",
                    _format_value(val_g) if in_g else "—",
                ]
            )
            self._style_item(item, change)

            if isinstance(val_o, dict) and isinstance(val_g, dict):
                self._populate_dict(item, val_o, val_g, only_changed)
            elif isinstance(eff_val, dict):
                if change in self._stats:
                    self._stats[change] += 1
                self._populate_dict(item, val_o if in_o else {}, val_g if in_g else {}, False)
            elif isinstance(val_o, list) and isinstance(val_g, list):
                self._populate_list(item, val_o, val_g, only_changed)
            else:
                if change in self._stats:
                    self._stats[change] += 1

            parent.addChild(item)

    def _apply_search(self, keyword: str) -> None:
        q = keyword.strip().lower()

        def _filter_node(item: QTreeWidgetItem) -> bool:
            text_match = (not q) or any(
                q in (item.text(col) or "").lower() for col in (0, 3, 4)
            )
            child_match = False
            for idx in range(item.childCount()):
                if _filter_node(item.child(idx)):
                    child_match = True
            visible = text_match or child_match
            item.setHidden(not visible)
            if q and child_match:
                item.setExpanded(True)
            return visible

        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            _filter_node(root.child(i))


class ConfigDiffDialog(QDialog):
    """Standalone resizable dialog hosting ConfigDiffViewer."""

    def __init__(
        self,
        original: Optional[Dict[str, Any]],
        generated: Optional[Dict[str, Any]],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("config.plist 配置树形对比查看器")
        self.resize(1020, 680)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        layout.addWidget(SubtitleLabel("config.plist 对比视图（模板 vs 最终生成）", self))
        self.viewer = ConfigDiffViewer(self)
        self.viewer.load_configs(original, generated)
        layout.addWidget(self.viewer, 1)
