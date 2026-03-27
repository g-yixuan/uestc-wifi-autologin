# UESTC Wi-Fi Auto Login

校园网自动登录工具（Windows 优先）。

## 下载

- [下载最新版本（Windows）](https://github.com/g-yixuan/uestc-wifi-autologin/releases/latest/download/uestc-wifi-autologin-0.1.1.zip)
- [查看所有版本](https://github.com/g-yixuan/uestc-wifi-autologin/releases)


本仓库有两类文档：
- `README.md`（本文件）：给开发者/维护者，放在 GitHub 首页。
- `README.txt`：给最终用户，发布时复制到 `release/README.txt`。

## 功能说明

- 自动检测外网是否可用。
- 检测到校园网网关可达但未联网时，自动发起登录。
- 支持账号密码配置文件 `account_config.yaml`。
- 支持单实例互斥：重复启动会自动退出。
- 异常会写入 `error.log`，便于排查。

## 开发环境

- Windows 10/11
- Python 3.11+
- [uv](https://github.com/astral-sh/uv)

## 本地开发

1. 安装依赖

```bash
uv sync
```

2. 本地运行

```bash
uv run main.py
```

3. 配置账号

- 复制 `account_config.example.yaml` 为 `account_config.yaml`
- 填写自己的账号和密码

## 打包发布

### 1) 有框版本（带控制台）

```bash
uv run --with pyinstaller pyinstaller --clean --noconfirm --onefile --name uestc-wifi-autologin main.py
```

### 2) 无框版本（隐藏控制台）

```bash
uv run --with pyinstaller pyinstaller --clean --noconfirm --onefile --noconsole --name uestc-wifi-autologin-no-console main.py
```

### 3) 组装 release 目录

将以下文件放入 `release/`：

- `dist/uestc-wifi-autologin.exe`
- `dist/uestc-wifi-autologin-no-console.exe`
- `account_config.example.yaml`
- `README.txt`（用户文档）

### 4) 打包 zip（可选）

```powershell
Compress-Archive -Path release\uestc-wifi-autologin.exe,release\uestc-wifi-autologin-no-console.exe,release\account_config.example.yaml,release\README.txt -DestinationPath release\uestc-wifi-autologin-0.1.1.zip -Force
```

## 项目结构

- `main.py`：主程序
- `pyproject.toml`：项目依赖声明
- `uv.lock`：锁文件
- `account_config.example.yaml`：配置模板
- `README.md`：开发者文档
- `README.txt`：用户文档（发布用）

## 常见问题

1. 双击后无反应
- 无框版不会弹控制台，优先检查 `error.log`。

2. 重复启动
- 程序启用了单实例互斥，第二次启动会自动退出。

3. 配置报错
- 删除 `account_config.yaml`，重新运行让程序自动生成模板。


