# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Pdilb
import argparse
import sys
from pathlib import Path

from . import (
    __app_name__,
    __app_display_name__,
    __version__,
    __description__,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=__app_name__,
        description=__description__,
    )
    parser.add_argument(
        "--version", action="version",
        version=f"{__app_name__} {__version__}",
    )
    parser.add_argument(
        "--nogui", action="store_true",
        help="run in interactive command-line mode",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.nogui:
        from .cli import run_interactive
        return run_interactive()

    return _run_gui()


def _run_gui() -> int:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QLocale, QTranslator

    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationDisplayName(__app_display_name__)
    app.setOrganizationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setDesktopFileName("desktop_installer")

    translator = QTranslator(app)
    sys_locale = QLocale.system().name()
    target = "zh_CN" if sys_locale.startswith("zh") else "en_US"
    for base in [
        Path(__file__).parent / "i18n",
        Path("/usr/share/desktop_installer/i18n"),
        Path("/usr/lib/python3/dist-packages/desktop_installer/i18n"),
    ]:
        qm = base / f"desktop_installer_{target}.qm"
        if qm.exists() and translator.load(str(qm)):
            app.installTranslator(translator)
            break

    from .theme import apply_theme, read_accent_color
    apply_theme(app)

    from .icon import build_icon
    icon = build_icon(read_accent_color(), size=256)
    if not icon.isNull():
        app.setWindowIcon(icon)

    from .ui.main_window import MainWindow
    win = MainWindow()
    win.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
