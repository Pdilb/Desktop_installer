# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Pdilb
import argparse
import sys
from pathlib import Path

from PySide6.QtCore import QLocale, QTranslator, QLibraryInfo, Qt
from PySide6.QtWidgets import QApplication

from . import (
    __app_name__,
    __app_display_name__,
    __version__,
)
from .theme import apply_theme, read_accent_color
from .icon import build_icon


# ---------- i18n ----------

def _load_translations(app: QApplication) -> QTranslator | None:
    """
    根据系统语言加载 .qm 翻译文件。
    优先 zh_CN，其次系统默认；找不到则使用英文源字符串。
    """
    translator = QTranslator(app)

    # 决定目标语言
    sys_locale = QLocale.system().name()          # 例如 "zh_CN" / "en_US"
    target = "zh_CN" if sys_locale.startswith("zh") else "en_US"

    # 查找 .qm 的路径（源码运行 / 安装后兼容）
    candidates = [
        Path(__file__).parent / "i18n",                          # 源码运行
        Path("/usr/share/desktop_installer/i18n"),               # deb 安装
        Path("/usr/lib/python3/dist-packages/desktop_installer/i18n"),
    ]
    for base in candidates:
        qm = base / f"desktop_installer_{target}.qm"
        if qm.exists():
            if translator.load(str(qm)):
                app.installTranslator(translator)
                return translator
    return None


# ---------- 主入口 ----------

def main() -> int:
    parser = argparse.ArgumentParser(
        prog=__app_name__,
        description="将已安装的 deb/snap 包的 .desktop 文件添加到桌面",
    )
    parser.add_argument(
        "--version", action="version",
        version=f"{__app_name__} {__version__}",
    )
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationDisplayName(__app_display_name__)
    app.setOrganizationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setDesktopFileName("Desktop_installer")

    # 加载翻译
    _translator = _load_translations(app)

    # 应用主题
    apply_theme(app)

    # 设置窗口图标（强调色动态生成）
    icon = build_icon(read_accent_color(), size=256)
    if not icon.isNull():
        app.setWindowIcon(icon)

    # 延迟导入，避免 QApplication 尚未创建时就初始化 UI
    from .ui.main_window import MainWindow
    win = MainWindow()
    win.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
