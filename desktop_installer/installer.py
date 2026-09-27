# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Pdilb
"""将 .desktop 文件安装到用户桌面。"""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QStandardPaths


class ConflictAction:
    OVERWRITE = "overwrite"
    SKIP = "skip"
    RENAME = "rename"
    APPLY_ALL = "apply_all"   # 内部标记：记住这个选择


@dataclass
class InstallResult:
    package: str
    source: Path
    target: Path | None
    status: str   # "installed" / "skipped" / "error"
    message: str = ""


def get_desktop_dir() -> Path:
    """获取当前用户的桌面目录（自动兼容中文“桌面”）。"""
    loc = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
    if not loc:
        loc = str(Path.home() / "Desktop")
    path = Path(loc)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _mark_trusted(desktop_file: Path) -> None:
    """GNOME 下标记 .desktop 为可信任，否则双击会弹“不受信任”。"""
    try:
        subprocess.run(
            ["gio", "set", str(desktop_file), "metadata::trusted", "true"],
            capture_output=True, check=False,
        )
    except FileNotFoundError:
        pass


def _unique_target(base: Path) -> Path:
    """若存在，生成 name(1).desktop / name(2).desktop ..."""
    stem, suffix = base.stem, base.suffix
    i = 1
    while True:
        candidate = base.with_name(f"{stem}({i}){suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def install_one(
    source: Path,
    desktop_dir: Path,
    on_conflict,
) -> InstallResult:
    """
    安装单个 .desktop。

    on_conflict: 回调 (source, existing_target) -> ConflictAction
                 返回 "overwrite" / "skip" / "rename"
    """
    target = desktop_dir / source.name

    # 处理冲突
    if target.exists():
        action = on_conflict(source, target)
        if action == ConflictAction.SKIP:
            return InstallResult("", source, None, "skipped", "已跳过")
        if action == ConflictAction.RENAME:
            target = _unique_target(target)
        # OVERWRITE 则继续

    try:
        shutil.copy2(source, target)
        # 加执行权限
        os.chmod(
            target,
            os.stat(target).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
        )
        # GNOME 标记 trusted
        _mark_trusted(target)
    except OSError as e:
        return InstallResult("", source, None, "error", str(e))

    return InstallResult("", source, target, "installed")


def install_many(
    entries,
    desktop_dir: Path,
    on_conflict,
    on_progress=None,
) -> list[InstallResult]:
    """批量安装。entries 为 scanner.DesktopEntry 列表。"""
    results: list[InstallResult] = []
    total = len(entries)
    for i, entry in enumerate(entries, 1):
        res = install_one(entry.path, desktop_dir, on_conflict)
        res.package = entry.package
        results.append(res)
        if on_progress:
            on_progress(i, total, entry)
    return results