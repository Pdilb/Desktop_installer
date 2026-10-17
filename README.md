# desktop_installer (dtier)

> Add `.desktop` shortcuts of installed **deb** and **snap** packages to your desktop — in one click.

Ubuntu-native UI · Follows system dark/light mode · No `sudo` required

---

## Features

- Scan all installed **deb** and **snap** packages
- Real-time progress dialog on startup
- **Search bar** to filter packages by name or path
- Tabbed UI: `deb packages (N)` / `snap packages (N)`
- 4 sorting modes: name A→Z / Z→A, install time old→new / new→old
- **Added / not-added status column**
- Batch select, **Add** and **Remove** shortcuts
- **Interactive command-line mode** (`dtier --nogui`)
- **Check for updates** in the About dialog
- **Chinese / English UI** (auto-detected)
- **man page** (`man dtier`)

## Install

### From deb package

```bash
sudo dpkg -i desktop-installer_3.0.0_all.deb
sudo apt-get install -f
```

From APT repository (Recommended)

```bash
curl -fsSL https://pdilb.github.io/Desktop_installer/pdilb-public.key | sudo gpg --dearmor -o /usr/share/keyrings/pdilb.gpg
echo "deb [signed-by=/usr/share/keyrings/pdilb.gpg] https://pdilb.github.io/Desktop_installer stable main" | sudo tee /etc/apt/sources.list.d/pdilb.list
sudo apt update
sudo apt install desktop-installer
```

Usage

GUI Mode

1. Switch to the deb packages or snap packages tab
2. Type in the search bar to filter
3. Check the packages you want
4. Click Add or Remove selected

Command-Line Mode

```bash
dtier --nogui
```

Inside the interactive shell:

```text
desktop_installer> list                   # list all packages
desktop_installer> sh <keyword>           # search packages
desktop_installer> add <pkg> [<pkg>...]   # add to desktop
desktop_installer> rm  <pkg> [<pkg>...]   # remove from desktop
desktop_installer> refresh                # rescan
desktop_installer> exit                   # exit (or Ctrl+C)
```

System requirements

· Ubuntu 24.04 / 26.04 (or newer GNOME-based distro)
· Python 3.12+
· PySide6 6.6+
· System commands: dpkg, gio

License

PolyForm Noncommercial License 1.0.0

· ✅ Modify and redistribute
· ✅ Must credit the original author (see NOTICE)
· ❌ Commercial use prohibited

---

desktop_installer (dtier) · 中文说明

把已安装 deb / snap 包的 .desktop 快捷方式，一键搬到桌面。

Ubuntu 原生 UI · 跟随系统深浅色 · 全程不需要 sudo

功能

· 扫描系统内所有已安装的 deb 和 snap 包
· 启动时显示实时进度条
· 搜索栏，实时过滤包名和路径
· 4 种排序：包名 A→Z / Z→A、时间 早→晚 / 晚→早
· 已添加 / 未添加状态列
· 批量添加、批量移除快捷方式
· 交互式命令行模式（dtier --nogui）
· 在关于界面检查更新
· 中英双语界面（自动识别）
· 附带 man page（man dtier）

安装

从 APT 源安装（推荐）

```bash
curl -fsSL https://pdilb.github.io/Desktop_installer/pdilb-public.key | sudo gpg --dearmor -o /usr/share/keyrings/pdilb.gpg
echo "deb [signed-by=/usr/share/keyrings/pdilb.gpg] https://pdilb.github.io/Desktop_installer stable main" | sudo tee /etc/apt/sources.list.d/pdilb.list
sudo apt update
sudo apt install desktop-installer
```

命令行模式

```bash
dtier --nogui
```

进入交互提示符后：

```text
desktop_installer> list
desktop_installer> sh firefox
desktop_installer> add firefox
desktop_installer> rm firefox