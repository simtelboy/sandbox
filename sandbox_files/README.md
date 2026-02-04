# Kiro 自动化安装和登录脚本

这是一个用于自动化安装和配置 Kiro IDE 的 PowerShell 和 Python 脚本集合。

## 🚀 功能特性

- **自动化安装**：自动下载并安装 Kiro IDE
- **智能等待**：检测安装进度和界面加载状态
- **登录自动化**：自动检测并点击登录按钮
- **多种登录方式**：支持 Google、GitHub、AWS Builder ID 等
- **用户友好**：提供详细的进度反馈和错误处理

## 📁 文件说明

### 主要脚本
- `start_sandbox.ps1` - 主启动脚本，启动整个自动化流程
- `install.ps1` - Kiro 安装脚本
- `automate_kiro.py` - 核心自动化脚本，处理安装过程和界面检测
- `kiro_login_automation.py` - 登录自动化脚本

### 辅助工具
- `debug_kiro.py` - 调试工具，用于分析 Kiro 界面
- `window_analyzer.py` - 窗口分析工具
- `quick_analyzer.py` - 快速界面分析工具

## 🛠️ 使用方法

### 方法1：完整自动化流程
```powershell
powershell -ExecutionPolicy Bypass -File .\start_sandbox.ps1
```

### 方法2：仅安装 Kiro
```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

### 方法3：仅运行登录自动化
```bash
python kiro_login_automation.py
```

## ⚙️ 系统要求

- Windows 10/11
- PowerShell 5.0+
- Python 3.7+
- 所需 Python 包：
  - `pywinauto`
  - `requests`

## 🔧 配置选项

脚本支持以下登录方式：
1. Google 账户登录
2. GitHub 账户登录（默认）
3. AWS Builder ID 登录
4. 组织身份登录

默认选择 GitHub 登录，3秒后自动执行。

## 📊 工作流程

1. **安装阶段**：下载并安装 Kiro IDE
2. **等待阶段**：智能检测界面加载状态
3. **登录阶段**：自动检测并点击登录按钮
4. **完成**：打开浏览器完成登录流程

## 🐛 故障排除

如果遇到问题：

1. **权限问题**：使用管理员权限运行 PowerShell
2. **执行策略**：使用 `-ExecutionPolicy Bypass` 参数
3. **界面检测失败**：等待更长时间让界面完全加载
4. **登录按钮未找到**：手动运行 `python kiro_login_automation.py`

## 📝 更新日志

- **v1.0** - 初始版本，基本安装和登录功能
- **v1.1** - 添加智能等待机制，提高成功率
- **v1.2** - 优化登录按钮检测，支持多种登录方式
- **v1.3** - 修复等待时间问题，提高界面检测准确性

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

## 📄 许可证

MIT License - 详见 LICENSE 文件

## ⚠️ 免责声明

此脚本仅用于学习和自动化目的。请确保遵守相关软件的使用条款。