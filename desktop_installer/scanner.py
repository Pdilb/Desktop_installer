# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Pdilb
"""扫描已安装的 deb / snap 包，收集其 .desktop 文件信息。"""
from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


# ---------- 数据结构 ----------

@dataclass
class DesktopEntry:
    """一个可添加到桌面的 .desktop 条目。"""
    package: str          # 包名
    path: Path            # .desktop 完整路径
    install_time: datetime  # 安装时间
    source: str           # "deb" 或 "snap"

    @property
    def display_path(self) -> str:
        return str(self.path)


# ---------- 公共工具 ----------

def _read_desktop_name(desktop_file: Path) -> str | None:
    """尝试从 .desktop 读取 Name，用于兜底展示。"""
    try:
        text = desktop_file.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    m = re.search(r"^Name=(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else None


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
    # 输出形如：sogo: /usr/share/applications/sogo.desktop
    first = out.stdout.splitlines()[0] if out.stdout else ""
    if ":" in first:
        return first.split(":", 1)[0].strip()
    return None


def _deb_install_time(package: str) -> datetime:
    """通过 /var/lib/dpkg/info/<pkg>.list 的 mtime 近似安装时间。"""
    list_file = Path("/var/lib/dpkg/info") / f"{package}.list"
    if list_file.exists():
        return _safe_mtime(list_file)
    return datetime.fromtimestamp(0)


def scan_deb() -> list[DesktopEntry]:
    """扫描系统里所有 deb 包的 .desktop 文件。"""
    entries: list[DesktopEntry] = []
    seen: set[Path] = set()

    for app_dir in DEB_APPLICATION_DIRS:
        if not app_dir.is_dir():
            continue
        for desktop_file in sorted(app_dir.glob("*.desktop")):
            if desktop_file in seen:
                continue
            seen.add(desktop_file)

            owner = _deb_owner(desktop_file)
            if not owner:
                # 无归属包（例如手动放的），跳过
                continue

            entries.append(DesktopEntry(
                package=owner,
                path=desktop_file,
                install_time=_deb_install_time(owner),
                source="deb",
            ))
    return entries


# ---------- snap 扫描 ----------

SNAP_APPLICATION_DIRS = [
    Path("/var/lib/snapd/desktop/applications"),
]

SNAP_STATE_FILE = Path("/var/lib/snapd/state.json")


def _load_snap_install_times() -> dict[str, datetime]:
    """从 snapd state.json 读取每个 snap 的安装时间。"""
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
        # 格式类似 2025-07-06T10:00:00Z
        try:
            cleaned = install_date.replace("Z", "+00:00")
            times[name] = datetime.fromisoformat(cleaned).astimezone()
        except ValueError:
            continue
    return times


def _snap_from_desktop_name(desktop_file: Path) -> str | None:
    """snap 的 desktop 文件命名通常是 <snap>_<app>.desktop 或 <snap>.desktop。"""
    stem = desktop_file.stem
    if "_" in stem:
        return stem.split("_", 1)[0]
    return stem


def scan_snap() -> list[DesktopEntry]:
    """扫描系统里所有 snap 包的 .desktop 文件。"""
    entries: list[DesktopEntry] = []
    install_times = _load_snap_install_times()

    for app_dir in SNAP_APPLICATION_DIRS:
        if not app_dir.is_dir():
            continue
        for desktop_file in sorted(app_dir.glob("*.desktop")):
            pkg = _snap_from_desktop_name(desktop_file)
            if not pkg:
                continue
            install_time = install_times.get(pkg) or _safe_mtime(desktop_file)
            entries.append(DesktopEntry(
                package=pkg,
                path=desktop_file,
                install_time=install_time,
                source="snap",
            ))
    return entries


# ---------- 聚合 ----------

def scan_all() -> tuple[list[DesktopEntry], list[DesktopEntry]]:
    """返回 (deb_entries, snap_entries)。"""
    return scan_deb(), scan_snap()