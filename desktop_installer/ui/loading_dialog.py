# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Pdilb
"""扫描时的居中加载对话框：确定进度条 + 实时文字。"""
from __future__ import annotations

from PySide6.QtCore import Qt, QLocale
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QProgressBar,
    QVBoxLayout,
)


class LoadingDialog(QDialog):
    """居中显示，带确定进度条的加载对话框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_zh = QLocale.system().name().startswith("zh")
        
        self.setWindowTitle("请稍候" if self._is_zh else "Please wait")
        self.setModal(True)
        self.setFixedSize(400, 150)
        self.setWindowFlags(
            Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint
        )
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(12)

        self.label = QLabel("准备中…" if self._is_zh else "Preparing…")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 13px;")
        root.addWidget(self.label)

        # 确定进度条
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%")
        self.progress.setFixedHeight(18)
        root.addWidget(self.progress)

        self.hint = QLabel("正在扫描已安装的软件包…" if self._is_zh else "Scanning installed packages…")
        self.hint.setAlignment(Qt.AlignCenter)
        self.hint.setStyleSheet("color: #888; font-size: 11px;")
        self.hint.setWordWrap(True)
        root.addWidget(self.hint)

    # ---------- 对外接口 ----------

    def set_stage(self, stage: str) -> None:
        if self._is_zh:
            self.hint.setText(f"正在扫描 {stage} 包…")
        else:
            self.hint.setText(f"Scanning {stage} packages…")

    def set_progress(self, current: int, total: int, name: str = "") -> None:
        if total <= 0:
            self.progress.setRange(0, 0)
            self.label.setText(name or ("扫描中…" if self._is_zh else "Scanning…"))
            return

        self.progress.setRange(0, total)
        self.progress.setValue(current)
        if name:
            self.label.setText(f"{name}  ({current}/{total})")
        else:
            self.label.setText(f"{current} / {total}")