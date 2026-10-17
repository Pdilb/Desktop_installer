# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Pdilb
"""主窗口 UI：标签页 + 搜索 + 排序 + 状态列 + 添加/移除 + 异步扫描。"""
from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal, QEvent
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QApplication,
)

from ..scanner import DesktopEntry, scan_deb, scan_snap, get_desktop_dir
from ..installer import (
    ConflictAction,
    install_many,
    remove_many,
)
from ..about_dialog import AboutDialog
from .. import __app_display_name__
from .. import theme
from .loading_dialog import LoadingDialog


# ---------- 表格列 ----------
COL_PACKAGE = 0
COL_PATH = 1
COL_TIME = 2
COL_STATUS = 3
COL_CHECK = 4


# ---------- 后台扫描线程 ----------

class _ScanWorker(QThread):
    """后台扫描 deb / snap 包，并实时发送进度。"""
    finished_scan = Signal(list, list)
    progress = Signal(str, int, int, str)   # stage, current, total, name
    stage_changed = Signal(str)             # stage

    def __init__(self, desktop_dir, parent=None):
        super().__init__(parent)
        self._desktop_dir = desktop_dir

    def run(self):
        try:
            # ---- deb ----
            self.stage_changed.emit("deb")
            deb_entries = scan_deb(
                self._desktop_dir,
                on_progress=lambda c, t, n: self.progress.emit("deb", c, t, n),
            )

            # ---- snap ----
            self.stage_changed.emit("snap")
            snap_entries = scan_snap(
                self._desktop_dir,
                on_progress=lambda c, t, n: self.progress.emit("snap", c, t, n),
            )

            self.finished_scan.emit(deb_entries, snap_entries)
        except Exception:
            self.finished_scan.emit([], [])


# ---------- 表格组件 ----------

class PackageTable(QWidget):
    """一个标签页内部的表格 + 搜索 + 排序下拉。"""

    def __init__(self, source: str, parent=None):
        super().__init__(parent)
        self._entries: list[DesktopEntry] = []
        self._source = source
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.search_label = QLabel(self.tr("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(self.tr("Filter by name or path"))
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._populate)
        top_row.addWidget(self.search_label)
        top_row.addWidget(self.search_edit, stretch=1)

        self.sort_label = QLabel(self.tr("Sort:"))
        self.sort_combo = QComboBox()
        self._refresh_sort_options()
        self.sort_combo.currentIndexChanged.connect(self._populate)
        top_row.addWidget(self.sort_label)
        top_row.addWidget(self.sort_combo)

        layout.addLayout(top_row)

        self.table = QTableWidget(0, 5)
        self._refresh_headers()
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

    def _refresh_headers(self) -> None:
        self.table.setHorizontalHeaderLabels([
            self.tr("Package"),
            self.tr("Path"),
            self.tr("Installed"),
            self.tr("Status"),
            self.tr("Select"),
        ])

    def _refresh_sort_options(self) -> None:
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

    def set_entries(self, entries: list[DesktopEntry]) -> None:
        self._entries = entries
        self._populate()

    def _filtered_sorted(self) -> list[DesktopEntry]:
        q = self.search_edit.text().strip().lower()
        rows = self._entries
        if q:
            rows = [
                e for e in rows
                if q in e.package.lower() or q in str(e.path).lower()
            ]

        idx = self.sort_combo.currentIndex()
        if idx == 0:
            return sorted(rows, key=lambda e: e.package.lower())
        if idx == 1:
            return sorted(rows, key=lambda e: e.package.lower(), reverse=True)
        if idx == 2:
            return sorted(rows, key=lambda e: e.install_time)
        return sorted(rows, key=lambda e: e.install_time, reverse=True)

    def _populate(self) -> None:
        self.table.blockSignals(True)
        rows = self._filtered_sorted()
        self.table.setRowCount(len(rows))

        for r, entry in enumerate(rows):
            name_item = QTableWidgetItem(entry.package)
            name_item.setData(Qt.UserRole, entry)
            self.table.setItem(r, COL_PACKAGE, name_item)

            path_item = QTableWidgetItem(entry.display_path)
            path_item.setToolTip(entry.display_path)
            self.table.setItem(r, COL_PATH, path_item)

            time_str = entry.install_time.strftime("%Y-%m-%d %H:%M")
            self.table.setItem(r, COL_TIME, QTableWidgetItem(time_str))

            status_item = QTableWidgetItem(self._status_text(entry))
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, COL_STATUS, status_item)

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
        return self.tr("✅ Added") if entry.already_added else self.tr("➕ Not added")

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
        if hasattr(win, "_refresh_buttons"):
            win._refresh_buttons()

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

    def refresh_status(self) -> None:
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

    def retranslate(self) -> None:
        self.search_label.setText(self.tr("Search:"))
        self.search_edit.setPlaceholderText(self.tr("Filter by name or path"))
        self.sort_label.setText(self.tr("Sort:"))
        self._refresh_sort_options()
        self._refresh_headers()
        self._populate()


# ---------- 主窗口 ----------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(__app_display_name__)
        self.resize(960, 640)

        self._loading: LoadingDialog | None = None

        self._build_ui()
        self._build_menu()
        self._start_scan()

        app = QApplication.instance()
        if app is not None:
            theme.watch_color_scheme(app, callback=self._on_theme_changed)

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, stretch=1)

        bottom = QWidget()
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(12, 8, 12, 12)

        self.status_label = QLabel(self.tr("Scanning…"))
        bottom_layout.addWidget(self.status_label)
        bottom_layout.addStretch()

        self.remove_btn = QPushButton(self.tr("Remove selected"))
        self.remove_btn.setEnabled(False)
        self.remove_btn.clicked.connect(self._on_remove_clicked)
        bottom_layout.addWidget(self.remove_btn)

        self.add_btn = QPushButton(self.tr("Add"))
        self.add_btn.setObjectName("primary")
        self.add_btn.setEnabled(False)
        self.add_btn.clicked.connect(self._on_add_clicked)
        bottom_layout.addWidget(self.add_btn)

        root.addWidget(bottom)

        self.deb_table: PackageTable | None = None
        self.snap_table: PackageTable | None = None

    def _build_menu(self) -> None:
        menubar = self.menuBar()
        help_menu = menubar.addMenu(self.tr("Help"))
        about_action = QAction(self.tr("About"), self)
        about_action.setShortcut(QKeySequence("F1"))
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    # ---------- 扫描 ----------
    def _start_scan(self) -> None:
        desktop_dir = get_desktop_dir()
        self._scan_worker = _ScanWorker(desktop_dir, self)
        self._scan_worker.finished_scan.connect(self._on_scan_finished)
        self._scan_worker.progress.connect(self._on_scan_progress)
        self._scan_worker.stage_changed.connect(self._on_stage_changed)
        self._scan_worker.start()

        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._show_loading)

    def _show_loading(self) -> None:
        self._loading = LoadingDialog(self)
        self._loading.show()
        self._center_loading()

    def _center_loading(self) -> None:
        if self._loading is None:
            return
        parent_geo = self.geometry()
        dlg_geo = self._loading.frameGeometry()
        dlg_geo.moveCenter(parent_geo.center())
        self._loading.move(dlg_geo.topLeft())

    def _on_stage_changed(self, stage: str) -> None:
        if self._loading is not None:
            self._loading.set_stage(stage)

    def _on_scan_progress(self, stage: str, current: int, total: int, name: str) -> None:
        if self._loading is not None:
            self._loading.set_progress(current, total, name)

    def _on_scan_finished(self, deb_entries, snap_entries) -> None:
        self.deb_table = PackageTable(source="deb")
        self.snap_table = PackageTable(source="snap")

        self.deb_table.set_entries(deb_entries)
        self.snap_table.set_entries(snap_entries)

        for table in (self.deb_table, self.snap_table):
            for _, cb in table._iter_checkboxes():
                cb.stateChanged.connect(self._refresh_buttons)

        self.tabs.addTab(self.deb_table, self.tr("deb packages ({n})").format(n=len(deb_entries)))
        self.tabs.addTab(self.snap_table, self.tr("snap packages ({n})").format(n=len(snap_entries)))
        self.tabs.currentChanged.connect(lambda _: self._refresh_buttons())

        self.status_label.setText(
            self.tr("deb: {d} · snap: {s}").format(d=len(deb_entries), s=len(snap_entries))
        )
        self._refresh_buttons()

        if self._loading is not None:
            self._loading.accept()
            self._loading = None

    # ---------- 状态刷新 ----------
    def _current_table(self) -> PackageTable | None:
        w = self.tabs.currentWidget()
        return w if isinstance(w, PackageTable) else None

    def _refresh_buttons(self) -> None:
        table = self._current_table()
        if table is None:
            self.add_btn.setEnabled(False)
            self.remove_btn.setEnabled(False)
            return

        selected = table.selected_entries()
        has_added = any(e.already_added for e in selected)
        has_not_added = any(not e.already_added for e in selected)

        self.add_btn.setEnabled(has_not_added)
        self.remove_btn.setEnabled(has_added)

    def _on_theme_changed(self) -> None:
        for table in (self.deb_table, self.snap_table):
            if table is not None:
                table.refresh_status()

    def _show_about(self) -> None:
        dlg = AboutDialog(self)
        dlg.exec()

    # ---------- 添加 ----------
    def _on_add_clicked(self) -> None:
        table = self._current_table()
        if table is None:
            return
        entries = [e for e in table.selected_entries() if not e.already_added]
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
        self._refresh_buttons()

    # ---------- 移除 ----------
    def _on_remove_clicked(self) -> None:
        table = self._current_table()
        if table is None:
            return
        entries = [e for e in table.selected_entries() if e.already_added]
        if not entries:
            QMessageBox.information(self, self.tr("Done"), self.tr("Nothing to remove."))
            return

        confirm = QMessageBox.question(
            self,
            self.tr("Remove selected"),
            self.tr("Remove {n} shortcut(s) from the desktop?").format(n=len(entries)),
        )
        if confirm != QMessageBox.Yes:
            return

        desktop_dir = get_desktop_dir()
        results = remove_many(entries, desktop_dir)

        removed = sum(1 for r in results if r.status == "removed")
        not_found = sum(1 for r in results if r.status == "not_found")
        errors = [r for r in results if r.status == "error"]

        msg = self.tr("Removed {n} from desktop.").format(n=removed)
        if not_found:
            msg += "\n" + self.tr("Skipped {n}.").format(n=not_found)
        if errors:
            msg += "\n" + self.tr("Failed {n}:").format(n=len(errors)) + "\n" + "\n".join(
                f"  {e.package}: {e.message}" for e in errors
            )
        QMessageBox.information(self, self.tr("Done"), msg)

        table.set_all_checked(False)
        table.refresh_status()
        self._refresh_buttons()

    # ---------- 语言切换 ----------
    def changeEvent(self, event):
        if event.type() == QEvent.LanguageChange:
            self.retranslate()
        super().changeEvent(event)

    def retranslate(self) -> None:
        self.setWindowTitle(__app_display_name__)
        self.add_btn.setText(self.tr("Add"))
        self.remove_btn.setText(self.tr("Remove selected"))
        for t in (self.deb_table, self.snap_table):
            if t is not None:
                t.retranslate()