"""Persistent application settings for OC-Studio."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict


GITHUB_MIRROR_PRESETS: Dict[str, str] = {
    "direct": "",
    "ghfast": "https://ghfast.top/",
    "ghproxy_net": "https://ghproxy.net/",
    "ghproxy_cc": "https://mirror.ghproxy.com/",
}


def get_app_root() -> Path:
    """Return the root directory of OC-Studio (works in source and PyInstaller)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_core_dir() -> Path:
    """Return the directory of the bundled OpCore-Simplify upstream core."""
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            bundled = Path(meipass) / "core"
            if bundled.exists():
                return bundled
    return get_app_root() / "core"


def get_settings_path() -> Path:
    return get_app_root() / "oc_studio_settings.json"


@dataclass
class AppSettings:
    language: str = "zh_CN"
    theme: str = "auto"  # auto | light | dark
    mirror_mode: str = "direct"  # direct | ghfast | ghproxy_net | ghproxy_cc | custom
    custom_mirror_url: str = ""
    http_proxy: str = ""
    output_dir: str = ""
    auto_check_core: bool = True

    def get_active_mirror_prefix(self) -> str:
        if self.mirror_mode == "custom":
            url = self.custom_mirror_url.strip()
            if url and not url.endswith("/"):
                url += "/"
            return url
        return GITHUB_MIRROR_PRESETS.get(self.mirror_mode, "")

    def get_effective_output_dir(self) -> Path:
        if self.output_dir.strip():
            return Path(self.output_dir.strip())
        return get_app_root() / "Results"

    @classmethod
    def load(cls) -> "AppSettings":
        path = get_settings_path()
        if not path.exists():
            return cls()
        try:
            with open(path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
            valid_fields = {k: v for k, v in raw.items() if k in cls.__dataclass_fields__}
            return cls(**valid_fields)
        except Exception:
            return cls()

    def save(self) -> None:
        path = get_settings_path()
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(asdict(self), fh, ensure_ascii=False, indent=2)
        except OSError:
            pass
