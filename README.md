# Kiro IDE 自动化安装项目

这是一个完整的 Kiro IDE 自动化安装和配置项目，包含 Windows Sandbox 环境配置和自动化脚本。

## 🚀 项目概述

本项目提供了一套完整的解决方案，用于在 Windows Sandbox 环境中自动化安装和配置 Kiro IDE，包括：

- Windows Sandbox 环境配置
- 自动化安装脚本
- 登录自动化工具
- 调试和分析工具

## 📁 项目结构

```
sandbox/
├── README.md                    # 项目说明文档
├── start_sandbox.ps1           # 主启动脚本
├── sandbox_config.wsb          # Windows Sandbox 配置文件
├── promat.txt                   # 项目提示文件
├── .claude/                     # Claude Code 配置目录
└── sandbox_files/               # 沙盒环境中的脚本文件
    ├── README.md                # 脚本详细说明
    ├── install.ps1              # Kiro 安装脚本
    ├── automate_kiro.py         # 核心自动化脚本
    ├── kiro_login_automation.py # 登录自动化脚本
    ├── debug_kiro.py            # 调试工具
    ├── window_analyzer.py       # 窗口分析工具
    ├── quick_analyzer.py        # 快速分析工具
    └── kiro_step1.py            # 辅助脚本
```

## 🛠️ 使用方法

### 方法1：完整的 Sandbox 环境（推荐）
```powershell
# 启动 Windows Sandbox 并自动运行安装
powershell -ExecutionPolicy Bypass -File .\start_sandbox.ps1
```

### 方法2：直接在主机运行
```powershell
# 进入 sandbox_files 目录
cd sandbox_files

# 运行完整安装流程
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

### 方法3：仅运行登录自动化
```bash
cd sandbox_files
python kiro_login_automation.py
```

## ⚙️ 系统要求

- Windows 10/11 Pro/Enterprise（支持 Windows Sandbox）
- PowerShell 5.0+
- Python 3.7+（会自动安装）
- 所需 Python 包（会自动安装）：
  - `pywinauto`
  - `requests`

## 🔧 功能特性

### 🎯 自动化安装
- 自动下载 Python 和 Kiro IDE
- 智能检测安装进度
- 自动处理安装界面交互

### 🧠 智能等待机制
- 检测界面加载状态
- 窗口标题变化监控
- 控件数量动态检测
- 登录按钮可用性验证

### 🔐 登录自动化
- 支持多种登录方式：
  - Google 账户登录
  - GitHub 账户登录（默认）
  - AWS Builder ID 登录
  - 组织身份登录
- 3秒倒计时自动选择
- 详细的按钮检测和点击

### 🛠️ 调试工具
- 窗口结构分析
- 控件信息查看
- 界面状态监控
- 详细的日志输出

## 📊 工作流程

1. **环境准备**：启动 Windows Sandbox 或准备主机环境
2. **依赖安装**：自动下载并安装 Python 和依赖包
3. **Kiro 安装**：下载并安装 Kiro IDE
4. **界面等待**：智能检测登录界面加载完成
5. **登录自动化**：自动检测并点击登录按钮
6. **完成**：打开浏览器完成登录流程

## 🐛 故障排除

### 常见问题

1. **PowerShell 执行策略错误**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
   ```

2. **Windows Sandbox 不可用**
   - 确保使用 Windows 10/11 Pro/Enterprise
   - 启用 Windows Sandbox 功能

3. **界面检测失败**
   - 等待更长时间让界面完全加载
   - 使用调试工具分析界面状态

4. **登录按钮未找到**
   - 手动运行 `python kiro_login_automation.py`
   - 检查界面是否完全加载

### 调试工具使用

```bash
# 分析当前窗口结构
python window_analyzer.py

# 快速检查界面状态
python quick_analyzer.py

# 详细调试信息
python debug_kiro.py
```

## 📝 配置说明

### Windows Sandbox 配置 (sandbox_config.wsb)
- 启用网络访问
- 映射主机文件夹
- 配置内存和处理器

### 登录选项配置
- 默认选择：GitHub 登录
- 自动选择时间：3秒
- 支持手动选择 1-5 选项

## 🔄 更新日志

- **v1.0** - 初始版本，基本安装和登录功能
- **v1.1** - 添加 Windows Sandbox 支持
- **v1.2** - 智能等待机制，提高成功率
- **v1.3** - 优化登录按钮检测，支持多种登录方式
- **v1.4** - 修复等待时间问题，提高界面检测准确性
- **v1.5** - 完整项目结构，添加调试工具

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

### 贡献指南
1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

MIT License - 详见 LICENSE 文件

## ⚠️ 免责声明

此项目仅用于学习和自动化目的。请确保：
- 遵守相关软件的使用条款
- 在安全的环境中测试
- 不用于恶意目的

## 🙏 致谢

- 感谢 Anthropic 提供的 Claude Code 开发环境
- 感谢 pywinauto 项目提供的 Windows 自动化支持
- 感谢所有贡献者和测试用户