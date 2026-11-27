"""Welcome home page for OC-Studio."""

from __future__ import annotations

from typing import List, Optional, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QWidget
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

from app import APP_VERSION, UPSTREAM_REPO
from app.core_updater import CoreVersionInfo
from app.i18n import Translator


class HomePage(ScrollArea):
    """Clean welcome & workflow overview page with live i18n & theme support."""

    start_requested = Signal()
    open_diff_requested = Signal()
    open_settings_requested = Signal()

    def __init__(self, translator: Translator, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.tr_mgr = translator
        self._last_core_info: Optional[CoreVersionInfo] = None
        self.setObjectName("homePage")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.container = QWidget(self)
        self.setWidget(self.container)
        self.enableTransparentBackground()

        root = QVBoxLayout(self.container)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(18)

        # Hero Card
        hero_card = CardWidget(self.container)
        hero_lay = QVBoxLayout(hero_card)
        hero_lay.setContentsMargins(26, 24, 26, 24)
        hero_lay.setSpacing(10)

        self.welcome_label = TitleLabel("", hero_card)
        self.hero_sub = BodyLabel("", hero_card)
        self.hero_sub.setWordWrap(True)
        self.core_badge_label = CaptionLabel("", hero_card)
        self.core_badge_label.setWordWrap(True)

        hero_lay.addWidget(self.welcome_label)
        hero_lay.addWidget(self.hero_sub)
        hero_lay.addWidget(self.core_badge_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        self.start_btn = PrimaryPushButton(FluentIcon.PLAY, "", hero_card)
        self.start_btn.clicked.connect(self.start_requested.emit)

        self.diff_btn = PushButton(FluentIcon.DOCUMENT, "", hero_card)
        self.diff_btn.clicked.connect(self.open_diff_requested.emit)

        self.settings_btn = PushButton(FluentIcon.SETTING, "", hero_card)
        self.settings_btn.clicked.connect(self.open_settings_requested.emit)

        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.diff_btn)
        btn_row.addWidget(self.settings_btn)
        btn_row.addStretch(1)
        hero_lay.addLayout(btn_row)

        root.addWidget(hero_card)

        # 4-Step Guide Grid
        self.steps_title = SubtitleLabel("", self.container)
        root.addWidget(self.steps_title)

        grid_host = QWidget(self.container)
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(12)

        self._step_labels: List[Tuple[StrongBodyLabel, CaptionLabel]] = []
        for idx in range(4):
            card = CardWidget(grid_host)
            lay = QVBoxLayout(card)
            lay.setContentsMargins(18, 16, 18, 16)
            lay.setSpacing(6)
            t_lbl = StrongBodyLabel("", card)
            b_lbl = CaptionLabel("", card)
            b_lbl.setWordWrap(True)
            lay.addWidget(t_lbl)
            lay.addWidget(b_lbl)
            lay.addStretch(1)
            grid.addWidget(card, idx // 2, idx % 2)
            self._step_labels.append((t_lbl, b_lbl))

        root.addWidget(grid_host)

        # Friendly reminder card
        tip_card = CardWidget(self.container)
        tip_lay = QVBoxLayout(tip_card)
        tip_lay.setContentsMargins(20, 14, 20, 14)
        tip_lay.setSpacing(4)
        self.tip_title = StrongBodyLabel("", tip_card)
        self.tip_body = CaptionLabel("", tip_card)
        self.tip_body.setWordWrap(True)
        tip_lay.addWidget(self.tip_title)
        tip_lay.addWidget(self.tip_body)
        root.addWidget(tip_card)

        root.addStretch(1)
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        t = self.tr_mgr.t
        self.welcome_label.setText(t("home.welcome"))
        self.hero_sub.setText(t("home.subtitle"))
        self.start_btn.setText(t("home.start_btn"))
        self.diff_btn.setText(t("home.diff_btn"))
        self.settings_btn.setText(t("home.settings_btn"))
        self.steps_title.setText(t("home.steps_title"))
        for idx, (t_lbl, b_lbl) in enumerate(self._step_labels, start=1):
            t_lbl.setText(t(f"home.step{idx}_title"))
            b_lbl.setText(t(f"home.step{idx}_desc"))
        self.tip_title.setText(t("home.tip_title"))
        self.tip_body.setText(t("home.tip_body"))
        if self._last_core_info is not None:
            self.update_core_info(self._last_core_info)
        else:
            self.core_badge_label.setText(
                t("home.core_badge", ver=APP_VERSION, repo=UPSTREAM_REPO, sha="...", date="...")
            )

    def update_core_info(self, info: CoreVersionInfo) -> None:
        self._last_core_info = info
        self.core_badge_label.setText(
            self.tr_mgr.t(
                "home.core_badge",
                ver=APP_VERSION,
                repo=UPSTREAM_REPO,
                sha=info.short_local_sha,
                date=info.local_date or "bundled",
            )
        )
