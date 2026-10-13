# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Pdilb
"""动态生成 QIcon：SVG + 强调色着色。"""
from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

# 项目内 SVG 路径（源码运行 / 安装后均兼容）
_SVG_CANDIDATES = [
    Path(__file__).parent.parent / "assets" / "desktop_installer.svg",
    Path("/usr/share/icons/hicolor/scalable/apps/desktop_installer.svg"),
]

# SVG 中的占位色，会被替换成强调色
_PLACEHOLDER = "#FF0000"


def _find_svg() -> Path | None:
    for p in _SVG_CANDIDATES:
        if p.exists():
            return p
    return None


def _read_svg_with_accent(accent: str) -> bytes | None:
    """读取 SVG 内容，把占位色替换成强调色。"""
    svg_path = _find_svg()
    if svg_path is None:
        return None
    try:
        text = svg_path.read_text(encoding="utf-8")
    except OSError:
        return None
    text = text.replace(_PLACEHOLDER, accent)
    text = text.replace(_PLACEHOLDER.lower(), accent)
    return text.encode("utf-8")


def build_icon(accent: str, size: int = 256) -> QIcon:
    """根据强调色生成 QIcon。失败时返回空 QIcon。"""
    data = _read_svg_with_accent(accent)
    if data is None:
        return QIcon()

    renderer = QSvgRenderer(QByteArray(data))
    if not renderer.isValid():
        return QIcon()

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)
