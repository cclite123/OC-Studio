"""Interactive dialogs bridging upstream core prompts to Fluent UI."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QButtonGroup, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    LineEdit,
    MessageBoxBase,
    PlainTextEdit,
    RadioButton,
    SubtitleLabel,
)

from app.core_adapter import PromptRequest


def _translate_prompt_title(prompt: str) -> str:
    lower = prompt.lower()
    if "uefi" in lower:
        return "BIOS 启动模式确认"
    if "gpu" in lower:
        return "选择显卡配置方案"
    if "wi-fi" in lower or "wifi" in lower:
        return "选择 Intel Wi-Fi 驱动方案"
    if "bluetooth" in lower:
        return "选择蓝牙设备"
    if "force load" in lower:
        return "确认是否强制加载不兼容驱动"
    return "内核需要你做个选择"


class CorePromptDialog(MessageBoxBase):
    """Modal Fluent dialog for interactive decisions requested by OpCore-Simplify."""

    def __init__(self, req: PromptRequest, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.req = req
        self._selected_value = req.default_value

        self.titleLabel = SubtitleLabel(_translate_prompt_title(req.prompt), self)
        self.viewLayout.addWidget(self.titleLabel)

        # Show concise upstream context
        context_text = "\n".join(req.context_lines[-16:]).strip()
        if context_text:
            self.contextBox = PlainTextEdit(self)
            self.contextBox.setReadOnly(True)
            self.contextBox.setPlainText(context_text)
            self.contextBox.setFixedHeight(170)
            self.viewLayout.addWidget(self.contextBox)

        self.promptLabel = BodyLabel(req.prompt, self)
        self.promptLabel.setWordWrap(True)
        self.viewLayout.addWidget(self.promptLabel)

        self._radio_group = QButtonGroup(self)
        self._input_edit: Optional[LineEdit] = None

        if req.kind in ("yes_no", "choice") and req.options:
            opt_container = QWidget(self)
            opt_layout = QVBoxLayout(opt_container)
            opt_layout.setContentsMargins(0, 6, 0, 6)
            opt_layout.setSpacing(8)
            for idx, (val, label) in enumerate(req.options):
                rb = RadioButton(label, opt_container)
                rb.setProperty("return_value", val)
                if val == req.default_value or (idx == 0 and not req.default_value):
                    rb.setChecked(True)
                    self._selected_value = val
                self._radio_group.addButton(rb)
                opt_layout.addWidget(rb)
            self.viewLayout.addWidget(opt_container)
        else:
            self._input_edit = LineEdit(self)
            self._input_edit.setText(req.default_value)
            self.viewLayout.addWidget(self._input_edit)

        self.yesButton.setText("确定")
        self.cancelButton.setText("使用推荐默认值")
        self.widget.setMinimumWidth(520)

    def get_answer(self) -> str:
        if self._input_edit is not None:
            return self._input_edit.text().strip() or self.req.default_value
        checked = self._radio_group.checkedButton()
        if checked is not None:
            return str(checked.property("return_value"))
        return self._selected_value


class DetailErrorDialog(MessageBoxBase):
    """Readable error dialog with scrollable stack/log details."""

    def __init__(self, title: str, detail: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(title, self)
        self.viewLayout.addWidget(self.titleLabel)

        self.detailBox = PlainTextEdit(self)
        self.detailBox.setReadOnly(True)
        self.detailBox.setPlainText(detail)
        self.detailBox.setFixedHeight(240)
        self.viewLayout.addWidget(self.detailBox)

        self.yesButton.setText("我知道了")
        self.cancelButton.hide()
        self.widget.setMinimumWidth(540)
