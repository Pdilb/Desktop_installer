# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Pdilb
"""关于对话框，展示版本、作者、协议、依赖等信息。"""
from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from . import (
    __version__,
    __app_display_name__,
    __author__,
    __author_url__,
    __repo_url__,
    __license__,
    __license_url__,
    __description_en__,
)
from .theme import read_accent_color
from .icon import build_icon


class AboutDialog(QDialog):
    """应用内关于对话框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("About"))
        self.setFixedWidth(440)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(14)

        # 图标 + 标题
        header = QHBoxLayout()
        header.setSpacing(16)

        icon_label = QLabel()
        icon = build_icon(read_accent_color(), size=96)
        if not icon.isNull():
            icon_label.setPixmap(icon.pixmap(96, 96))
        header.addWidget(icon_label)

        title_box = QVBoxLayout()
        title = QLabel(f"<b style='font-size:16px'>{__app_display_name__}</b>")
        version = QLabel(f"v{__version__}")
        version.setStyleSheet("color: #888;")
        desc = QLabel(self.tr(__description_en__))
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #888; font-size: 12px;")
        title_box.addWidget(title)
        title_box.addWidget(version)
        title_box.addWidget(desc)
        title_box.addStretch()
        header.addLayout(title_box, stretch=1)
        root.addLayout(header)

        # 信息表
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(8)

        author_label = QLabel(f'<a href="{__author_url__}">{__author__}</a>')
        author_label.setOpenExternalLinks(True)
        form.addRow(self.tr("Author:"), author_label)

        repo_label = QLabel(f'<a href="{__repo_url__}">{__repo_url__}</a>')
        repo_label.setOpenExternalLinks(True)
        form.addRow(self.tr("Source:"), repo_label)

        license_label = QLabel(f'<a href="{__license_url__}">{__license__}</a>')
        license_label.setOpenExternalLinks(True)
        form.addRow(self.tr("License:"), license_label)

        # 第三方依赖
        deps = QLabel("PySide6 (LGPL v3)")
        form.addRow(self.tr("Built with:"), deps)

        root.addLayout(form)

        # 按钮区
        btns = QHBoxLayout()
        copy_btn = QPushButton(self.tr("Copy version info"))
        copy_btn.clicked.connect(self._copy_version_info)
        btns.addWidget(copy_btn)
        btns.addStretch()

        box = QDialogButtonBox(QDialogButtonBox.Close)
        box.rejected.connect(self.reject)
        box.accepted.connect(self.accept)
        btns.addWidget(box)
        root.addLayout(btns)

    def _copy_version_info(self) -> None:
        """复制版本信息到剪贴板，方便用户反馈问题。"""
        info = (
            f"{__app_display_name__} v{__version__}\n"
            f"Author: {__author__} ({__author_url__})\n"
            f"Source: {__repo_url__}\n"
            f"License: {__license__}\n"
            f"OS: {QGuiApplication.platformName()}\n"
        )
        QGuiApplication.clipboard().setText(info)
