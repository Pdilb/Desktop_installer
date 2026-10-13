# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Pdilb
"""主窗口 UI：标签页 + 表格 + 排序下拉 + 状态列 + 关于入口。"""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
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

from ..scanner import DesktopEntry, scan_deb, scan_snap, get_desktop_dir
from ..installer import (
    ConflictAction,
    install_many,
)
from ..about_dialog import AboutDialog
from .. import __app_display_name__, __version__
from .. import theme


# ---------- 表格列 ----------
COL_PACKAGE = 0
COL_PATH = 1
COL_TIME = 2
COL_STATUS = 3
COL_CHECK = 4


class PackageTable(QWidget):
    """一个标签页内部的表格 + 排序下拉。"""

    def __init__(self, entries: list[DesktopEntry], source: str, parent=None):
        super().__init__(parent)
        self._entries = entries
        self._source = source
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
        self.sort_label = QLabel(self.tr("Sort:"))
        self.sort_combo = QComboBox()
        self._refresh_sort_options()
        self.sort_combo.currentIndexChanged.connect(self._populate)
        sort_row.addWidget(self.sort_label)
        sort_row.addWidget(self.sort_combo)
        layout.addLayout(sort_row)

        # 表格
        column_titles = [
            self.tr("Package"),
            self.tr("Path"),
            self.tr("Installed"),
            self.tr("Status"),
            self.tr("Select"),
        ]
        self.table = QTableWidget(0, len(column_titles))
        self.table.setHorizontalHeaderLabels(column_titles)
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
        header.setSectionResizeMode(COL_STATUS, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_CHECK, QHeaderView.Fixed)
        self.table.setColumnWidth(COL_CHECK, 60)

        self.table.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.table)

    def _refresh_sort_options(self) -> None:
        """重建排序选项（语言切换时也会重调）。"""
        current = self.sort_combo.currentIndex() if self.sort_combo.count() else 0
        self.sort_combo.blockSignals(True)
        self.sort_combo.clear()
        self.sort_combo.addItems([
            self.tr("Name A → Z"),
            self.tr("Name Z → A"),
            self.tr("Installed  old → new"),
            self.tr("Installed  new → old"),
        ])
        self.sort_combo.setCurrentIndex(max(0, current))
        self.sort_combo.blockSignals(False)

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
        self.table.blockSignals(True)
        rows = self._sorted_entries()
        self.table.setRowCount(len(rows))

        for r, entry in enumerate(rows):
            # 包名
            name_item = QTableWidgetItem(entry.package)
            name_item.setData(Qt.UserRole, entry)
            self.table.setItem(r, COL_PACKAGE, name_item)

            # 路径
            path_item = QTableWidgetItem(entry.display_path)
            path_item.setToolTip(entry.display_path)
            self.table.setItem(r, COL_PATH, path_item)

            # 安装时间
            time_str = entry.install_time.strftime("%Y-%m-%d %H:%M")
            time_item = QTableWidgetItem(time_str)
            self.table.setItem(r, COL_TIME, time_item)

            # 状态
            status_item = QTableWidgetItem(self._status_text(entry))
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, COL_STATUS, status_item)

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

    def _status_text(self, entry: DesktopEntry) -> str:
        if entry.already_added:
            return self.tr("✅ Added")
        return self.tr("➕ Not added")

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

    # ---------- 刷新状态列 ----------
    def refresh_status(self) -> None:
        """重新检查桌面，刷新「已添加」状态列。"""
        desktop_dir = get_desktop_dir()
        for r in range(self.table.rowCount()):
            item = self.table.item(r, COL_PACKAGE)
            if not item:
                continue
            entry: DesktopEntry = item.data(Qt.UserRole)
            if entry is None:
                continue
            entry.already_added = self._check_added(entry.path, desktop_dir)

            status_item = self.table.item(r, COL_STATUS)
            if status_item:
                status_item.setText(self._status_text(entry))

    @staticmethod
    def _check_added(desktop_file, desktop_dir) -> bool:
        from pathlib import Path
        desktop_dir = Path(desktop_dir)
        if not desktop_dir.is_dir():
            return False
        name = desktop_file.name
        if (desktop_dir / name).exists():
            return True
        stem, suffix = desktop_file.stem, desktop_file.suffix
        for i in range(1, 20):
            if (desktop_dir / f"{stem}({i}){suffix}").exists():
                return True
        return False

    # ---------- 语言切换 ----------
    def retranslate(self) -> None:
        """重新设置所有静态字符串（语言切换时调用）。"""
        self.sort_label.setText(self.tr("Sort:"))
        self._refresh_sort_options()
        self.table.setHorizontalHeaderLabels([
            self.tr("Package"),
            self.tr("Path"),
            self.tr("Installed"),
            self.tr("Status"),
            self.tr("Select"),
        ])
        self._populate()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(__app_display_name__)
        self.resize(920, 620)

        self._build_ui()
        self._build_menu()
        self._load_data()

        # 监听深浅色切换，实时应用主题
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is not None:
            theme.watch_color_scheme(app, callback=self._on_theme_changed)

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

        self.status_label = QLabel("")
        bottom_layout.addWidget(self.status_label)
        bottom_layout.addStretch()

        self.add_btn = QPushButton(self.tr("Add"))
        self.add_btn.setObjectName("primary")
        self.add_btn.setEnabled(False)
        self.add_btn.clicked.connect(self._on_add_clicked)
        bottom_layout.addWidget(self.add_btn)

        root.addWidget(bottom)

        self.deb_table: PackageTable | None = None
        self.snap_table: PackageTable | None = None

    def _build_menu(self) -> None:
        """菜单栏：About 入口。"""
        menubar = self.menuBar()

        # Help 菜单
        help_menu = menubar.addMenu(self.tr("Help"))

        about_action = QAction(self.tr("About"), self)
        about_action.setShortcut(QKeySequence("F1"))
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    # ---------- 数据 ----------
    def _load_data(self) -> None:
        desktop_dir = get_desktop_dir()
        deb_entries = scan_deb(desktop_dir)
        snap_entries = scan_snap(desktop_dir)

        self.deb_table = PackageTable(deb_entries, source="deb")
        self.snap_table = PackageTable(snap_entries, source="snap")

        self.tabs.addTab(self.deb_table, self.tr("deb packages ({n})").format(n=len(deb_entries)))
        self.tabs.addTab(self.snap_table, self.tr("snap packages ({n})").format(n=len(snap_entries)))

        self.tabs.currentChanged.connect(lambda _: self._refresh_add_button())
        self.status_label.setText(
            self.tr("deb: {d} · snap: {s}").format(d=len(deb_entries), s=len(snap_entries))
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

    # ---------- 主题切换回调 ----------
    def _on_theme_changed(self) -> None:
        """系统深浅色切换时刷新表格颜色。"""
        for table in (self.deb_table, self.snap_table):
            if table is not None:
                table.refresh_status()

    # ---------- 关于 ----------
    def _show_about(self) -> None:
        dlg = AboutDialog(self)
        dlg.exec()

    # ---------- 添加 ----------
    def _on_add_clicked(self) -> None:
        table = self._current_table()
        if table is None:
            return
        entries = table.selected_entries()
        if not entries:
            return

        desktop_dir = get_desktop_dir()
        remember = {"action": None}

        def on_conflict(source, existing):
            if remember["action"]:
                return remember["action"]
            box = QMessageBox(self)
            box.setWindowTitle(self.tr("File exists"))
            box.setIcon(QMessageBox.Question)
            box.setText(self.tr("Already exists on desktop:\n{name}").format(name=existing.name))
            box.setInformativeText(self.tr("How do you want to handle it?"))
            overwrite = box.addButton(self.tr("Overwrite"), QMessageBox.AcceptRole)
            rename = box.addButton(self.tr("Rename"), QMessageBox.ActionRole)
            skip = box.addButton(self.tr("Skip"), QMessageBox.RejectRole)
            apply_all = QCheckBox(self.tr("Apply to all"))
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

        msg = self.tr("Added {n} to desktop.").format(n=ok)
        if skipped:
            msg += "\n" + self.tr("Skipped {n}.").format(n=skipped)
        if errors:
            msg += "\n" + self.tr("Failed {n}:").format(n=len(errors)) + "\n" + "\n".join(
                f"  {e.source.name}: {e.message}" for e in errors
            )
        QMessageBox.information(self, self.tr("Done"), msg)

        table.set_all_checked(False)
        table.refresh_status()
        self._refresh_add_button()

    # ---------- 语言切换（可选，供未来扩展） ----------
    def changeEvent(self, event):
        """语言切换时会触发 LanguageChange 事件，刷新字符串。"""
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.LanguageChange:
            self.retranslate()
        super().changeEvent(event)

    def retranslate(self) -> None:
        self.setWindowTitle(__app_display_name__)
        self.add_btn.setText(self.tr("Add"))
        if self.deb_table:
            self.deb_table.retranslate()
        if self.snap_table:
            self.snap_table.retranslate()
