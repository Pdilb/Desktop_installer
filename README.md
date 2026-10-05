# desktop_installer (dtier)

一键把已安装的 **deb** 和 **snap** 包的 `.desktop` 快捷方式添加到桌面，并自动添加可执行权限。

专为 Ubuntu 设计，跟随系统深浅色模式与强调色。

## 截图

<img width="2880" height="1704" alt="截图 2026-10-05 14-18-45" src="https://github.com/user-attachments/assets/d2d3918e-6717-4216-8b4e-8650f4e72804" />
<img width="2880" height="1704" alt="截图 2026-10-05 14-19-24" src="https://github.com/user-attachments/assets/3f3bcd00-560c-4bc2-9bbd-836c9bac0fc7" />
<img width="687" height="498" alt="截图 2026-10-05 14-20-05" src="https://github.com/user-attachments/assets/5a649ffb-b2d5-4a45-9bcc-fa3a6ca196d4" />
<img width="963" height="681" alt="截图 2026-10-05 14-20-38" src="https://github.com/user-attachments/assets/591b9426-2555-4ba9-873d-d81256178f2e" />

## 功能

- 扫描系统内所有已安装的 deb 包与 snap 包的 `.desktop` 文件
- 标签页分别展示 deb / snap
- 表格显示：包名、完整路径、安装时间、勾选框
- 支持四种排序：包名 A→Z / Z→A、安装时间 早→晚 / 晚→早
- 批量勾选，一键添加到桌面
- 自动 `chmod +x`，并在 GNOME 下标记为“可信任”
- 桌面文件冲突时，可选：覆盖 / 重命名 / 跳过，并支持“应用到全部”
- 不需要 sudo，全程用户权限运行
- Ubuntu 风味 UI：跟随系统强调色与深浅色

## 安装

### 从 deb 包安装（推荐）

```bash
sudo dpkg -i desktop_installer_0.1.0_all.deb
sudo apt-get install -f    # 修复依赖
```

安装后：

- GUI 入口：应用菜单里搜索 **Desktop Installer**
- 命令行：`dtier` 或 `desktop_installer`

### 从源码运行

```bash
git clone https://github.com/Pdilb/desktop_installer.git
cd desktop_installer
python3 -m venv .venv
source .venv/bin/activate
pip install PySide6
python -m desktop_installer
```

## 使用

1. 切换到 **deb包** 或 **snap包** 标签页
2. 用排序下拉菜单选择你想要的排序方式
3. 勾选想要添加到桌面的软件（可多选）
4. 点击右下角 **添加** 按钮
5. 若桌面上已有同名文件，会弹出对话框让你选择处理方式

完成后，桌面上会出现对应的 `.desktop` 文件，双击即可启动程序。

## 命令行简写

安装后可通过 `dtier` 直接启动：

```bash
dtier
```

`desktop_installer` 和 `dtier` 是同一个程序。

## 系统要求

- Ubuntu 22.04 或更新版本（其他基于 GNOME 的发行版亦可）
- Python 3.10+
- PySide6 6.5+
- 依赖系统命令：`dpkg`、`gio`（GNOME）

## 协议

本项目采用 **PolyForm Noncommercial License 1.0.0**。

- ✅ 允许修改、分发
- ✅ 必须保留原作者署名（见 [NOTICE](NOTICE)）
- ❌ 禁止商业用途

完整协议见 [LICENSE](LICENSE)。

## 贡献

欢迎提交 Issue 和 Pull Request。

## 作者

Pdilb — https://github.com/Pdilb
