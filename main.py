"""OC-Studio entry point."""

from __future__ import annotations

import importlib
import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

import app._core_deps  # noqa: F401  Ensure PyInstaller bundles stdlib deps needed by core/
from app.config import AppSettings
from app.core_adapter import CoreAdapter, CoreEventBridge
from app.ui.main_window import MainWindow


CORE_MODULES = [
    "Scripts.acpi_guru",
    "Scripts.compatibility_checker",
    "Scripts.config_prodigy",
    "Scripts.dsdt",
    "Scripts.gathering_files",
    "Scripts.github",
    "Scripts.hardware_customizer",
    "Scripts.integrity_checker",
    "Scripts.kext_maestro",
    "Scripts.report_validator",
    "Scripts.resource_fetcher",
    "Scripts.run",
    "Scripts.smbios",
    "Scripts.utils",
    "Scripts.wifi_profile_extractor",
]


def _run_smoke_test() -> int:
    """Verify frozen bundle loads CoreAdapter and every upstream core module cleanly."""
    settings = AppSettings.load()
    bridge = CoreEventBridge()
    CoreAdapter(settings, bridge)

    for mod in CORE_MODULES:
        importlib.import_module(mod)

    # On macOS offscreen CI runners, Cocoa NSWindow hooks inside qframelesswindow
    # cannot initialize without a real WindowServer; instantiate full MainWindow elsewhere.
    if not (sys.platform == "darwin" and os.environ.get("QT_QPA_PLATFORM") == "offscreen"):
        window = MainWindow()
        window.close()

    print("OC-Studio smoke test PASSED.")
    return 0


def main() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app_inst = QApplication(sys.argv)
    app_inst.setApplicationName("OC-Studio")

    if "--smoke-test" in sys.argv:
        return _run_smoke_test()

    window = MainWindow()
    window.show()
    return app_inst.exec()


if __name__ == "__main__":
    sys.exit(main())
