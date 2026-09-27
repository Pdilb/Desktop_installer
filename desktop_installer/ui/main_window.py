# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Pdilb
"""主窗口 UI。"""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..scanner import DesktopEntry, scan_deb, scan_snap
from ..installer import (
    ConflictAction,
    get_desktop_dir,
    install_many,
)
from .. import theme


# ---------- 表格列 ----------
COL_PACKAGE = 0
COL_PATH = 1
COL_TIME = 2
COL_CHECK = 3
COLUMN_TITLES = ["包名", "路径", "安装时间", "选择"]


class PackageTable(QWidget):
    """一个标签页内部的表格 + 排序下拉。"""

    def __init__(self, entries: list[DesktopEntry], parent=None):
        super().__init__(parent)
        self._entries = entries
        self._build_ui()
        self._populate()

    # ---------- UI ----------
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 排序下拉
        sort_row = QHBoxLayout()
        sort_row.addStretch()
        sort_label = QLabel("排序：")
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "包名 A → Z",
            "包名 Z → A",
            "安装时间 早 → 晚",
            "安装时间 晚 → 早",
        ])
        self.sort_combo.currentIndexChanged.connect(self._populate)
        sort_row.addWidget(sort_label)
        sort_row.addWidget(self.sort_combo)
        layout.addLayout(sort_row)

        # 表格
        self.table = QTableWidget(0, len(COLUMN_TITLES))
        self.table.setHorizontalHeaderLabels(COLUMN_TITLES)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setDefaultSectionSize(34)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(COL_PACKAGE, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_PATH, QHeaderView.Stretch)
        header.setSectionResizeMode(COL_TIME, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_CHECK, QHeaderView.Fixed)
        self.table.setColumnWidth(COL_CHECK, 60)

        self.table.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.table)

    # ---------- 数据填充 ----------
    def _sorted_entries(self) -> list[DesktopEntry]:
        idx = self.sort_combo.currentIndex()
        if idx == 0:
            return sorted(self._entries, key=lambda e: e.package.lower())
        if idx == 1:
            return sorted(self._entries, key=lambda e: e.package.lower(), reverse=True)
        if idx == 2:
            return sorted(self._entries, key=lambda e: e.install_time)
        return sorted(self._entries, key=lambda e: e.install_time, reverse=True)

    def _populate(self) -> None:
        # 重建时避免触发 itemChanged
        self.table.blockSignals(True)
        rows = self._sorted_entries()
        self.table.setRowCount(len(rows))

        for r, entry in enumerate(rows):
            # 包名
            name_item = QTableWidgetItem(entry.package)
            name_item.setData(Qt.UserRole, entry)
            self.table.setItem(r, COL_PACKAGE, name_item)

            # 路径（完整路径 + Tooltip，显示用省略号）
            path_item = QTableWidgetItem(entry.display_path)
            path_item.setToolTip(entry.display_path)
            self.table.setItem(r, COL_PATH, path_item)

            # 安装时间
            time_str = entry.install_time.strftime("%Y-%m-%d %H:%M")
            time_item = QTableWidgetItem(time_str)
            self.table.setItem(r, COL_TIME, time_item)

            # 勾选框
            cb = QCheckBox()
            cb.stateChanged.connect(self._on_check_changed)
            wrap = QWidget()
            wl = QHBoxLayout(wrap)
            wl.setContentsMargins(0, 0, 0, 0)
            wl.setAlignment(Qt.AlignCenter)
            wl.addWidget(cb)
            self.table.setCellWidget(r, COL_CHECK, wrap)

        self.table.blockSignals(False)
        self._on_check_changed()

    # ---------- 勾选状态 ----------
    def _iter_checkboxes(self):
        for r in range(self.table.rowCount()):
            wrap = self.table.cellWidget(r, COL_CHECK)
            if wrap:
                cb = wrap.findChild(QCheckBox)
                if cb:
                    yield r, cb

    def _on_item_changed(self, _item) -> None:
        self._on_check_changed()

    def _on_check_changed(self) -> None:
        # 通知父窗口刷新按钮状态
        win = self.window()
        if hasattr(win, "_refresh_add_button"):
            win._refresh_add_button()

    def selected_entries(self) -> list[DesktopEntry]:
        result = []
        for r, cb in self._iter_checkboxes():
            if cb.isChecked():
                item = self.table.item(r, COL_PACKAGE)
                if item:
                    result.append(item.data(Qt.UserRole))
        return result

    def set_all_checked(self, checked: bool) -> None:
        for _, cb in self._iter_checkboxes():
            cb.blockSignals(True)
            cb.setChecked(checked)
            cb.blockSignals(False)
        self._on_check_changed()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("desktop installer")
        self.resize(860, 600)

        theme.apply_theme(__import__("PySide6.QtWidgets", fromlist=["QApplication"]).QApplication.instance())

        self._build_ui()
        self._load_data()

    # ---------- UI ----------
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 标签页
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, stretch=1)

        # 底部按钮栏
        bottom = QWidget()
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(12, 8, 12, 12)

        self.status_label = QLabel("正在扫描…")
        bottom_layout.addWidget(self.status_label)
        bottom_layout.addStretch()

        self.add_btn = QPushButton("添加")
        self.add_btn.setObjectName("primary")
        self.add_btn.setEnabled(False)
        self.add_btn.clicked.connect(self._on_add_clicked)
        bottom_layout.addWidget(self.add_btn)

        root.addWidget(bottom)

        self.deb_table: PackageTable | None = None
        self.snap_table: PackageTable | None = None

    # ---------- 数据 ----------
    def _load_data(self) -> None:
        deb_entries = scan_deb()
        snap_entries = scan_snap()

        self.deb_table = PackageTable(deb_entries)
        self.snap_table = PackageTable(snap_entries)

        self.tabs.addTab(self.deb_table, f"deb包 ({len(deb_entries)})")
        self.tabs.addTab(self.snap_table, f"snap包 ({len(snap_entries)})")

        self.tabs.currentChanged.connect(lambda _: self._refresh_add_button())
        self.status_label.setText(
            f"deb: {len(deb_entries)} 个 · snap: {len(snap_entries)} 个"
        )
        self._refresh_add_button()

    # ---------- 状态刷新 ----------
    def _current_table(self) -> PackageTable | None:
        w = self.tabs.currentWidget()
        return w if isinstance(w, PackageTable) else None

    def _refresh_add_button(self) -> None:
        table = self._current_table()
        if table is None:
            self.add_btn.setEnabled(False)
            return
        self.add_btn.setEnabled(len(table.selected_entries()) > 0)

    # ---------- 添加 ----------
    def _on_add_clicked(self) -> None:
        table = self._current_table()
        if table is None:
            return
        entries = table.selected_entries()
        if not entries:
            return

        desktop_dir = get_desktop_dir()

        # 冲突处理的“应用到全部”记忆
        remember = {"action": None}

        def on_conflict(source, existing):
            if remember["action"]:
                return remember["action"]
            box = QMessageBox(self)
            box.setWindowTitle("文件已存在")
            box.setIcon(QMessageBox.Question)
            box.setText(f"桌面上已存在：\n{existing.name}")
            box.setInformativeText("请选择处理方式：")
            overwrite = box.addButton("覆盖", QMessageBox.AcceptRole)
            rename = box.addButton("重命名", QMessageBox.ActionRole)
            skip = box.addButton("跳过", QMessageBox.RejectRole)
            apply_all = QCheckBox("应用到全部")
            box.setCheckBox(apply_all)
            box.exec()

            clicked = box.clickedButton()
            if clicked is overwrite:
                action = ConflictAction.OVERWRITE
            elif clicked is rename:
                action = ConflictAction.RENAME
            else:
                action = ConflictAction.SKIP

            if apply_all.isChecked():
                remember["action"] = action
            return action

        results = install_many(entries, desktop_dir, on_conflict)

        ok = sum(1 for r in results if r.status == "installed")
        skipped = sum(1 for r in results if r.status == "skipped")
        errors = [r for r in results if r.status == "error"]

        msg = f"已添加 {ok} 个到桌面。"
        if skipped:
            msg += f"\n跳过 {skipped} 个。"
        if errors:
            msg += f"\n失败 {len(errors)} 个：\n" + "\n".join(
                f"  {e.source.name}: {e.message}" for e in errors
            )
        QMessageBox.information(self, "完成", msg)

        # 清空勾选
        table.set_all_checked(False)
        self._refresh_add_button()