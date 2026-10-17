# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Pdilb
"""扫描已安装的 deb / snap 包，收集其 .desktop 文件信息。"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QStandardPaths


# ---------- 数据结构 ----------

@dataclass
class DesktopEntry:
    """一个可添加到桌面的 .desktop 条目。"""
    package: str
    path: Path
    install_time: datetime
    source: str
    already_added: bool = False

    @property
    def display_path(self) -> str:
        return str(self.path)


# ---------- 桌面目录 ----------

def get_desktop_dir() -> Path:
    """获取当前用户的桌面目录（自动兼容中文“桌面”）。"""
    loc = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
    if not loc:
        loc = str(Path.home() / "Desktop")
    return Path(loc)


def _is_already_added(desktop_file: Path, desktop_dir: Path | None = None) -> bool:
    """检查桌面上是否已存在同名或同名重命名版本。"""
    if desktop_dir is None:
        desktop_dir = get_desktop_dir()
    if not desktop_dir.is_dir():
        return False

    name = desktop_file.name
    if (desktop_dir / name).exists():
        return True

    stem = desktop_file.stem
    suffix = desktop_file.suffix
    for i in range(1, 20):
        if (desktop_dir / f"{stem}({i}){suffix}").exists():
            return True
    return False


def _safe_mtime(path: Path) -> datetime:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return datetime.fromtimestamp(0)


# ---------- deb 扫描 ----------

DEB_APPLICATION_DIRS = [
    Path("/usr/share/applications"),
    Path("/usr/local/share/applications"),
]


def _deb_owner(desktop_file: Path) -> str | None:
    """用 dpkg -S 查询某个 .desktop 属于哪个包。"""
    try:
        out = subprocess.run(
            ["dpkg", "-S", str(desktop_file)],
            capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        return None
    if out.returncode != 0:
        return None
    first = out.stdout.splitlines()[0] if out.stdout else ""
    if ":" in first:
        return first.split(":", 1)[0].strip()
    return None


def _deb_install_time(package: str) -> datetime:
    list_file = Path("/var/lib/dpkg/info") / f"{package}.list"
    if list_file.exists():
        return _safe_mtime(list_file)
    return datetime.fromtimestamp(0)


def scan_deb(desktop_dir: Path | None = None, on_progress=None) -> list[DesktopEntry]:
    """扫描系统里所有 deb 包的 .desktop 文件。"""
    all_files: list[Path] = []
    seen: set[Path] = set()

    for app_dir in DEB_APPLICATION_DIRS:
        if not app_dir.is_dir():
            continue
        for f in sorted(app_dir.glob("*.desktop")):
            if f in seen:
                continue
            seen.add(f)
            all_files.append(f)

    total = len(all_files)
    entries: list[DesktopEntry] = []

    for i, desktop_file in enumerate(all_files, 1):
        owner = _deb_owner(desktop_file)
        if owner:
            entries.append(DesktopEntry(
                package=owner,
                path=desktop_file,
                install_time=_deb_install_time(owner),
                source="deb",
                already_added=_is_already_added(desktop_file, desktop_dir),
            ))
        
        if on_progress:
            on_progress(i, total, desktop_file.name)

    return entries


# ---------- snap 扫描 ----------

SNAP_APPLICATION_DIRS = [
    Path("/var/lib/snapd/desktop/applications"),
]
SNAP_STATE_FILE = Path("/var/lib/snapd/state.json")


def _load_snap_install_times() -> dict[str, datetime]:
    times: dict[str, datetime] = {}
    if not SNAP_STATE_FILE.exists():
        return times
    try:
        data = json.loads(SNAP_STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return times

    snaps = data.get("data", {}).get("snaps", {})
    for name, info in snaps.items():
        install_date = info.get("install-date")
        if not install_date:
            continue
        try:
            cleaned = install_date.replace("Z", "+00:00")
            times[name] = datetime.fromisoformat(cleaned).astimezone()
        except ValueError:
            continue
    return times


def _snap_from_desktop_name(desktop_file: Path) -> str | None:
    stem = desktop_file.stem
    if "_" in stem:
        return stem.split("_", 1)[0]
    return stem


def scan_snap(desktop_dir: Path | None = None, on_progress=None) -> list[DesktopEntry]:
    """扫描系统里所有 snap 包的 .desktop 文件。"""
    all_files: list[Path] = []
    for app_dir in SNAP_APPLICATION_DIRS:
        if not app_dir.is_dir():
            continue
        for f in sorted(app_dir.glob("*.desktop")):
            all_files.append(f)

    total = len(all_files)
    entries: list[DesktopEntry] = []
    install_times = _load_snap_install_times()

    for i, desktop_file in enumerate(all_files, 1):
        pkg = _snap_from_desktop_name(desktop_file)
        if pkg:
            install_time = install_times.get(pkg) or _safe_mtime(desktop_file)
            entries.append(DesktopEntry(
                package=pkg,
                path=desktop_file,
                install_time=install_time,
                source="snap",
                already_added=_is_already_added(desktop_file, desktop_dir),
            ))
        
        if on_progress:
            on_progress(i, total, desktop_file.name)

    return entries


# ---------- 聚合 ----------

def scan_all(desktop_dir: Path | None = None) -> tuple[list[DesktopEntry], list[DesktopEntry]]:
    return scan_deb(desktop_dir), scan_snap(desktop_dir)