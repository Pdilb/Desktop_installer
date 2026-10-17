# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Pdilb
"""关于对话框，展示版本、作者、协议、依赖等信息，并支持检查更新。"""
from __future__ import annotations

import json
import urllib.request
from urllib.error import URLError

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
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
    __description_en__,  # 使用这个作为源字符串
    __api_latest_release__,
)
from .theme import read_accent_color
from .icon import build_icon


# ---------- 后台线程：检查更新 ----------

class _UpdateChecker(QThread):
    finished_check = Signal(bool, str, str)   # has_new, latest_version, download_url

    def run(self):
        try:
            req = urllib.request.Request(
                __api_latest_release__,
                headers={"User-Agent": "desktop_installer"},
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read().decode("utf-8"))
        except (URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
            self.finished_check.emit(False, "", f"network error: {e}")
            return

        tag = (data.get("tag_name") or "").lstrip("v")
        url = data.get("html_url") or __repo_url__ + "/releases/latest"
        has_new = self._is_newer(tag, __version__)
        self.finished_check.emit(has_new, tag, url)

    @staticmethod
    def _is_newer(latest: str, current: str) -> bool:
        def parse(v):
            return [int(x) for x in v.split(".") if x.isdigit()]
        try:
            return parse(latest) > parse(current)
        except Exception:
            return False


# ---------- 对话框 ----------

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("About"))
        self.setFixedWidth(460)
        self._update_thread: _UpdateChecker | None = None
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
        
        # 关键：使用 self.tr() 包裹，这样能在 .ts 里翻译
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

        form.addRow(self.tr("Built with:"), QLabel("PySide6 (LGPL v3)"))
        root.addLayout(form)

        # 按钮区
        btns = QHBoxLayout()
        copy_btn = QPushButton(self.tr("Copy version info"))
        copy_btn.clicked.connect(self._copy_version_info)
        btns.addWidget(copy_btn)

        self.check_btn = QPushButton(self.tr("Check for updates"))
        self.check_btn.clicked.connect(self._check_updates)
        btns.addWidget(self.check_btn)
        btns.addStretch()

        box = QDialogButtonBox(QDialogButtonBox.Close)
        box.rejected.connect(self.reject)
        box.accepted.connect(self.accept)
        btns.addWidget(box)
        root.addLayout(btns)

    def _copy_version_info(self) -> None:
        info = (
            f"{__app_display_name__} v{__version__}\n"
            f"Author: {__author__} ({__author_url__})\n"
            f"Source: {__repo_url__}\n"
            f"License: {__license__}\n"
            f"OS: {QGuiApplication.platformName()}\n"
        )
        QGuiApplication.clipboard().setText(info)

    def _check_updates(self) -> None:
        self.check_btn.setEnabled(False)
        self.check_btn.setText(self.tr("Checking…"))

        self._update_thread = _UpdateChecker(self)
        self._update_thread.finished_check.connect(self._on_check_done)
        self._update_thread.start()

    def _on_check_done(self, has_new: bool, latest: str, url: str) -> None:
        self.check_btn.setEnabled(True)
        self.check_btn.setText(self.tr("Check for updates"))

        if not latest:
            QMessageBox.warning(self, self.tr("Check for updates"),
                                self.tr("Could not check for updates:\n") + url)
            return

        if has_new:
            box = QMessageBox(self)
            box.setWindowTitle(self.tr("New version available"))
            box.setText(self.tr("A new version is available: v{ver}").format(ver=latest))
            open_btn = box.addButton(self.tr("Open download page"), QMessageBox.AcceptRole)
            box.addButton(self.tr("Later"), QMessageBox.RejectRole)
            box.exec()
            if box.clickedButton() is open_btn:
                from PySide6.QtGui import QDesktopServices
                from PySide6.QtCore import QUrl
                QDesktopServices.openUrl(QUrl(url))
        else:
            QMessageBox.information(self, self.tr("Check for updates"),
                                    self.tr("You are using the latest version."))