# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Pdilb
"""交互式命令行模式：desktop_installer --nogui。"""
from __future__ import annotations

import shlex
import sys
from pathlib import Path

from .scanner import DesktopEntry, scan_deb, scan_snap, get_desktop_dir
from .installer import (
    ConflictAction,
    install_one,
    remove_one,
)


# ---------- 彩色输出（仅 TTY 时启用） ----------

_USE_COLOR = sys.stdout.isatty()


def _c(text: str, code: str) -> str:
    if not _USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def _green(s: str) -> str:
    return _c(s, "32")


def _yellow(s: str) -> str:
    return _c(s, "33")


def _red(s: str) -> str:
    return _c(s, "31")


def _cyan(s: str) -> str:
    return _c(s, "36")


def _bold(s: str) -> str:
    return _c(s, "1")


# ---------- 数据缓存 ----------

class _Cache:
    """缓存扫描结果，避免每次命令都重新扫描。"""
    def __init__(self):
        self.deb_entries: list[DesktopEntry] = []
        self.snap_entries: list[DesktopEntry] = []
        self.by_name: dict[str, DesktopEntry] = {}
        self._loaded = False

    def load(self, force: bool = False) -> None:
        if self._loaded and not force:
            return
        desktop_dir = get_desktop_dir()
        self.deb_entries = scan_deb(desktop_dir)
        self.snap_entries = scan_snap(desktop_dir)
        self.by_name = {
            e.package: e for e in self.deb_entries + self.snap_entries
        }
        self._loaded = True

    def refresh_status(self) -> None:
        """只刷新 already_added，不重新扫描。"""
        desktop_dir = get_desktop_dir()
        for e in self.deb_entries + self.snap_entries:
            e.already_added = _check_added(e.path, desktop_dir)


def _check_added(desktop_file: Path, desktop_dir: Path) -> bool:
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


# ---------- 输出辅助 ----------

def _print_table(entries: list[DesktopEntry]) -> None:
    """以表格形式打印条目。"""
    if not entries:
        print(_yellow("  (no packages)"))
        return

    # 计算列宽
    pkg_w = max(8, max(len(e.package) for e in entries))
    path_w = max(8, min(60, max(len(e.display_path) for e in entries)))
    status_w = 9   # "✅ Added" 或 "➕ Not added"

    header = (
        f"  {'PKG':<{pkg_w}}  {'PATH':<{path_w}}  "
        f"{'INSTALLED':<16}  {'STATUS':<{status_w}}"
    )
    print(_bold(header))
    print(_bold("  " + "-" * (len(header) - 2)))

    for e in entries:
        status = _green("✅ Added") if e.already_added else _yellow("➕ Not added")
        time_str = e.install_time.strftime("%Y-%m-%d %H:%M")
        path = e.display_path
        if len(path) > path_w:
            path = "…" + path[-(path_w - 1):]
        print(
            f"  {e.package:<{pkg_w}}  {path:<{path_w}}  "
            f"{time_str:<16}  {status}"
        )


# ---------- 命令处理 ----------

def _cmd_list(cache: _Cache, args: list[str]) -> None:
    cache.refresh_status()
    print(_bold("\n[deb packages]"))
    _print_table(cache.deb_entries)
    print(_bold("\n[snap packages]"))
    _print_table(cache.snap_entries)
    print()


def _cmd_search(cache: _Cache, args: list[str]) -> None:
    if not args:
        print(_red("usage: sh <keyword>"))
        return
    q = " ".join(args).lower()
    cache.refresh_status()

    deb_matches = [
        e for e in cache.deb_entries
        if q in e.package.lower() or q in str(e.path).lower()
    ]
    snap_matches = [
        e for e in cache.snap_entries
        if q in e.package.lower() or q in str(e.path).lower()
    ]

    print(_bold(f"\n[deb packages — {len(deb_matches)} match(es)]"))
    _print_table(deb_matches)
    print(_bold(f"\n[snap packages — {len(snap_matches)} match(es)]"))
    _print_table(snap_matches)
    print()


def _cmd_add(cache: _Cache, args: list[str]) -> None:
    if not args:
        print(_red("usage: add <package> [<package> ...]"))
        return

    desktop_dir = get_desktop_dir()
    cache.refresh_status()

    def on_conflict(_src, _dst):
        # 交互式 CLI 也走默认：已存在就跳过
        return ConflictAction.SKIP

    for name in args:
        entry = cache.by_name.get(name)
        if entry is None:
            print(_red(f"error: package not found: {name}"))
            continue

        res = install_one(entry.path, desktop_dir, on_conflict)
        if res.status == "installed":
            print(f"  {_green('added')}   {name}  -> {res.target}")
        elif res.status == "skipped":
            print(f"  {_yellow('skipped')} {name} (already exists)")
        else:
            print(f"  {_red('error')}   {name}: {res.message}")

    cache.refresh_status()


def _cmd_rm(cache: _Cache, args: list[str]) -> None:
    if not args:
        print(_red("usage: rm <package> [<package> ...]"))
        return

    desktop_dir = get_desktop_dir()
    cache.refresh_status()

    for name in args:
        entry = cache.by_name.get(name)
        if entry is None:
            print(_red(f"error: package not found: {name}"))
            continue

        res = remove_one(entry.path, desktop_dir)
        if res.status == "removed":
            print(f"  {_green('removed')} {name}")
        elif res.status == "not_found":
            print(f"  {_yellow('not found')} {name} (no shortcut on desktop)")
        else:
            print(f"  {_red('error')}   {name}: {res.message}")

    cache.refresh_status()


def _cmd_help(_cache: _Cache, _args: list[str]) -> None:
    print("""
Available commands:
  list                     list all installed deb/snap packages
  sh <keyword>             search packages by name or path
  add <pkg> [<pkg> ...]    add package(s) to the desktop
  rm  <pkg> [<pkg> ...]    remove package(s) from the desktop
  refresh                  re-scan packages
  help                     show this help
  exit                     exit (or Ctrl+C / Ctrl+D)
""")


def _cmd_refresh(cache: _Cache, _args: list[str]) -> None:
    print("Re-scanning packages...")
    cache.load(force=True)
    print(f"  deb:  {len(cache.deb_entries)}")
    print(f"  snap: {len(cache.snap_entries)}")


# ---------- 主循环 ----------

_COMMANDS = {
    "list": _cmd_list,
    "ls":   _cmd_list,      # 简写
    "sh":   _cmd_search,
    "search": _cmd_search,
    "add":  _cmd_add,
    "rm":   _cmd_rm,
    "remove": _cmd_rm,
    "help": _cmd_help,
    "?":    _cmd_help,
    "refresh": _cmd_refresh,
}


def run_interactive() -> int:
    """交互式命令行主循环。"""
    print(_bold("desktop_installer") + " interactive mode")
    print("Type " + _cyan("help") + " for available commands, " +
          _cyan("exit") + " to quit.\n")

    cache = _Cache()
    print("Scanning packages...")
    cache.load(force=True)
    print(f"  deb:  {len(cache.deb_entries)}")
    print(f"  snap: {len(cache.snap_entries)}\n")

    while True:
        try:
            line = input(_cyan("desktop_installer> "))
        except (EOFError, KeyboardInterrupt):
            print()
            break

        line = line.strip()
        if not line:
            continue

        try:
            parts = shlex.split(line)
        except ValueError as e:
            print(_red(f"parse error: {e}"))
            continue

        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in ("exit", "quit", "q"):
            break

        handler = _COMMANDS.get(cmd)
        if handler is None:
            print(_red(f"unknown command: {cmd}"))
            print("Type " + _cyan("help") + " for available commands.")
            continue

        try:
            handler(cache, args)
        except Exception as e:
            print(_red(f"error: {e}"))

    print("bye.")
    return 0
