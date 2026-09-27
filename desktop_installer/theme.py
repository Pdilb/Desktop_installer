# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Pdilb
"""Ubuntu 风味：读取强调色、跟随深浅色。"""
from __future__ import annotations

import subprocess

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication


# Ubuntu 预设强调色 → RGB
ACCENT_COLORS = {
    "orange":   "#E95420",
    "blue":     "#0073E5",  # Ubuntu 22.10+ 默认
    "purple":   "#9141AC",
    "pink":     "#E91E63",
    "red":      "#E62D42",
    "teal":     "#2190A4",
    "green":    "#3A944A",
    "yellow":   "#C88800",
    "grey":     "#5E5C64",
}


def read_accent_color() -> str:
    """通过 gsettings 读取 GNOME 强调色名，失败回退到 Ubuntu 橙。"""
    try:
        out = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "accent-color"],
            capture_output=True, text=True, check=False, timeout=2,
        )
        if out.returncode == 0:
            name = out.stdout.strip().strip("'\"")
            return ACCENT_COLORS.get(name, ACCENT_COLORS["orange"])
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return ACCENT_COLORS["orange"]


def is_dark_mode(app: QApplication) -> bool:
    """Qt 6.5+ 可直接读取 colorScheme。"""
    try:
        return app.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except AttributeError:
        return False


def apply_theme(app: QApplication) -> None:
    """
    应用 Ubuntu 风味：跟随深浅色 + 用强调色高亮选中项。
    """
    accent = read_accent_color()
    dark = is_dark_mode(app)

    bg = "#1e1e1e" if dark else "#ffffff"
    fg = "#f2f2f2" if dark else "#2e3436"
    base = "#2b2b2b" if dark else "#f6f5f4"
    alt = "#333333" if dark else "#f0efed"
    border = "#3d3d3d" if dark else "#d3d0cb"

    qss = f"""
    QWidget {{
        background-color: {bg};
        color: {fg};
        font-size: 13px;
    }}
    QTabWidget::pane {{
        border-top: 1px solid {border};
    }}
    QTabBar::tab {{
        background: transparent;
        padding: 8px 16px;
        border: none;
        color: {fg};
    }}
    QTabBar::tab:selected {{
        color: {accent};
        border-bottom: 2px solid {accent};
    }}
    QTableWidget {{
        background-color: {base};
        alternate-background-color: {alt};
        gridline-color: {border};
        selection-background-color: {accent};
        selection-color: #ffffff;
        border: 1px solid {border};
    }}
    QHeaderView::section {{
        background-color: {bg};
        color: {fg};
        border: none;
        border-bottom: 1px solid {border};
        padding: 6px 10px;
    }}
    QCheckBox::indicator:checked {{
        background-color: {accent};
        border: 1px solid {accent};
    }}
    QPushButton {{
        background-color: {base};
        border: 1px solid {border};
        border-radius: 6px;
        padding: 6px 18px;
        color: {fg};
    }}
    QPushButton:hover {{
        background-color: {alt};
    }}
    QPushButton:disabled {{
        color: #888888;
        background-color: {base};
    }}
    QPushButton#primary {{
        background-color: {accent};
        color: #ffffff;
        border: 1px solid {accent};
    }}
    QPushButton#primary:disabled {{
        background-color: #9a9a9a;
        border: 1px solid #9a9a9a;
        color: #e0e0e0;
    }}
    QComboBox {{
        background-color: {base};
        border: 1px solid {border};
        border-radius: 6px;
        padding: 4px 10px;
        color: {fg};
    }}
    """
    app.setStyleSheet(qss)