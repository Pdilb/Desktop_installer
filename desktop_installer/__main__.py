# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Pdilb
import sys
from PySide6.QtWidgets import QApplication
from .ui.main_window import MainWindow
from . import __app_name__


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationDisplayName("Desktop Installer")
    app.setOrganizationName("desktop_installer")
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())