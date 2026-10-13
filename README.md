
# desktop_installer (dtier)

> Add `.desktop` shortcuts of installed **deb** and **snap** packages to your desktop — in one click.

Ubuntu-native UI · Follows system dark/light mode and accent color · No `sudo` required

---

## Features

- Scan all installed **deb** and **snap** packages
- Tabbed UI: `deb packages (N)` / `snap packages (N)`
- Table: package name, full path, install time, **status**, checkbox
- 4 sorting modes: name A→Z / Z→A, install time old→new / new→old
- **Added / not-added status column**
- Batch select, one-click add to desktop
- Auto `chmod +x`, auto GNOME trusted marking
- Conflict handling: **overwrite / rename / skip**, with "apply to all"
- **Real-time dark/light theme following**
- **Icon colored by system accent color**
- **Chinese / English UI** (auto-detected)
- **About dialog** (F1)
- **man page** (`man dtier`)
- **Auto-add desktop shortcut on install**
- **APT repository**

## Install

### From deb package

```bash
sudo dpkg -i desktop-installer_2.0.0_all.deb
sudo apt-get install -f
```

Then:

· App menu: search Desktop Installer
· Terminal: dtier or desktop_installer

From APT repository

```bash
curl -fsSL https://pdilb.github.io/Desktop_installer/pdilb-public.key | sudo gpg --dearmor -o /usr/share/keyrings/pdilb.gpg
echo "deb [signed-by=/usr/share/keyrings/pdilb.gpg] https://pdilb.github.io/Desktop_installer stable main" | sudo tee /etc/apt/sources.list.d/pdilb.list
sudo apt update
sudo apt install desktop-installer
```

From source

```bash
git clone https://github.com/Pdilb/Desktop_installer.git
cd Desktop_installer
python3 -m venv .venv
source .venv/bin/activate
pip install PySide6

sudo apt-get install -y qt6-l10n-tools
lrelease desktop_installer/i18n/desktop_installer_zh_CN.ts
lrelease desktop_installer/i18n/desktop_installer_en_US.ts

python3 -m desktop_installer
```

Usage

1. Switch to the deb packages or snap packages tab
2. Choose a sorting mode from the dropdown
3. Check the packages you want
4. Click Add at the bottom right
5. If a file already exists, choose Overwrite / Rename / Skip

Keyboard shortcuts

Shortcut Action
F1 Open About dialog

System requirements

· Ubuntu 26.04 (Resolute Raccoon) or newer GNOME-based distro
· Python 3.14+
· PySide6 6.10+
· System commands: dpkg, gio (GNOME)

License

PolyForm Noncommercial License 1.0.0

· ✅ Modify and redistribute
· ✅ Must credit the original author (see NOTICE)
· ❌ Commercial use prohibited

See LICENSE for full text.

---

desktop_installer (dtier) · 中文说明

把已安装 deb / snap 包的 .desktop 快捷方式，一键搬到桌面。

Ubuntu 原生 UI · 跟随系统深浅色模式与强调色 · 全程不需要 sudo

功能

· 扫描系统内所有已安装的 deb 和 snap 包
· 标签页分类展示：deb包 (N) / snap包 (N)
· 表格列：包名、完整路径、安装时间、状态、勾选框
· 4 种排序：包名 A→Z / Z→A、安装时间 早→晚 / 晚→早
· 已添加 / 未添加状态列
· 批量勾选，一键添加到桌面
· 自动加执行权限，GNOME 下自动标记为「可信任」
· 冲突处理：覆盖 / 重命名 / 跳过，支持「应用到全部」
· 深色/浅色模式实时跟随
· 图标颜色跟随系统强调色
· 中英双语界面（自动识别系统语言）
· 关于对话框（快捷键 F1）
· man page（man dtier）
· 安装时自动放桌面快捷方式
· APT 源

安装

从 deb 包安装

```bash
sudo dpkg -i desktop-installer_2.0.0_all.deb
sudo apt-get install -f
```

安装后：

· 应用菜单搜索 Desktop Installer
· 终端输入 dtier 或 desktop_installer

从 APT 源安装

```bash
curl -fsSL https://pdilb.github.io/Desktop_installer/pdilb-public.key | sudo gpg --dearmor -o /usr/share/keyrings/pdilb.gpg
echo "deb [signed-by=/usr/share/keyrings/pdilb.gpg] https://pdilb.github.io/Desktop_installer stable main" | sudo tee /etc/apt/sources.list.d/pdilb.list
sudo apt update
sudo apt install desktop-installer
```

从源码运行

```bash
git clone https://github.com/Pdilb/Desktop_installer.git
cd Desktop_installer
python3 -m venv .venv
source .venv/bin/activate
pip install PySide6

sudo apt-get install -y qt6-l10n-tools
lrelease desktop_installer/i18n/desktop_installer_zh_CN.ts
lrelease desktop_installer/i18n/desktop_installer_en_US.ts

python3 -m desktop_installer
```

使用

1. 切换到 deb包 或 snap包 标签页
2. 用排序下拉菜单选择排序方式
3. 勾选想要添加到桌面的软件
4. 点击右下角 添加
5. 桌面已有同名文件时，选择 覆盖 / 重命名 / 跳过

快捷键

快捷键 功能
F1 打开关于对话框

系统要求

· Ubuntu 26.04（代号 Resolute Raccoon）或更新版本的 GNOME 系发行版
· Python 3.14+
· PySide6 6.10+
· 系统命令：dpkg、gio

协议

PolyForm Noncommercial License 1.0.0

· ✅ 允许修改、分发
· ✅ 必须保留原作者署名（见 NOTICE）
· ❌ 禁止商业用途

完整协议见 LICENSE。

作者

Pdilb — https://github.com/Pdilb
