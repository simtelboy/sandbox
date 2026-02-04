# 检查并启用 Windows Sandbox 功能
Write-Host "检查 Windows Sandbox 功能状态..." -ForegroundColor Yellow

try {
    # 检查 Windows Sandbox 功能是否启用
    $sandboxFeature = Get-WindowsOptionalFeature -Online -FeatureName "Containers-DisposableClientVM" -ErrorAction SilentlyContinue

    if ($sandboxFeature) {
        Write-Host "Windows Sandbox 功能状态: $($sandboxFeature.State)" -ForegroundColor Cyan

        if ($sandboxFeature.State -eq "Disabled") {
            Write-Host "⚠️  Windows Sandbox 功能未启用，正在启用..." -ForegroundColor Yellow
            Write-Host "注意：启用后需要重启计算机才能生效！" -ForegroundColor Red

            try {
                # 启用 Windows Sandbox 功能
                Enable-WindowsOptionalFeature -Online -FeatureName "Containers-DisposableClientVM" -All -NoRestart
                Write-Host "✅ Windows Sandbox 功能已启用，请重启计算机后再运行此脚本。" -ForegroundColor Green
                Write-Host ""
                Write-Host "按任意键退出..." -ForegroundColor Gray
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                exit 1
            } catch {
                Write-Host "❌ 启用 Windows Sandbox 功能失败: $($_.Exception.Message)" -ForegroundColor Red
                Write-Host "请手动启用 Windows Sandbox 功能：" -ForegroundColor Yellow
                Write-Host "1. 打开 '启用或关闭 Windows 功能'" -ForegroundColor Gray
                Write-Host "2. 勾选 'Windows Sandbox'" -ForegroundColor Gray
                Write-Host "3. 重启计算机" -ForegroundColor Gray
                Write-Host ""
                Write-Host "按任意键退出..." -ForegroundColor Gray
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                exit 1
            }
        } else {
            Write-Host "✅ Windows Sandbox 功能已启用，可以正常使用。" -ForegroundColor Green
        }
    } else {
        Write-Host "⚠️  无法检测到 Windows Sandbox 功能，可能不支持此功能。" -ForegroundColor Yellow
        Write-Host "请确认您的 Windows 版本支持 Windows Sandbox（Windows 10 Pro/Enterprise 或 Windows 11）" -ForegroundColor Gray
    }
} catch {
    Write-Host "⚠️  检查 Windows Sandbox 功能时出现错误: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "继续执行脚本..." -ForegroundColor Gray
}

Write-Host ""

# 检查 Kiro 进程是否正在运行
Write-Host "检查系统中是否有 Kiro 进程正在运行..." -ForegroundColor Yellow

try {
    # 只查找真正的 kiro.exe 进程（精确匹配进程名）
    $kiroProcesses = Get-Process | Where-Object { $_.ProcessName -eq "kiro" }

    if ($kiroProcesses.Count -gt 0) {
        Write-Host ""
        Write-Host "⚠️  检测到 Kiro 进程正在运行！" -ForegroundColor Red
        Write-Host "发现的 Kiro 进程：" -ForegroundColor Yellow

        foreach ($process in $kiroProcesses) {
            $windowTitle = if ($process.MainWindowTitle) { $process.MainWindowTitle } else { "无窗口标题" }
            Write-Host "  - 进程名: $($process.ProcessName).exe | PID: $($process.Id) | 窗口: $windowTitle" -ForegroundColor Cyan
        }

        Write-Host ""
        Write-Host "❌ 请先关闭所有 Kiro 程序，然后重新运行此脚本。" -ForegroundColor Red
        Write-Host ""
        Write-Host "按任意键退出..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    } else {
        Write-Host "✅ 未检测到 Kiro 进程，可以安全继续。" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  检查 Kiro 进程时出现错误: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "继续执行脚本..." -ForegroundColor Gray
}

Write-Host ""

# ==================== 检查并下载 sandbox_files 文件夹 ====================

$sandboxFilesPath = "$PSScriptRoot\sandbox_files"

if (!(Test-Path $sandboxFilesPath)) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "首次运行检测" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "⚠️  未检测到 sandbox_files 文件夹" -ForegroundColor Yellow
    Write-Host "📦 正在从 GitHub 下载必要文件..." -ForegroundColor Cyan
    Write-Host ""

    $githubZipUrl = "https://github.com/simtelboy/sandbox/archive/refs/heads/main.zip"
    $tempZipPath = "$PSScriptRoot\sandbox-temp.zip"
    $tempExtractPath = "$PSScriptRoot\sandbox-main"

    try {
        # 下载 zip 文件
        Write-Host "📥 下载中... (约 12 MB)" -ForegroundColor Yellow
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $githubZipUrl -OutFile $tempZipPath -UseBasicParsing
        Write-Host "✅ 下载完成" -ForegroundColor Green

        # 解压 zip 文件
        Write-Host "📂 解压中..." -ForegroundColor Yellow
        Expand-Archive -Path $tempZipPath -DestinationPath $PSScriptRoot -Force
        Write-Host "✅ 解压完成" -ForegroundColor Green

        # 移动 sandbox_files 文件夹到正确位置
        Write-Host "📁 配置文件夹..." -ForegroundColor Yellow
        if (Test-Path "$tempExtractPath\sandbox_files") {
            Move-Item -Path "$tempExtractPath\sandbox_files" -Destination $sandboxFilesPath -Force
            Write-Host "✅ sandbox_files 文件夹已就绪" -ForegroundColor Green
        } else {
            throw "解压后未找到 sandbox_files 文件夹"
        }

        # 清理临时文件
        Write-Host "🧹 清理临时文件..." -ForegroundColor Yellow
        Remove-Item -Path $tempZipPath -Force -ErrorAction SilentlyContinue
        Remove-Item -Path $tempExtractPath -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "✅ 清理完成" -ForegroundColor Green

        Write-Host ""
        Write-Host "🎉 sandbox_files 文件夹下载成功！" -ForegroundColor Green
        Write-Host ""

    } catch {
        Write-Host ""
        Write-Host "❌ 下载失败: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        Write-Host "请手动下载并解压：" -ForegroundColor Yellow
        Write-Host "1. 访问: https://github.com/simtelboy/sandbox" -ForegroundColor Gray
        Write-Host "2. 点击 'Code' -> 'Download ZIP'" -ForegroundColor Gray
        Write-Host "3. 解压后，将 sandbox_files 文件夹放到脚本所在目录" -ForegroundColor Gray
        Write-Host ""
        Write-Host "按任意键退出..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
} else {
    Write-Host "✅ sandbox_files 文件夹已存在" -ForegroundColor Green
}

Write-Host ""

# 检查并配置 .env 文件
$envFilePath = "$PSScriptRoot\sandbox_files\.env"

if (!(Test-Path $envFilePath)) {
    Write-Host "⚙️  首次运行检测到，开始配置程序..." -ForegroundColor Yellow
    Write-Host ""

    # 创建默认 .env 文件
    $defaultEnvContent = @"
# GitHub注册自动化配置
[EMAIL]
# 邮箱域名配置（用于生成随机邮箱地址）
EMAIL_DOMAIN=example.com

# 邮箱IMAP配置
IMAP_SERVER=imap.example.com
IMAP_PORT=993
IMAP_USER=your_email@qq.com
IMAP_PASS=xxxxxxxxxxxxxxxx
IMAP_USE_SSL=True

# Kiro登录方式配置
[LOGIN]
# 默认登录方式选择 (1=Google, 2=GitHub, 3=AWS Builder ID)
DEFAULT_LOGIN_METHOD=2

# 注册模式配置
[REGISTRATION]
# 注册模式 (false=自动化, true=手动化)
ENABLE_MANUAL_MODE=false

# 手机验证配置
[SMS]
# 手机号验证网站（用于接收验证码）
SMS_WEBSITE=https://sms-activate.org/
"@

    $defaultEnvContent | Out-File -FilePath $envFilePath -Encoding UTF8 -Force
    Write-Host "✅ 已创建配置文件: $envFilePath" -ForegroundColor Green
    Write-Host ""

    # 用户配置流程
    Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                    📧 邮箱配置向导                            ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""

    # 1. 邮箱域名配置
    Write-Host "【步骤 1/3】邮箱域名配置" -ForegroundColor Yellow
    Write-Host "你的邮箱域名（被 Cloudflare 转发的域名，例如: kt167.cc）: " -NoNewline -ForegroundColor White
    $emailDomain = Read-Host

    if ([string]::IsNullOrWhiteSpace($emailDomain)) {
        $emailDomain = "example.com"
        Write-Host "  → 使用默认域名: $emailDomain" -ForegroundColor Gray
    }

    # 2. 接收转发邮箱地址
    Write-Host ""
    Write-Host "【步骤 2/3】接收邮箱地址" -ForegroundColor Yellow
    Write-Host "你的接收邮箱地址（例如: your_email@qq.com）: " -NoNewline -ForegroundColor White
    $forwardEmail = Read-Host

    if ([string]::IsNullOrWhiteSpace($forwardEmail)) {
        $forwardEmail = "your_email@qq.com"
        Write-Host "  → 使用默认邮箱: $forwardEmail" -ForegroundColor Gray
    }

    # 解析邮箱后缀
    $emailParts = $forwardEmail -split "@"
    if ($emailParts.Count -eq 2) {
        $emailProvider = $emailParts[1].ToLower()

        # 根据邮箱提供商设置IMAP服务器
        $imapServer = switch ($emailProvider) {
            "qq.com" { "imap.qq.com" }
            "163.com" { "imap.163.com" }
            "126.com" { "imap.126.com" }
            "gmail.com" { "imap.gmail.com" }
            "outlook.com" { "imap-mail.outlook.com" }
            "hotmail.com" { "imap-mail.outlook.com" }
            default { "imap.$emailProvider" }
        }
    } else {
        $imapServer = "imap.example.com"
        $forwardEmail = "your_email@qq.com"
        Write-Host "  → 邮箱格式无效，使用默认配置" -ForegroundColor Yellow
    }

    # 3. 邮件授权码（醒目提示）
    Write-Host ""
    Write-Host "【步骤 3/3】邮箱授权码" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "┌─────────────────────────────────────────────────────────────┐" -ForegroundColor Cyan
    Write-Host "│  ⚠️  重要：这里需要的是 IMAP 授权码，不是邮箱密码！        │" -ForegroundColor Cyan
    Write-Host "└─────────────────────────────────────────────────────────────┘" -ForegroundColor Cyan
    Write-Host ""

    # 根据邮箱类型显示获取授权码的方法
    if ($emailProvider -eq "qq.com") {
        Write-Host "📱 QQ 邮箱授权码获取方法：" -ForegroundColor Green
        Write-Host "  1. 登录 QQ 邮箱网页版 (mail.qq.com)" -ForegroundColor White
        Write-Host "  2. 点击【设置】→【账户】" -ForegroundColor White
        Write-Host "  3. 找到【POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务】" -ForegroundColor White
        Write-Host "  4. 开启【IMAP/SMTP服务】" -ForegroundColor White
        Write-Host "  5. 点击【生成授权码】，按提示用手机发送短信" -ForegroundColor White
        Write-Host "  6. 复制生成的授权码（16位字母，例如：abcdefghijklmnop）" -ForegroundColor White
    } elseif ($emailProvider -eq "163.com" -or $emailProvider -eq "126.com") {
        Write-Host "📱 163/126 邮箱授权码获取方法：" -ForegroundColor Green
        Write-Host "  1. 登录 163/126 邮箱网页版" -ForegroundColor White
        Write-Host "  2. 点击【设置】→【POP3/SMTP/IMAP】" -ForegroundColor White
        Write-Host "  3. 开启【IMAP/SMTP服务】" -ForegroundColor White
        Write-Host "  4. 点击【客户端授权密码】→【新增授权密码】" -ForegroundColor White
        Write-Host "  5. 按提示用手机发送短信验证" -ForegroundColor White
        Write-Host "  6. 复制生成的授权码" -ForegroundColor White
    } else {
        Write-Host "📱 邮箱授权码获取方法：" -ForegroundColor Green
        Write-Host "  1. 登录邮箱网页版" -ForegroundColor White
        Write-Host "  2. 进入【设置】→【账户安全】或【POP3/IMAP设置】" -ForegroundColor White
        Write-Host "  3. 开启 IMAP 服务" -ForegroundColor White
        Write-Host "  4. 生成客户端授权码/应用专用密码" -ForegroundColor White
        Write-Host "  5. 复制生成的授权码" -ForegroundColor White
    }

    Write-Host ""
    Write-Host "请输入邮箱授权码: " -NoNewline -ForegroundColor Yellow
    $imapPass = Read-Host

    if ([string]::IsNullOrWhiteSpace($imapPass)) {
        $imapPass = "xxxxxxxxxxxxxxxx"
        Write-Host "使用默认授权码（请稍后手动修改）" -ForegroundColor Gray
    }

    # 更新 .env 文件
    $updatedEnvContent = @"
# GitHub注册自动化配置
[EMAIL]
# 邮箱域名配置（用于生成随机邮箱地址）
EMAIL_DOMAIN=$emailDomain

# 邮箱IMAP配置
IMAP_SERVER=$imapServer
IMAP_PORT=993
IMAP_USER=$forwardEmail
IMAP_PASS=$imapPass
IMAP_USE_SSL=True

# Kiro登录方式配置
[LOGIN]
# 默认登录方式选择 (1=Google, 2=GitHub, 3=AWS Builder ID)
DEFAULT_LOGIN_METHOD=2

# 注册模式配置
[REGISTRATION]
# 注册模式 (false=自动化, true=手动化)
ENABLE_MANUAL_MODE=false

# 手机验证配置
[SMS]
# 手机号验证网站（用于接收验证码）
SMS_WEBSITE=https://sms-activate.org/
"@

    $updatedEnvContent | Out-File -FilePath $envFilePath -Encoding UTF8 -Force

    Write-Host ""
    Write-Host "✅ 配置完成！配置信息已保存到: $envFilePath" -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 配置摘要:" -ForegroundColor Cyan
    Write-Host "  邮箱域名: $emailDomain" -ForegroundColor Gray
    Write-Host "  IMAP服务器: $imapServer" -ForegroundColor Gray
    Write-Host "  转发邮箱: $forwardEmail" -ForegroundColor Gray
    Write-Host "  授权码: " -NoNewline -ForegroundColor Gray
    Write-Host $imapPass.Substring(0, [Math]::Min(4, $imapPass.Length)) -NoNewline -ForegroundColor Gray
    Write-Host "****" -ForegroundColor Gray
    Write-Host ""
    Write-Host "按任意键继续..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    Clear-Host
} else {
    Write-Host "✅ 配置文件已存在: $envFilePath" -ForegroundColor Green
}

Write-Host ""

# 检查并创建 VirtualBrowser 文件夹（用于固化）
$virtualBrowserPath = "$PSScriptRoot\VirtualBrowser"
if (!(Test-Path $virtualBrowserPath)) {
    Write-Host "📁 创建 VirtualBrowser 文件夹（用于固化安装）..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $virtualBrowserPath -Force | Out-Null
    Write-Host "✅ VirtualBrowser 文件夹已创建" -ForegroundColor Green
} else {
    # 检查文件夹是否有内容
    $vbFiles = Get-ChildItem -Path $virtualBrowserPath -Recurse -ErrorAction SilentlyContinue
    if ($vbFiles.Count -gt 0) {
        Write-Host "✅ VirtualBrowser 已固化（文件数: $($vbFiles.Count)）" -ForegroundColor Green
    } else {
        Write-Host "📁 VirtualBrowser 文件夹为空，首次运行时将自动安装" -ForegroundColor Yellow
    }
}

Write-Host ""

# 读取 .env 配置文件
function Read-EnvConfig {
    $envFilePath = "$PSScriptRoot\sandbox_files\.env"
    $config = @{}

    if (Test-Path $envFilePath) {
        $content = Get-Content $envFilePath -Encoding UTF8
        foreach ($line in $content) {
            if ($line -match '^([^#=]+)=(.*)$') {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                $config[$key] = $value
            }
        }
    }

    return $config
}

# 更新 .env 配置文件中的单个值
function Update-EnvConfig($key, $value) {
    $envFilePath = "$PSScriptRoot\sandbox_files\.env"

    if (Test-Path $envFilePath) {
        $content = Get-Content $envFilePath -Encoding UTF8
        $updated = $false

        for ($i = 0; $i -lt $content.Count; $i++) {
            if ($content[$i] -match "^$([regex]::Escape($key))=") {
                $content[$i] = "$key=$value"
                $updated = $true
                break
            }
        }

        if ($updated) {
            $content | Out-File -FilePath $envFilePath -Encoding UTF8 -Force
            return $true
        }
    }

    return $false
}

# 登录方式选择器 - 左右切换界面（防闪烁）
function Show-LoginMethodSelector($settingItem, $currentValue) {
    $options = @("1", "2", "3")  # 1=Google, 2=GitHub, 3=AWS Builder ID
    $optionNames = @("Google", "GitHub", "AWS Builder ID")

    # 确定当前选中的选项索引
    $currentIndex = [array]::IndexOf($options, $currentValue)
    $selectedOption = if ($currentIndex -ge 0) { $currentIndex } else { 1 }  # 默认GitHub
    $needFullRedraw = $true
    $headerHeight = 8  # 头部占用行数
    $optionLineY = $headerHeight + 2  # 选项所在行

    # 隐藏光标
    [Console]::CursorVisible = $false

    # 绘制选项行（防闪烁）
    function Draw-LoginOptionLine($options, $optionNames, $selectedOption) {
        [Console]::SetCursorPosition(0, $optionLineY)
        Write-Host "  "  -NoNewline

        for ($i = 0; $i -lt $options.Count; $i++) {
            if ($i -eq $selectedOption) {
                # 选中状态：黑底黄字
                Write-Host "[ $($options[$i]) - $($optionNames[$i]) ]" -ForegroundColor Black -BackgroundColor Yellow -NoNewline
            } else {
                # 未选中状态：灰色
                Write-Host "  $($options[$i]) - $($optionNames[$i])  " -ForegroundColor Gray -NoNewline
            }
            Write-Host "  " -NoNewline  # 选项间距
        }

        # 清除行尾可能的残留字符
        Write-Host (" " * 10)
    }

    # 局部更新选项选择（防闪烁核心）
    function Update-LoginOptionSelection($options, $optionNames, $oldOption, $newOption) {
        if ($oldOption -ne $newOption) {
            Draw-LoginOptionLine $options $optionNames $newOption
        }
    }

    # 完整界面绘制（仅在必要时使用）
    function Draw-FullLoginSelectorInterface($settingItem, $currentValue, $options, $optionNames, $selectedOption) {
        Clear-Host
        Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
        Write-Host "║                    默认登录方式选择                          ║" -ForegroundColor Cyan
        Write-Host "╠══════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
        Write-Host "║  使用 ←→ 选择登录方式，Enter 确认，ESC 取消                  ║" -ForegroundColor Yellow
        Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
        Write-Host ""

        Write-Host "设置项: " -ForegroundColor White -NoNewline
        Write-Host "$($settingItem.Name)" -ForegroundColor Yellow
        Write-Host ""

        # 绘制选项
        Draw-LoginOptionLine $options $optionNames $selectedOption

        Write-Host ""
        Write-Host ""
        Write-Host "💡 提示: 这是Kiro程序自动点击的登录按钮类型" -ForegroundColor Gray
    }

    try {
        while ($true) {
            # 首次进入时完整绘制
            if ($needFullRedraw) {
                Draw-FullLoginSelectorInterface $settingItem $currentValue $options $optionNames $selectedOption
                $needFullRedraw = $false
            }

            $key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            switch ($key.VirtualKeyCode) {
                37 { # Left Arrow - 局部更新
                    $oldOption = $selectedOption
                    $selectedOption = if ($selectedOption -gt 0) { $selectedOption - 1 } else { $options.Count - 1 }
                    Update-LoginOptionSelection $options $optionNames $oldOption $selectedOption
                }
                39 { # Right Arrow - 局部更新
                    $oldOption = $selectedOption
                    $selectedOption = if ($selectedOption -lt ($options.Count - 1)) { $selectedOption + 1 } else { 0 }
                    Update-LoginOptionSelection $options $optionNames $oldOption $selectedOption
                }
                13 { # Enter - 确认选择
                    return $options[$selectedOption]
                }
                27 { # ESC - 取消
                    return $null
                }
            }
        }
    }
    finally {
        # 恢复光标显示
        [Console]::CursorVisible = $true
    }
}

# 手动模式选择器 - 左右切换界面（防闪烁）
function Show-ManualModeSelector($settingItem, $currentValue) {
    $options = @("false", "true")  # false=自动化, true=手动化
    $optionNames = @("自动化", "手动化")

    # 确定当前选中的选项索引
    $selectedOption = if ($currentValue.ToLower() -eq "true") { 1 } else { 0 }
    $needFullRedraw = $true
    $headerHeight = 8  # 头部占用行数
    $optionLineY = $headerHeight + 2  # 选项所在行

    # 隐藏光标
    [Console]::CursorVisible = $false

    # 绘制选项行（防闪烁）
    function Draw-OptionLine($options, $optionNames, $selectedOption) {
        [Console]::SetCursorPosition(0, $optionLineY)
        Write-Host "  "  -NoNewline

        for ($i = 0; $i -lt $options.Count; $i++) {
            if ($i -eq $selectedOption) {
                # 选中状态：黑底黄字
                Write-Host "[ $($optionNames[$i]) ]" -ForegroundColor Black -BackgroundColor Yellow -NoNewline
            } else {
                # 未选中状态：灰色
                Write-Host "  $($optionNames[$i])  " -ForegroundColor Gray -NoNewline
            }
            Write-Host "    " -NoNewline  # 选项间距
        }

        # 清除行尾可能的残留字符
        Write-Host (" " * 20)
    }

    # 局部更新选项选择（防闪烁核心）
    function Update-OptionSelection($options, $optionNames, $oldOption, $newOption) {
        if ($oldOption -ne $newOption) {
            Draw-OptionLine $options $optionNames $newOption
        }
    }

    # 完整界面绘制（仅在必要时使用）
    function Draw-FullSelectorInterface($settingItem, $currentValue, $options, $optionNames, $selectedOption) {
        Clear-Host
        Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
        Write-Host "║                      注册模式选择                            ║" -ForegroundColor Cyan
        Write-Host "╠══════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
        Write-Host "║  使用 ←→ 选择模式，Enter 确认，ESC 取消                      ║" -ForegroundColor Yellow
        Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
        Write-Host ""

        Write-Host "设置项: " -ForegroundColor White -NoNewline
        Write-Host "$($settingItem.Name)" -ForegroundColor Yellow
        Write-Host ""

        # 绘制选项
        Draw-OptionLine $options $optionNames $selectedOption

        Write-Host ""
        Write-Host ""
        Write-Host "💡 提示: 自动化=程序自动填写表单，手动化=用户手动操作" -ForegroundColor Gray
    }

    try {
        while ($true) {
            # 首次进入时完整绘制
            if ($needFullRedraw) {
                Draw-FullSelectorInterface $settingItem $currentValue $options $optionNames $selectedOption
                $needFullRedraw = $false
            }

            $key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            switch ($key.VirtualKeyCode) {
                37 { # Left Arrow - 局部更新
                    $oldOption = $selectedOption
                    $selectedOption = if ($selectedOption -gt 0) { $selectedOption - 1 } else { $options.Count - 1 }
                    Update-OptionSelection $options $optionNames $oldOption $selectedOption
                }
                39 { # Right Arrow - 局部更新
                    $oldOption = $selectedOption
                    $selectedOption = if ($selectedOption -lt ($options.Count - 1)) { $selectedOption + 1 } else { 0 }
                    Update-OptionSelection $options $optionNames $oldOption $selectedOption
                }
                13 { # Enter - 确认选择
                    return $options[$selectedOption]
                }
                27 { # ESC - 取消
                    return $null
                }
            }
        }
    }
    finally {
        # 恢复光标显示
        [Console]::CursorVisible = $true
    }
}

# 系统设置菜单 - 无闪烁版本
function Show-SystemSettings {
    $selectedIndex = 0
    $needFullRedraw = $true
    $headerHeight = 7  # 头部占用行数

    # 隐藏光标
    [Console]::CursorVisible = $false

    # 设置项定义
    $settingItems = @(
        @{ Key = "EMAIL_DOMAIN"; Name = "邮箱域名（用来生成随机邮箱的缀名，必须要在Cloudflare设置转发）"; DefaultValue = "example.com" },
        @{ Key = "IMAP_USER"; Name = "接受转发的邮箱（比如:xxx@qq.com）"; DefaultValue = "your_email@qq.com" },
        @{ Key = "IMAP_PASS"; Name = "邮箱授权码"; DefaultValue = "xxxxxxxxxxxxxxxx"; IsPassword = $true },
        @{ Key = "DEFAULT_LOGIN_METHOD"; Name = "默认注册账号的网站"; DefaultValue = "2"; IsChoice = $true },
        @{ Key = "ENABLE_MANUAL_MODE"; Name = "注册模式"; DefaultValue = "false"; IsManualMode = $true },
        @{ Key = "SMS_WEBSITE"; Name = "手机号验证网站（用于接收验证码）"; DefaultValue = "https://sms-activate.org/" }
    )

    # 绘制单个设置项
    function Draw-SettingItem($item, $index, $isSelected, $config) {
        $lineY = $headerHeight + $index
        [Console]::SetCursorPosition(0, $lineY)

        # 获取当前值
        $currentValue = if ($config.ContainsKey($item.Key)) { $config[$item.Key] } else { $item.DefaultValue }

        # 处理密码显示
        if ($item.IsPassword -and $currentValue -ne $item.DefaultValue) {
            $displayValue = $currentValue.Substring(0, [Math]::Min(4, $currentValue.Length)) + "****"
        } elseif ($item.IsChoice) {
            $choiceText = switch ($currentValue) {
                "1" { "1 (Google)" }
                "2" { "2 (GitHub)" }
                "3" { "3 (AWS Builder ID)" }
                default { $currentValue }
            }
            $displayValue = $choiceText
        } elseif ($item.IsManualMode) {
            $modeText = switch ($currentValue.ToLower()) {
                "true" { "手动化" }
                "false" { "自动化" }
                default { $currentValue }
            }
            $displayValue = $modeText
        } else {
            $displayValue = $currentValue
        }

        if ($isSelected) {
            Write-Host "  ► " -ForegroundColor Green -NoNewline
            Write-Host "[$($index+1)] " -ForegroundColor White -NoNewline
            Write-Host "$($item.Name)" -ForegroundColor Yellow -NoNewline
            Write-Host " = " -ForegroundColor White -NoNewline
            Write-Host "$displayValue" -ForegroundColor Yellow
        } else {
            Write-Host "    " -NoNewline
            Write-Host "[$($index+1)] " -ForegroundColor Gray -NoNewline
            Write-Host "$($item.Name)" -ForegroundColor White -NoNewline
            Write-Host " = " -ForegroundColor Gray -NoNewline
            Write-Host "$displayValue" -ForegroundColor Yellow
        }
    }

    # 局部更新选择
    function Update-SettingSelection($settingItems, $oldIndex, $newIndex, $config) {
        # 重绘旧选中项
        if ($oldIndex -ge 0 -and $oldIndex -lt $settingItems.Count) {
            Draw-SettingItem $settingItems[$oldIndex] $oldIndex $false $config
        }

        # 重绘新选中项
        if ($newIndex -ge 0 -and $newIndex -lt $settingItems.Count) {
            Draw-SettingItem $settingItems[$newIndex] $newIndex $true $config
        }
    }

    # 完整界面绘制
    function Draw-FullSettingsInterface($settingItems, $selectedIndex, $config) {
        Clear-Host
        Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
        Write-Host "║                        系统设置                              ║" -ForegroundColor Cyan
        Write-Host "╠══════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
        Write-Host "║  使用 ↑↓ 选择设置项，Enter 修改，ESC 返回主菜单              ║" -ForegroundColor Yellow
        Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "注：1=Google, 2=GitHub, 3=AWS Builder ID | 注册模式：自动化/手动化" -ForegroundColor Gray
        Write-Host ""

        # 显示所有设置项
        for ($i = 0; $i -lt $settingItems.Count; $i++) {
            Draw-SettingItem $settingItems[$i] $i ($i -eq $selectedIndex) $config
        }

        Write-Host ""
    }

    try {
        while ($true) {
            # 读取当前配置
            $config = Read-EnvConfig

            # 首次进入时完整绘制
            if ($needFullRedraw) {
                Draw-FullSettingsInterface $settingItems $selectedIndex $config
                $needFullRedraw = $false
            }

            # 处理用户输入
            $key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            switch ($key.VirtualKeyCode) {
                38 { # Up Arrow
                    $oldIndex = $selectedIndex
                    $selectedIndex = if ($selectedIndex -gt 0) { $selectedIndex - 1 } else { $settingItems.Count - 1 }
                    if ($oldIndex -ne $selectedIndex) {
                        Update-SettingSelection $settingItems $oldIndex $selectedIndex $config
                    }
                }
                40 { # Down Arrow
                    $oldIndex = $selectedIndex
                    $selectedIndex = if ($selectedIndex -lt ($settingItems.Count - 1)) { $selectedIndex + 1 } else { 0 }
                    if ($oldIndex -ne $selectedIndex) {
                        Update-SettingSelection $settingItems $oldIndex $selectedIndex $config
                    }
                }
                13 { # Enter - 修改设置项
                    $selectedItem = $settingItems[$selectedIndex]
                    $currentValue = if ($config.ContainsKey($selectedItem.Key)) { $config[$selectedItem.Key] } else { $selectedItem.DefaultValue }

                    # 检查设置项类型，使用对应的左右切换界面
                    if ($selectedItem.IsManualMode) {
                        # 手动模式选择器
                        $result = Show-ManualModeSelector $selectedItem $currentValue
                        if ($result -ne $null) {
                            $updateResult = Update-EnvConfig $selectedItem.Key $result
                            if ($updateResult) {
                                Write-Host "✅ 注册模式已更新为: $(if ($result -eq 'true') { '手动化' } else { '自动化' })" -ForegroundColor Green
                                Start-Sleep -Seconds 1
                            }
                        }
                        $needFullRedraw = $true
                    } elseif ($selectedItem.IsChoice) {
                        # 登录方式选择器
                        $result = Show-LoginMethodSelector $selectedItem $currentValue
                        if ($result -ne $null) {
                            $updateResult = Update-EnvConfig $selectedItem.Key $result
                            if ($updateResult) {
                                $methodNames = @{1 = 'Google'; 2 = 'GitHub'; 3 = 'AWS Builder ID'}
                                $methodName = $methodNames[[int]$result]
                                Write-Host "✅ 默认登录方式已更新为: $result ($methodName)" -ForegroundColor Green
                                Start-Sleep -Seconds 1
                            }
                        }
                        $needFullRedraw = $true
                    } else {
                        # 原有的文本输入方式（用于其他设置项）
                        Clear-Host
                        Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
                        Write-Host "║                      修改设置项                              ║" -ForegroundColor Cyan
                        Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
                        Write-Host ""
                        Write-Host "设置项: " -NoNewline -ForegroundColor White
                        Write-Host "$($selectedItem.Name)" -ForegroundColor Yellow
                        Write-Host "当前值: " -NoNewline -ForegroundColor White

                        if ($selectedItem.IsPassword -and $currentValue -ne $selectedItem.DefaultValue) {
                            Write-Host ($currentValue.Substring(0, [Math]::Min(4, $currentValue.Length)) + "****") -ForegroundColor Yellow
                        } else {
                            Write-Host "$currentValue" -ForegroundColor Yellow
                        }

                        Write-Host ""

                        Write-Host "请输入新值 (直接回车保持不变): " -NoNewline -ForegroundColor White
                        $newValue = Read-Host

                        if (![string]::IsNullOrWhiteSpace($newValue)) {
                            # 特殊处理：如果是邮箱设置，需要同时更新相关项
                            if ($selectedItem.Key -eq "IMAP_USER") {
                                $emailParts = $newValue -split "@"
                                if ($emailParts.Count -eq 2) {
                                    $emailProvider = $emailParts[1].ToLower()
                                    $imapServer = switch ($emailProvider) {
                                        "qq.com" { "imap.qq.com" }
                                        "163.com" { "imap.163.com" }
                                        "126.com" { "imap.126.com" }
                                        "gmail.com" { "imap.gmail.com" }
                                        "outlook.com" { "imap-mail.outlook.com" }
                                        "hotmail.com" { "imap-mail.outlook.com" }
                                        default { "imap.$emailProvider" }
                                    }
                                    Update-EnvConfig "IMAP_SERVER" $imapServer
                                }
                            }

                            # 更新主要设置项
                            $updateResult = Update-EnvConfig $selectedItem.Key $newValue

                            if ($updateResult) {
                                Write-Host "✅ 设置已更新！" -ForegroundColor Green
                            } else {
                                Write-Host "❌ 更新失败！" -ForegroundColor Red
                            }
                        } else {
                            Write-Host "⚪ 保持原值不变" -ForegroundColor Gray
                        }

                        Write-Host ""
                        Write-Host "按任意键返回设置菜单..." -ForegroundColor Yellow
                        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                        $needFullRedraw = $true
                    }
                }
                27 { # ESC
                    return  # 返回主菜单
                }
            }
        }
    }
    finally {
        # 恢复光标显示
        [Console]::CursorVisible = $true
    }
}

# ==================== 固化环境检查和创建逻辑 ====================

# 检查固化环境是否就绪
function Test-PythonEnvironmentReady {
    $pythonEnvPath = "$PSScriptRoot\python_env"
    $pythonExePath = "$pythonEnvPath\python.exe"

    # 检查基本结构
    if (!(Test-Path $pythonEnvPath)) {
        return $false
    }

    if (!(Test-Path $pythonExePath)) {
        return $false
    }

    # 检查关键库是否安装（包括Tkinter）
    try {
        $testResult = & $pythonExePath -c "import pywinauto, selenium, requests; print('OK')" 2>$null
        $tkinterResult = & $pythonExePath -c "import tkinter; print('TKINTER_OK')" 2>$null
        return ($testResult -eq "OK" -and $tkinterResult -eq "TKINTER_OK")
    } catch {
        return $false
    }
}

# 创建固化的便携版 Python 环境
function Initialize-PythonEnvironment {
    param(
        [string]$TargetPath = "$PSScriptRoot\python_env"
    )

    Write-Host "`n╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                    首次环境初始化                            ║" -ForegroundColor Cyan
    Write-Host "╠══════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
    Write-Host "║  正在创建固化的 Python 环境，这个过程只需要执行一次...       ║" -ForegroundColor Yellow
    Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""

    # 清理可能存在的不完整环境
    if (Test-Path $TargetPath) {
        Write-Host "🧹 清理现有的不完整环境..." -ForegroundColor Yellow
        Remove-Item -Path $TargetPath -Recurse -Force -ErrorAction SilentlyContinue
    }

    # 创建目标目录
    New-Item -ItemType Directory -Path $TargetPath -Force | Out-Null
    Write-Host "📁 创建环境目录: $TargetPath" -ForegroundColor Green

    # 步骤1: 下载WinPython便携版（包含Tkinter）
    Write-Host "`n[1/4] 📥 下载 WinPython 3.13.7 便携版（包含Tkinter GUI支持）..." -ForegroundColor Yellow
    $exeUrl = "https://github.com/winpython/winpython/releases/download/17.2.20250920final/WinPython64-3.13.7.0dot.exe"
    $exePath = "$env:TEMP\winpython-$(Get-Random).exe"

    $downloadSuccess = $false
    $maxAttempts = 3

    for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
        try {
            Write-Host "  📡 尝试 $attempt/$maxAttempts : 下载WinPython中..." -ForegroundColor Cyan
            Invoke-WebRequest -Uri $exeUrl -OutFile $exePath -UseBasicParsing -TimeoutSec 300 -ErrorAction Stop

            $fileSize = [math]::Round((Get-Item $exePath).Length / 1MB, 2)
            if ($fileSize -gt 15) {
                Write-Host "  ✅ WinPython下载完成! (大小: ${fileSize} MB，包含Tkinter)" -ForegroundColor Green
                $downloadSuccess = $true
                break
            } else {
                throw "文件大小异常 (${fileSize} MB)"
            }
        } catch {
            Write-Host "  ❌ 下载失败: $($_.Exception.Message)" -ForegroundColor Red
            if (Test-Path $exePath) { Remove-Item $exePath -Force -ErrorAction SilentlyContinue }
            if ($attempt -lt $maxAttempts) {
                Write-Host "  ⏳ 10秒后重试..." -ForegroundColor Yellow
                Start-Sleep -Seconds 10
            }
        }
    }

    if (-not $downloadSuccess) {
        throw "WinPython 便携版下载失败，请检查网络连接"
    }

    # 步骤2: 解压 WinPython（自解压exe）
    Write-Host "`n[2/4] 📦 解压 WinPython 到固化目录..." -ForegroundColor Yellow
    try {
        Write-Host "  🔧 执行WinPython自解压..." -ForegroundColor Cyan

        # 创建临时解压目录
        $tempExtractPath = "$env:TEMP\winpython_extract_$(Get-Random)"
        New-Item -ItemType Directory -Path $tempExtractPath -Force | Out-Null
        Write-Host "    📁 临时解压目录: $tempExtractPath" -ForegroundColor Gray

        # WinPython使用7zip自解压格式，尝试多种解压方法
        $extractSuccess = $false

        # 方法1: 尝试7zip风格参数
        try {
            Write-Host "    🔧 尝试方法1: 7zip风格参数..." -ForegroundColor Gray
            $extractProcess = Start-Process -FilePath $exePath -ArgumentList "-o`"$tempExtractPath`"", "-y" -Wait -PassThru -WindowStyle Hidden
            if ($extractProcess.ExitCode -eq 0) {
                $extractSuccess = $true
                Write-Host "    ✅ 方法1成功" -ForegroundColor Green
            } else {
                Write-Host "    ❌ 方法1失败，退出代码: $($extractProcess.ExitCode)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "    ❌ 方法1异常: $($_.Exception.Message)" -ForegroundColor Yellow
        }

        # 方法2: 尝试NSIS风格参数
        if (-not $extractSuccess) {
            try {
                Write-Host "    🔧 尝试方法2: NSIS风格参数..." -ForegroundColor Gray
                $extractProcess = Start-Process -FilePath $exePath -ArgumentList "/S", "/D=`"$tempExtractPath`"" -Wait -PassThru -WindowStyle Hidden
                if ($extractProcess.ExitCode -eq 0) {
                    $extractSuccess = $true
                    Write-Host "    ✅ 方法2成功" -ForegroundColor Green
                } else {
                    Write-Host "    ❌ 方法2失败，退出代码: $($extractProcess.ExitCode)" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "    ❌ 方法2异常: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }

        # 方法3: 尝试直接执行到当前目录
        if (-not $extractSuccess) {
            try {
                Write-Host "    🔧 尝试方法3: 直接执行..." -ForegroundColor Gray
                Set-Location $tempExtractPath
                $extractProcess = Start-Process -FilePath $exePath -Wait -PassThru -WindowStyle Hidden
                Set-Location $PSScriptRoot
                if ($extractProcess.ExitCode -eq 0) {
                    $extractSuccess = $true
                    Write-Host "    ✅ 方法3成功" -ForegroundColor Green
                } else {
                    Write-Host "    ❌ 方法3失败，退出代码: $($extractProcess.ExitCode)" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "    ❌ 方法3异常: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }

        # 方法4: 尝试使用cmd执行
        if (-not $extractSuccess) {
            try {
                Write-Host "    🔧 尝试方法4: CMD执行..." -ForegroundColor Gray
                $cmdArgs = "/c `"$exePath`" -o`"$tempExtractPath`" -y"
                $extractProcess = Start-Process -FilePath "cmd.exe" -ArgumentList $cmdArgs -Wait -PassThru -WindowStyle Hidden
                if ($extractProcess.ExitCode -eq 0) {
                    $extractSuccess = $true
                    Write-Host "    ✅ 方法4成功" -ForegroundColor Green
                } else {
                    Write-Host "    ❌ 方法4失败，退出代码: $($extractProcess.ExitCode)" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "    ❌ 方法4异常: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }

        # 检查解压结果
        Write-Host "  🔍 检查解压结果..." -ForegroundColor Cyan
        Start-Sleep -Seconds 2  # 等待文件系统同步

        # 列出临时目录内容进行调试
        $tempContents = Get-ChildItem -Path $tempExtractPath -ErrorAction SilentlyContinue
        Write-Host "    📂 临时目录内容: $($tempContents.Count) 个项目" -ForegroundColor Gray

        if ($tempContents.Count -gt 0) {
            foreach ($item in $tempContents | Select-Object -First 10) {
                $itemType = if ($item.PSIsContainer) { "目录" } else { "文件" }
                Write-Host "      - $($item.Name) ($itemType)" -ForegroundColor Gray
            }
            if ($tempContents.Count -gt 10) {
                Write-Host "      ... 还有 $($tempContents.Count - 10) 个项目" -ForegroundColor Gray
            }
        }

        # 智能查找Python目录
        $pythonFound = $false

        # 策略1: 查找WinPython目录结构
        $winPythonDirs = Get-ChildItem -Path $tempExtractPath -Directory -ErrorAction SilentlyContinue | Where-Object {
            $_.Name -like "WinPython*" -or $_.Name -like "*python*"
        }

        foreach ($winPythonDir in $winPythonDirs) {
            Write-Host "    🔍 检查WinPython目录: $($winPythonDir.Name)" -ForegroundColor Gray

            # 查找python-*子目录
            $pythonSubDirs = Get-ChildItem -Path $winPythonDir.FullName -Directory -ErrorAction SilentlyContinue | Where-Object {
                $_.Name -like "python-*" -or (Test-Path "$($_.FullName)\python.exe")
            }

            if ($pythonSubDirs.Count -gt 0) {
                $pythonDir = $pythonSubDirs[0]
                Write-Host "    ✅ 找到Python目录: $($pythonDir.FullName)" -ForegroundColor Green

                # 复制Python目录到目标位置
                Copy-Item -Path "$($pythonDir.FullName)\*" -Destination $TargetPath -Recurse -Force
                Write-Host "  ✅ WinPython 解压完成（包含Tkinter支持）" -ForegroundColor Green
                $pythonFound = $true
                break
            }
        }

        # 策略2: 直接查找python.exe
        if (-not $pythonFound) {
            Write-Host "    🔍 策略2: 递归查找python.exe..." -ForegroundColor Gray
            $pythonExes = Get-ChildItem -Path $tempExtractPath -Recurse -Filter "python.exe" -ErrorAction SilentlyContinue | Select-Object -First 1

            if ($pythonExes) {
                $pythonDir = $pythonExes.Directory
                Write-Host "    ✅ 找到Python目录: $($pythonDir.FullName)" -ForegroundColor Green

                # 复制Python目录到目标位置
                Copy-Item -Path "$($pythonDir.FullName)\*" -Destination $TargetPath -Recurse -Force
                Write-Host "  ✅ WinPython 解压完成（包含Tkinter支持）" -ForegroundColor Green
                $pythonFound = $true
            }
        }

        # 策略3: 检查是否直接解压到了临时目录
        if (-not $pythonFound) {
            Write-Host "    🔍 策略3: 检查直接解压..." -ForegroundColor Gray
            if (Test-Path "$tempExtractPath\python.exe") {
                Write-Host "    ✅ 找到直接解压的Python" -ForegroundColor Green
                Copy-Item -Path "$tempExtractPath\*" -Destination $TargetPath -Recurse -Force
                Write-Host "  ✅ WinPython 解压完成（包含Tkinter支持）" -ForegroundColor Green
                $pythonFound = $true
            }
        }

        if (-not $pythonFound) {
            # 提供详细的调试信息
            Write-Host "  ❌ 未找到Python目录，调试信息:" -ForegroundColor Red
            Write-Host "    - 解压成功: $extractSuccess" -ForegroundColor Gray
            Write-Host "    - 临时目录: $tempExtractPath" -ForegroundColor Gray
            Write-Host "    - 目录内容数量: $($tempContents.Count)" -ForegroundColor Gray

            if ($tempContents.Count -gt 0) {
                Write-Host "    - 主要内容:" -ForegroundColor Gray
                $tempContents | Select-Object -First 5 | ForEach-Object {
                    Write-Host "      * $($_.Name)" -ForegroundColor Gray
                }
            }

            throw "未找到Python目录或python.exe文件"
        }

        # 清理临时文件
        Remove-Item $exePath -Force -ErrorAction SilentlyContinue
        Remove-Item $tempExtractPath -Recurse -Force -ErrorAction SilentlyContinue

    } catch {
        # 提供更详细的错误信息
        Write-Host "  ❌ 解压过程详细错误信息:" -ForegroundColor Red
        Write-Host "    错误: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "    下载文件: $exePath" -ForegroundColor Gray
        Write-Host "    文件存在: $(Test-Path $exePath)" -ForegroundColor Gray
        Write-Host "    临时目录: $tempExtractPath" -ForegroundColor Gray

        if (Test-Path $tempExtractPath) {
            $debugContents = Get-ChildItem -Path $tempExtractPath -ErrorAction SilentlyContinue
            Write-Host "    临时目录内容: $($debugContents.Count) 个项目" -ForegroundColor Gray
        }

        throw "WinPython 解压失败: $($_.Exception.Message)"
    }

    # 步骤3: 验证 WinPython 环境
    Write-Host "`n[3/4] ⚙️  验证 WinPython 环境..." -ForegroundColor Yellow
    try {
        $pythonExe = "$TargetPath\python.exe"

        if (Test-Path $pythonExe) {
            Write-Host "  ✅ Python 可执行文件已就绪" -ForegroundColor Green

            # 验证Tkinter支持
            $tkinterTest = & $pythonExe -c "import tkinter; print('Tkinter可用')" 2>$null
            if ($tkinterTest -eq "Tkinter可用") {
                Write-Host "  ✅ Tkinter GUI支持已确认" -ForegroundColor Green
            } else {
                Write-Host "  ⚠️  Tkinter验证失败，但继续..." -ForegroundColor Yellow
            }

            # 验证pip支持
            $pipTest = & $pythonExe -m pip --version 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ pip 包管理器已就绪" -ForegroundColor Green
            } else {
                Write-Host "  ⚠️  pip验证失败，但继续..." -ForegroundColor Yellow
            }
        } else {
            throw "Python可执行文件未找到"
        }
    } catch {
        throw "WinPython 环境验证失败: $($_.Exception.Message)"
    }

    # 步骤4: 安装必要的库
    Write-Host "`n[4/4] 📚 安装必要的 Python 库..." -ForegroundColor Yellow
    $libraries = @("pywinauto", "selenium", "webdriver-manager", "requests", "psutil")
    $pythonExe = "$TargetPath\python.exe"

    foreach ($lib in $libraries) {
        try {
            Write-Host "  📦 安装 $lib..." -ForegroundColor Cyan
            & $pythonExe -m pip install $lib --quiet --no-warn-script-location --disable-pip-version-check

            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ $lib 安装成功" -ForegroundColor Green
            } else {
                Write-Host "  ⚠️  $lib 安装可能有问题，但继续..." -ForegroundColor Yellow
            }
        } catch {
            Write-Host "  ❌ $lib 安装失败: $($_.Exception.Message)" -ForegroundColor Red
        }
    }

    # 验证环境完整性
    Write-Host "`n🔍 验证固化环境..." -ForegroundColor Yellow
    try {
        # 验证基础库
        $testResult = & $pythonExe -c "import pywinauto, selenium, requests; print('VALIDATION_SUCCESS')" 2>$null
        $tkinterResult = & $pythonExe -c "import tkinter; print('TKINTER_SUCCESS')" 2>$null

        if ($testResult -match "VALIDATION_SUCCESS") {
            Write-Host "✅ 基础库验证成功！" -ForegroundColor Green

            if ($tkinterResult -match "TKINTER_SUCCESS") {
                Write-Host "✅ Tkinter GUI支持验证成功！" -ForegroundColor Green
                Write-Host "🎛️ 控制面板功能将完全可用！" -ForegroundColor Cyan
            } else {
                Write-Host "⚠️  Tkinter验证失败，控制面板可能不可用" -ForegroundColor Yellow
            }

            # 显示环境信息
            $envSize = [math]::Round((Get-ChildItem $TargetPath -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
            Write-Host "📊 环境大小: ${envSize} MB" -ForegroundColor Cyan
            Write-Host "📍 环境路径: $TargetPath" -ForegroundColor Cyan
            Write-Host "🎉 WinPython固化环境创建完成，包含完整GUI支持！" -ForegroundColor Green

            return $true
        } else {
            throw "基础库验证失败"
        }
    } catch {
        throw "环境验证失败: $($_.Exception.Message)"
    }
}

# 智能环境检查和初始化
function Ensure-PythonEnvironment {
    Write-Host "`n🔍 检查固化 Python 环境..." -ForegroundColor Yellow

    if (Test-PythonEnvironmentReady) {
        Write-Host "✅ 固化 Python 环境已就绪，跳过初始化" -ForegroundColor Green

        # 显示环境信息
        $pythonEnvPath = "$PSScriptRoot\python_env"
        $envSize = [math]::Round((Get-ChildItem $pythonEnvPath -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
        Write-Host "📊 环境大小: ${envSize} MB" -ForegroundColor Cyan
        Write-Host "📍 环境路径: $pythonEnvPath" -ForegroundColor Cyan

        return $true
    } else {
        Write-Host "⚠️  固化 Python 环境未就绪，开始初始化..." -ForegroundColor Yellow

        try {
            $result = Initialize-PythonEnvironment
            if ($result) {
                Write-Host "`n🎉 固化环境初始化完成！" -ForegroundColor Green
                Write-Host "🔄 自动返回主菜单..." -ForegroundColor Cyan
                Start-Sleep -Seconds 2  # 给用户2秒时间看到成功信息
                return $true
            } else {
                throw "初始化返回失败"
            }
        } catch {
            Write-Host "`n❌ 固化环境初始化失败: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "💡 您可以选择：" -ForegroundColor Yellow
            Write-Host "   1. 检查网络连接后重试" -ForegroundColor Gray
            Write-Host "   2. 手动下载 Python 便携版到 python_env 目录" -ForegroundColor Gray
            Write-Host "   3. 使用传统模式（每次在沙盒内安装）" -ForegroundColor Gray
            Write-Host "`n按任意键返回主菜单..." -ForegroundColor Yellow
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            return $false
        }
    }
}

# 主菜单函数 - 无闪烁版本
function Show-MainMenu {
    $menuItems = @(
        @{ Text = "续杯模式 - 启动沙盒并注册新账号"; Action = "sandbox" },
        @{ Text = "账号管理 - 管理已保存的账号配置"; Action = "account" },
        @{ Text = "系统设置 - 配置邮箱和登录方式"; Action = "settings" },
        @{ Text = "退出程序"; Action = "exit" }
    )
    $selectedIndex = 0
    $needFullRedraw = $true
    $headerHeight = 6  # 头部占用行数

    # 隐藏光标
    [Console]::CursorVisible = $false

    # 绘制单个菜单项
    function Draw-MenuItem($item, $index, $isSelected) {
        $lineY = $headerHeight + $index
        [Console]::SetCursorPosition(0, $lineY)

        if ($isSelected) {
            Write-Host "  ► " -ForegroundColor Green -NoNewline
            Write-Host "$($item.Text)" -ForegroundColor Yellow
        } else {
            Write-Host "    " -NoNewline
            Write-Host "$($item.Text)" -ForegroundColor White
        }
    }

    # 局部更新选择
    function Update-MenuSelection($menuItems, $oldIndex, $newIndex) {
        # 重绘旧选中项（变为非选中状态）
        if ($oldIndex -ge 0 -and $oldIndex -lt $menuItems.Count) {
            Draw-MenuItem $menuItems[$oldIndex] $oldIndex $false
        }

        # 重绘新选中项（变为选中状态）
        if ($newIndex -ge 0 -and $newIndex -lt $menuItems.Count) {
            Draw-MenuItem $menuItems[$newIndex] $newIndex $true
        }
    }

    # 完整界面绘制
    function Draw-FullMenu($menuItems, $selectedIndex) {
        Clear-Host
        Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
        Write-Host "║                    Kiro 自动化沙盒管理系统                    ║" -ForegroundColor Cyan
        Write-Host "╠══════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
        Write-Host "║  使用 ↑↓ 选择选项，Enter 确认                                ║" -ForegroundColor Yellow
        Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
        Write-Host ""

        # 显示所有菜单选项
        for ($i = 0; $i -lt $menuItems.Count; $i++) {
            Draw-MenuItem $menuItems[$i] $i ($i -eq $selectedIndex)
        }

        Write-Host ""
        Write-Host ""

        # 底部作者信息
        Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor DarkGray
        Write-Host "║                     作者：simtel@qq.com                      ║" -ForegroundColor DarkGray
        Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor DarkGray
    }

    try {
        while ($true) {
            # 首次进入时完整绘制
            if ($needFullRedraw) {
                Draw-FullMenu $menuItems $selectedIndex
                $needFullRedraw = $false
            }

            # 处理用户输入
            $key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            switch ($key.VirtualKeyCode) {
                38 { # Up Arrow - 局部更新
                    $oldIndex = $selectedIndex
                    $selectedIndex = if ($selectedIndex -gt 0) { $selectedIndex - 1 } else { $menuItems.Count - 1 }
                    if ($oldIndex -ne $selectedIndex) {
                        Update-MenuSelection $menuItems $oldIndex $selectedIndex
                    }
                }
                40 { # Down Arrow - 局部更新
                    $oldIndex = $selectedIndex
                    $selectedIndex = if ($selectedIndex -lt ($menuItems.Count - 1)) { $selectedIndex + 1 } else { 0 }
                    if ($oldIndex -ne $selectedIndex) {
                        Update-MenuSelection $menuItems $oldIndex $selectedIndex
                    }
                }
                13 { # Enter
                    return $menuItems[$selectedIndex].Action
                }
                27 { # ESC - 也可以退出
                    return "exit"
                }
            }
        }
    }
    finally {
        # 恢复光标显示
        [Console]::CursorVisible = $true
    }
}

# 账号管理主函数 - 无闪烁版本
function Show-AccountManager {
    $selectedIndex = 0
    $lastRefreshTime = Get-Date
    $refreshInterval = 5  # 5秒刷新间隔，保持账号监控功能
    $lastAccountCount = -1
    $needFullRedraw = $true
    $headerHeight = 7  # 头部占用行数
    $footerHeight = 2  # 底部占用行数

    # 隐藏光标，提升视觉效果
    [Console]::CursorVisible = $false

    # 时间格式化辅助函数
    function Format-Time($timeStr) {
        try {
            if ($timeStr -and $timeStr.Length -ge 15) {
                $t = $timeStr -replace "_", " "
                return "$($t.Substring(0,8)) $($t.Substring(9,2)):$($t.Substring(11,2)):$($t.Substring(13,2))"
            }
        } catch {}
        return $timeStr
    }

    # 绘制单行账号信息
    function Draw-AccountLine($account, $index, $isSelected) {
        try {
            $timeFormatted = Format-Time $account.RegisterTime
            $lineY = $headerHeight + $index

            # 检查行号是否在有效范围内
            if ($lineY -ge 0 -and $lineY -lt ([Console]::WindowHeight - 2)) {
                # 定位到指定行
                [Console]::SetCursorPosition(0, $lineY)

                if ($isSelected) {
                    Write-Host "  ► " -ForegroundColor Green -NoNewline
                    Write-Host "[$($index+1)] " -ForegroundColor White -NoNewline
                    Write-Host "$($account.Email) " -ForegroundColor Yellow -NoNewline
                    Write-Host "($($account.AccountType)) " -ForegroundColor Cyan -NoNewline
                    Write-Host "$timeFormatted" -ForegroundColor Gray
                } else {
                    Write-Host "    " -NoNewline
                    Write-Host "[$($index+1)] " -ForegroundColor Gray -NoNewline
                    Write-Host "$($account.Email) " -ForegroundColor White -NoNewline
                    Write-Host "($($account.AccountType)) " -ForegroundColor Gray -NoNewline
                    Write-Host "$timeFormatted" -ForegroundColor DarkGray
                }
            }
        } catch {
            # 如果绘制失败，静默忽略
        }
    }

    # 局部更新：简化版本，直接触发完整重绘
    function Update-Selection($accounts, $oldIndex, $newIndex) {
        # 对于分页显示，始终触发完整重绘以确保正确性
        return $true
    }

    # 更新底部统计信息
    function Update-Footer($accountCount) {
        try {
            $footerY = [Console]::WindowHeight - $footerHeight
            if ($footerY -gt 0 -and $footerY -lt [Console]::WindowHeight) {
                [Console]::SetCursorPosition(0, $footerY)
                Write-Host "总计: $accountCount 个账号" -ForegroundColor Gray
                # 清除可能的多余字符
                Write-Host (" " * 20) -NoNewline
            }
        } catch {
            # 如果设置光标位置失败，直接输出
            Write-Host ""
            Write-Host "总计: $accountCount 个账号" -ForegroundColor Gray
        }
    }

    # 完整界面绘制（仅在必要时使用）
    function Draw-FullInterface($accounts, $selectedIndex) {
        Clear-Host
        Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
        Write-Host "║                        账号管理                              ║" -ForegroundColor Cyan
        Write-Host "╠══════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
        if ($accounts.Count -eq 0) {
            Write-Host "║  暂无已保存的账号配置 - 等待沙盒生成新账号...                ║" -ForegroundColor Yellow
            Write-Host "║  使用 ↑↓ 导航，Enter 操作，ESC 返回主菜单                   ║" -ForegroundColor Gray
        } else {
            Write-Host "║  使用 ↑↓ 选择账号，Enter 进入操作，ESC 返回主菜单            ║" -ForegroundColor Yellow
        }
        Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
        Write-Host ""

        if ($accounts.Count -eq 0) {
            Write-Host "  正在监控 OAuth 文件夹..." -ForegroundColor Gray
            Write-Host "  监控目录: $PSScriptRoot\sandbox_files\OAuth" -ForegroundColor DarkGray
            Write-Host ""
            Write-Host "  [提示] 在沙盒中完成账号注册后，账号配置会自动出现在此列表中" -ForegroundColor Yellow
        } else {
            # 计算可显示的最大账号数量（窗口高度 - 头部 - 底部 - 缓冲）
            $maxVisibleAccounts = [Console]::WindowHeight - $headerHeight - 5

            # 如果账号太多，只显示部分（使用滚动窗口）
            if ($accounts.Count -gt $maxVisibleAccounts) {
                # 简单的滚动逻辑：确保选中项可见
                $startIndex = 0
                $endIndex = $maxVisibleAccounts - 1

                # 如果选中的索引超过当前窗口，向下滚动
                if ($selectedIndex -gt $endIndex) {
                    $endIndex = $selectedIndex
                    $startIndex = [Math]::Max(0, $endIndex - $maxVisibleAccounts + 1)
                }

                # 如果选中的索引在当前窗口之前，向上滚动
                if ($selectedIndex -lt $startIndex) {
                    $startIndex = $selectedIndex
                    $endIndex = [Math]::Min($accounts.Count - 1, $startIndex + $maxVisibleAccounts - 1)
                }

                Write-Host "  显示 $($startIndex + 1)-$($endIndex + 1) / $($accounts.Count) 个账号" -ForegroundColor DarkGray
                Write-Host ""

                # 显示可见范围内的账号
                for ($i = $startIndex; $i -le $endIndex; $i++) {
                    $timeFormatted = Format-Time $accounts[$i].RegisterTime
                    if ($i -eq $selectedIndex) {
                        Write-Host "  ► " -ForegroundColor Green -NoNewline
                        Write-Host "[$($i+1)] " -ForegroundColor White -NoNewline
                        Write-Host "$($accounts[$i].Email) " -ForegroundColor Yellow -NoNewline
                        Write-Host "($($accounts[$i].AccountType)) " -ForegroundColor Cyan -NoNewline
                        Write-Host "$timeFormatted" -ForegroundColor Gray
                    } else {
                        Write-Host "    " -NoNewline
                        Write-Host "[$($i+1)] " -ForegroundColor Gray -NoNewline
                        Write-Host "$($accounts[$i].Email) " -ForegroundColor White -NoNewline
                        Write-Host "($($accounts[$i].AccountType)) " -ForegroundColor Gray -NoNewline
                        Write-Host "$timeFormatted" -ForegroundColor DarkGray
                    }
                }
            } else {
                # 账号数量不多，全部显示
                for ($i = 0; $i -lt $accounts.Count; $i++) {
                    $timeFormatted = Format-Time $accounts[$i].RegisterTime
                    if ($i -eq $selectedIndex) {
                        Write-Host "  ► " -ForegroundColor Green -NoNewline
                        Write-Host "[$($i+1)] " -ForegroundColor White -NoNewline
                        Write-Host "$($accounts[$i].Email) " -ForegroundColor Yellow -NoNewline
                        Write-Host "($($accounts[$i].AccountType)) " -ForegroundColor Cyan -NoNewline
                        Write-Host "$timeFormatted" -ForegroundColor Gray
                    } else {
                        Write-Host "    " -NoNewline
                        Write-Host "[$($i+1)] " -ForegroundColor Gray -NoNewline
                        Write-Host "$($accounts[$i].Email) " -ForegroundColor White -NoNewline
                        Write-Host "($($accounts[$i].AccountType)) " -ForegroundColor Gray -NoNewline
                        Write-Host "$timeFormatted" -ForegroundColor DarkGray
                    }
                }
            }
        }

        Write-Host ""
        Write-Host "总计: $($accounts.Count) 个账号" -ForegroundColor Gray
    }

    try {
        while ($true) {
            $currentTime = Get-Date
            $accounts = Get-AccountList

            # 确保 accounts 始终是数组
            if ($accounts -eq $null) {
                $accounts = @()
            } elseif ($accounts -isnot [Array]) {
                $accounts = @($accounts)
            }

            # 检查是否需要完整重绘
            $shouldFullRedraw = $false

            # 账号数量变化时需要完整重绘
            if ($accounts.Count -ne $lastAccountCount) {
                $shouldFullRedraw = $true
                $lastAccountCount = $accounts.Count
            }

            # 每5秒定时刷新（保持监控功能）
            if (($currentTime - $lastRefreshTime).TotalSeconds -ge $refreshInterval) {
                $shouldFullRedraw = $true
                $lastRefreshTime = $currentTime
            }

            # 首次进入或需要完整重绘
            if ($needFullRedraw) {
                $shouldFullRedraw = $true
                $needFullRedraw = $false
            }

            # 调整选中索引，防止越界
            if ($accounts.Count -eq 0) {
                $selectedIndex = 0
            } elseif ($selectedIndex -ge $accounts.Count) {
                $selectedIndex = $accounts.Count - 1
            }

            # 执行重绘
            if ($shouldFullRedraw) {
                Draw-FullInterface $accounts $selectedIndex
            }

            # 检查用户输入（非阻塞）
            if ($Host.UI.RawUI.KeyAvailable) {
                $key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                switch ($key.VirtualKeyCode) {
                    38 { # Up Arrow - 局部更新
                        if ($accounts.Count -gt 0) {
                            $oldIndex = $selectedIndex
                            $selectedIndex = if ($selectedIndex -gt 0) { $selectedIndex - 1 } else { $accounts.Count - 1 }
                            if ($oldIndex -ne $selectedIndex) {
                                $needRedraw = Update-Selection $accounts $oldIndex $selectedIndex
                                if ($needRedraw) {
                                    $needFullRedraw = $true
                                }
                            }
                        }
                    }
                    40 { # Down Arrow - 局部更新
                        if ($accounts.Count -gt 0) {
                            $oldIndex = $selectedIndex
                            $selectedIndex = if ($selectedIndex -lt ($accounts.Count - 1)) { $selectedIndex + 1 } else { 0 }
                            if ($oldIndex -ne $selectedIndex) {
                                $needRedraw = Update-Selection $accounts $oldIndex $selectedIndex
                                if ($needRedraw) {
                                    $needFullRedraw = $true
                                }
                            }
                        }
                    }
                    13 { # Enter
                        if ($accounts.Count -gt 0) {
                            # 恢复光标显示，因为要进入子菜单
                            [Console]::CursorVisible = $true

                            $selectedAccount = $accounts[$selectedIndex]
                            $action = Show-AccountActions $selectedAccount

                            switch ($action) {
                                "apply" {
                                    Apply-Account $selectedAccount
                                    Write-Host ""
                                    Write-Host "账号应用完成！按任意键继续..." -ForegroundColor Green
                                    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                                    $needFullRedraw = $true
                                }
                                "compress" {
                                    Compress-Account $selectedAccount
                                    Write-Host ""
                                    Write-Host "账号压缩分享完成！按任意键继续..." -ForegroundColor Green
                                    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                                    $needFullRedraw = $true
                                }
                                "info" {
                                    Show-AccountInfo $selectedAccount
                                    Write-Host ""
                                    Write-Host "按任意键继续..." -ForegroundColor Gray
                                    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                                    $needFullRedraw = $true
                                }
                                "back" {
                                    $needFullRedraw = $true
                                }
                            }

                            # 清空键盘缓冲区，防止残留按键干扰
                            while ($Host.UI.RawUI.KeyAvailable) {
                                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
                            }

                            # 重新隐藏光标
                            [Console]::CursorVisible = $false
                        }
                    }
                    27 { # ESC
                        return  # 返回主菜单
                    }
                }
            }

            # 短暂休眠以减少CPU占用
            Start-Sleep -Milliseconds 50
        }
    }
    finally {
        # 恢复光标显示
        [Console]::CursorVisible = $true
    }
}

# 获取账号列表
function Get-AccountList {
    $oauthDir = "$PSScriptRoot\sandbox_files\OAuth"
    if (!(Test-Path $oauthDir)) {
        return @()
    }

    $jsonFiles = Get-ChildItem -Path $oauthDir -Filter "*.json" -ErrorAction SilentlyContinue
    $accounts = @()

    foreach ($file in $jsonFiles) {
        # 检查文件名是否包含双下划线（新格式）
        if ($file.Name -match "__") {
            # 新格式：原文件名__邮箱__账号类型__时间.json
            # 例如：kiro-auth-token__block_height@kt167.lol__github__20251029_190554.json
            if ($file.Name -match "^(.+?)__(.+?)__([^_]+?)__(\d{8}_\d{6})\.json$") {
                $account = [PSCustomObject]@{
                    FileName = $file.Name
                    OriginalName = $matches[1]
                    Email = $matches[2]
                    AccountType = $matches[3]
                    RegisterTime = $matches[4]
                    FilePath = $file.FullName
                }
                $accounts += $account
            }
        }
    }

    # 确保始终返回数组，即使只有一个元素
    $sortedAccounts = $accounts | Sort-Object RegisterTime -Descending
    return @($sortedAccounts)
}


# 显示账号操作选择 - 无闪烁版本
function Show-AccountActions($account) {
    $actions = @("apply", "compress", "info")
    $actionNames = @("应用", "压缩分享", "查看信息")
    $selectedAction = 0
    $needFullRedraw = $true
    $actionLineY = 9  # 操作选项所在行

    # 隐藏光标
    [Console]::CursorVisible = $false

    # 绘制操作选项行
    function Draw-ActionLine($actions, $actionNames, $selectedAction) {
        [Console]::SetCursorPosition(0, $actionLineY)
        Write-Host "  "  -NoNewline
        for ($i = 0; $i -lt $actions.Count; $i++) {
            if ($i -eq $selectedAction) {
                Write-Host "[ $($actionNames[$i]) ]" -ForegroundColor Black -BackgroundColor Yellow -NoNewline
            } else {
                Write-Host "  $($actionNames[$i])  " -ForegroundColor Gray -NoNewline
            }
            Write-Host "  " -NoNewline
        }
        # 清除行尾可能的残留字符
        Write-Host (" " * 10)
    }

    # 局部更新操作选择
    function Update-ActionSelection($actions, $actionNames, $oldAction, $newAction) {
        if ($oldAction -ne $newAction) {
            Draw-ActionLine $actions $actionNames $newAction
        }
    }

    # 完整界面绘制
    function Draw-FullActionInterface($account, $actions, $actionNames, $selectedAction) {
        Clear-Host
        Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
        Write-Host "║                      账号操作选择                            ║" -ForegroundColor Cyan
        Write-Host "╠══════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
        Write-Host "║  使用 ←→ 选择操作，Enter 确认，ESC 返回                      ║" -ForegroundColor Yellow
        Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
        Write-Host ""

        Write-Host "选中账号: " -ForegroundColor White -NoNewline
        Write-Host "$($account.Email) " -ForegroundColor Yellow -NoNewline
        Write-Host "($($account.AccountType))" -ForegroundColor Cyan
        Write-Host ""

        # 绘制操作选项
        Draw-ActionLine $actions $actionNames $selectedAction
    }

    try {
        while ($true) {
            # 首次进入时完整绘制
            if ($needFullRedraw) {
                Draw-FullActionInterface $account $actions $actionNames $selectedAction
                $needFullRedraw = $false
            }

            $key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            switch ($key.VirtualKeyCode) {
                37 { # Left Arrow - 局部更新
                    $oldAction = $selectedAction
                    $selectedAction = if ($selectedAction -gt 0) { $selectedAction - 1 } else { $actions.Count - 1 }
                    Update-ActionSelection $actions $actionNames $oldAction $selectedAction
                }
                39 { # Right Arrow - 局部更新
                    $oldAction = $selectedAction
                    $selectedAction = if ($selectedAction -lt ($actions.Count - 1)) { $selectedAction + 1 } else { 0 }
                    Update-ActionSelection $actions $actionNames $oldAction $selectedAction
                }
                13 { # Enter
                    return $actions[$selectedAction]
                }
                27 { # ESC
                    return "back"
                }
            }
        }
    }
    finally {
        # 恢复光标显示
        [Console]::CursorVisible = $true
    }
}

# 应用账号配置
function Apply-Account($account) {
    Write-Host "正在应用账号配置: $($account.Email)..." -ForegroundColor Yellow

    # 备份并清空 AWS SSO Cache
    $awsSsoCacheDir = "$env:USERPROFILE\.aws\sso\cache"

    if (Test-Path $awsSsoCacheDir) {
        $awsSsoJsonFiles = Get-ChildItem -Path $awsSsoCacheDir -Filter "*.json" -ErrorAction SilentlyContinue
        if ($awsSsoJsonFiles.Count -gt 0) {
            Write-Host "正在备份 AWS SSO Cache 中的 $($awsSsoJsonFiles.Count) 个 JSON 文件..." -ForegroundColor Yellow

            $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
            $backupZipPath = "$awsSsoCacheDir\aws_sso_backup_$timestamp.zip"

            try {
                $awsSsoJsonFiles | Compress-Archive -DestinationPath $backupZipPath -Force
                Write-Host "AWS SSO Cache 备份完成: $backupZipPath" -ForegroundColor Green

                # 删除原始JSON文件
                foreach ($file in $awsSsoJsonFiles) {
                    Remove-Item -Path $file.FullName -Force
                    Write-Host "已删除 AWS SSO Cache 文件: $($file.Name)" -ForegroundColor Cyan
                }
            } catch {
                Write-Host "备份 AWS SSO Cache 文件失败: $($_.Exception.Message)" -ForegroundColor Red
                return
            }
        }
    } else {
        New-Item -ItemType Directory -Path $awsSsoCacheDir -Force -Recurse | Out-Null
        Write-Host "已创建 AWS SSO Cache 目录: $awsSsoCacheDir" -ForegroundColor Yellow
    }

    # 复制选中的账号文件到 AWS SSO Cache 并恢复原始文件名
    $originalFileName = "$($account.OriginalName).json"
    $targetPath = Join-Path $awsSsoCacheDir $originalFileName

    try {
        Copy-Item -Path $account.FilePath -Destination $targetPath -Force
        Write-Host "已应用账号配置: $originalFileName" -ForegroundColor Green

        # 查找同一账号的其他JSON文件（AWS Builder ID注册方式会生成2个JSON）
        # 查找条件：相同邮箱、平台、时间，但文件名不同
        $oauthDir = Split-Path $account.FilePath
        $relatedJsonFiles = Get-ChildItem -Path $oauthDir -Filter "*__$($account.Email)__$($account.AccountType)__$($account.RegisterTime).json" -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -ne $account.FilePath }

        if ($relatedJsonFiles) {
            foreach ($relatedFile in $relatedJsonFiles) {
                # 提取原始文件名（双下划线之前的部分）
                if ($relatedFile.Name -match "^(.+?)__") {
                    $relatedOriginalFileName = "$($matches[1]).json"
                    $relatedTargetPath = Join-Path $awsSsoCacheDir $relatedOriginalFileName
                    Copy-Item -Path $relatedFile.FullName -Destination $relatedTargetPath -Force
                    Write-Host "已应用关联配置文件: $relatedOriginalFileName" -ForegroundColor Green
                }
            }
            Write-Host "账号 $($account.Email) 的所有配置文件已成功应用到 AWS SSO Cache" -ForegroundColor Green
        } else {
            Write-Host "账号 $($account.Email) 已成功应用到 AWS SSO Cache" -ForegroundColor Green
        }
    } catch {
        Write-Host "应用账号配置失败: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 压缩分享账号
function Compress-Account($account) {
    Write-Host "正在压缩账号配置: $($account.Email)..." -ForegroundColor Yellow

    # 获取用户桌面路径
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    Write-Host "目标位置: 桌面 ($desktopPath)" -ForegroundColor Cyan

    # 创建临时目录用于准备文件
    $tempDir = "$env:TEMP\KiroAccountShare_$([System.Guid]::NewGuid().ToString('N').Substring(0,8))"
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

    try {
        # 1. 复制并重命名JSON文件为原始文件名
        $originalFileName = "$($account.OriginalName).json"
        $tempJsonPath = Join-Path $tempDir $originalFileName
        Copy-Item -Path $account.FilePath -Destination $tempJsonPath -Force
        Write-Host "已准备JSON文件: $originalFileName" -ForegroundColor Cyan

        # 查找同一账号的其他JSON文件（AWS Builder ID注册方式会生成2个JSON）
        $oauthDir = Split-Path $account.FilePath
        $relatedJsonFiles = Get-ChildItem -Path $oauthDir -Filter "*__$($account.Email)__$($account.AccountType)__$($account.RegisterTime).json" -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -ne $account.FilePath }

        $jsonFilesList = @($originalFileName)
        if ($relatedJsonFiles) {
            foreach ($relatedFile in $relatedJsonFiles) {
                # 提取原始文件名（双下划线之前的部分）
                if ($relatedFile.Name -match "^(.+?)__") {
                    $relatedOriginalFileName = "$($matches[1]).json"
                    $tempRelatedJsonPath = Join-Path $tempDir $relatedOriginalFileName
                    Copy-Item -Path $relatedFile.FullName -Destination $tempRelatedJsonPath -Force
                    Write-Host "已准备关联JSON文件: $relatedOriginalFileName" -ForegroundColor Cyan
                    $jsonFilesList += $relatedOriginalFileName
                }
            }
        }

        # 2. 从账号.txt提取账号信息并创建账号信息文件
        $accountInfoPath = Join-Path $tempDir "account_info.txt"
        $accountInfo = Get-AccountInfoFromFile $account.Email

        if ($accountInfo) {
            # 格式化时间显示
            $timeFormatted = ""
            try {
                if ($account.RegisterTime -and $account.RegisterTime.Length -ge 15) {
                    $timeFormatted = $account.RegisterTime -replace "_", " "
                    $timeFormatted = $timeFormatted.Substring(0, 8) + " " + $timeFormatted.Substring(9, 2) + ":" + $timeFormatted.Substring(11, 2) + ":" + $timeFormatted.Substring(13, 2)
                } else {
                    $timeFormatted = $account.RegisterTime
                }
            } catch {
                $timeFormatted = $account.RegisterTime
            }

            $jsonFilesListStr = $jsonFilesList -join ", "
            $accountInfoContent = @"
邮箱: $($account.Email)
密码: $($accountInfo.Password)
平台: $($account.AccountType)
注册时间: $timeFormatted
JSON文件: $jsonFilesListStr
"@
            $accountInfoContent | Out-File -FilePath $accountInfoPath -Encoding UTF8 -Force
            Write-Host "已创建账号信息文件: account_info.txt" -ForegroundColor Cyan
        } else {
            # 如果没有找到密码信息，创建基本信息文件
            $timeFormatted = ""
            try {
                if ($account.RegisterTime -and $account.RegisterTime.Length -ge 15) {
                    $timeFormatted = $account.RegisterTime -replace "_", " "
                    $timeFormatted = $timeFormatted.Substring(0, 8) + " " + $timeFormatted.Substring(9, 2) + ":" + $timeFormatted.Substring(11, 2) + ":" + $timeFormatted.Substring(13, 2)
                } else {
                    $timeFormatted = $account.RegisterTime
                }
            } catch {
                $timeFormatted = $account.RegisterTime
            }

            $jsonFilesListStr = $jsonFilesList -join ", "
            $accountInfoContent = @"
邮箱: $($account.Email)
密码: [未找到密码记录]
平台: $($account.AccountType)
注册时间: $timeFormatted
JSON文件: $jsonFilesListStr
"@
            $accountInfoContent | Out-File -FilePath $accountInfoPath -Encoding UTF8 -Force
            Write-Host "已创建基本账号信息文件 (未找到密码): account_info.txt" -ForegroundColor Yellow
        }

        # 3. 压缩临时目录中的所有文件到桌面
        $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
        $zipFileName = "Account_$($account.Email)_$timestamp.zip"
        $zipPath = Join-Path $desktopPath $zipFileName

        $filesToCompress = Get-ChildItem -Path $tempDir -File
        $filesToCompress | Compress-Archive -DestinationPath $zipPath -Force

        Write-Host "✅ 账号配置已压缩完成！" -ForegroundColor Green
        Write-Host "📁 保存位置: $zipPath" -ForegroundColor Green
        Write-Host "📦 压缩包包含:" -ForegroundColor Green
        foreach ($jsonFile in $jsonFilesList) {
            Write-Host "  - $jsonFile (恢复原始文件名的JSON配置)" -ForegroundColor Gray
        }
        Write-Host "  - account_info.txt (账号密码信息)" -ForegroundColor Gray

        # 尝试打开桌面文件夹（可选）
        try {
            Start-Process "explorer.exe" -ArgumentList "/select,`"$zipPath`""
            Write-Host "🔍 已在文件资源管理器中定位到压缩包" -ForegroundColor Cyan
        } catch {
            Write-Host "💡 提示: 压缩包已保存到桌面，文件名: $zipFileName" -ForegroundColor Yellow
        }

    } catch {
        Write-Host "❌ 压缩账号配置失败: $($_.Exception.Message)" -ForegroundColor Red
    } finally {
        # 清理临时目录
        if (Test-Path $tempDir) {
            Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

# 从账号.txt文件中获取账号信息
function Get-AccountInfoFromFile($email) {
    $accountFile = "$PSScriptRoot\sandbox_files\账号.txt"
    if (!(Test-Path $accountFile)) {
        return $null
    }

    try {
        $accountLines = Get-Content $accountFile -Encoding UTF8
        $matchedLine = $accountLines | Where-Object { $_ -match "^$([regex]::Escape($email))\t" }

        if ($matchedLine) {
            $parts = $matchedLine -split "\t"
            # 格式：邮箱\t\t密码\t平台\t时间 (索引: 0,1,2,3,4)
            if ($parts.Count -ge 3) {
                return @{
                    Email = $parts[0]
                    Password = $parts[2]
                    Platform = if ($parts.Count -ge 4) { $parts[3] } else { "" }
                    SaveTime = if ($parts.Count -ge 5) { $parts[4] } else { "" }
                }
            }
        }
        return $null
    } catch {
        Write-Host "读取账号文件失败: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# 显示账号详细信息
function Show-AccountInfo($account) {
    Clear-Host
    Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                      账号详细信息                            ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "邮箱地址: " -ForegroundColor White -NoNewline
    Write-Host "$($account.Email)" -ForegroundColor Yellow

    Write-Host "账号类型: " -ForegroundColor White -NoNewline
    Write-Host "$($account.AccountType)" -ForegroundColor Cyan

    # 安全的时间格式化
    $timeFormatted = ""
    try {
        if ($account.RegisterTime -and $account.RegisterTime.Length -ge 15) {
            $timeFormatted = $account.RegisterTime -replace "_", " "
            $timeFormatted = $timeFormatted.Substring(0, 8) + " " + $timeFormatted.Substring(9, 2) + ":" + $timeFormatted.Substring(11, 2) + ":" + $timeFormatted.Substring(13, 2)
        } else {
            $timeFormatted = $account.RegisterTime
        }
    } catch {
        $timeFormatted = $account.RegisterTime
    }
    Write-Host "注册时间: " -ForegroundColor White -NoNewline
    Write-Host "$timeFormatted" -ForegroundColor Green

    Write-Host "文件名称: " -ForegroundColor White -NoNewline
    Write-Host "$($account.FileName)" -ForegroundColor Gray

    # 查找同一账号的其他JSON文件
    $oauthDir = Split-Path $account.FilePath
    $relatedJsonFiles = Get-ChildItem -Path $oauthDir -Filter "*__$($account.Email)__$($account.AccountType)__$($account.RegisterTime).json" -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -ne $account.FilePath }

    $jsonFilesList = @("$($account.OriginalName).json")
    if ($relatedJsonFiles) {
        foreach ($relatedFile in $relatedJsonFiles) {
            if ($relatedFile.Name -match "^(.+?)__") {
                $jsonFilesList += "$($matches[1]).json"
            }
        }
    }

    Write-Host "JSON文件: " -ForegroundColor White -NoNewline
    if ($jsonFilesList.Count -eq 1) {
        Write-Host "$($jsonFilesList[0])" -ForegroundColor Gray
    } else {
        Write-Host ""
        foreach ($jsonFile in $jsonFilesList) {
            Write-Host "           - $jsonFile" -ForegroundColor Gray
        }
    }

    # 尝试从账号.txt文件中查找密码
    $accountFile = "$PSScriptRoot\sandbox_files\账号.txt"
    if (Test-Path $accountFile) {
        try {
            $accountLines = Get-Content $accountFile -Encoding UTF8
            $matchedLine = $accountLines | Where-Object { $_ -match "^$([regex]::Escape($account.Email))\t" }
            if ($matchedLine) {
                $parts = $matchedLine -split "\t"
                # 新格式：邮箱\t\t密码\t平台\t时间 (索引: 0,1,2,3,4)
                if ($parts.Count -ge 3) {
                    Write-Host "账号密码: " -ForegroundColor White -NoNewline
                    Write-Host "$($parts[2])" -ForegroundColor Red
                }
                if ($parts.Count -ge 5) {
                    Write-Host "保存时间: " -ForegroundColor White -NoNewline
                    Write-Host "$($parts[4])" -ForegroundColor Green
                }
                if ($parts.Count -ge 4) {
                    Write-Host "平台信息: " -ForegroundColor White -NoNewline
                    Write-Host "$($parts[3])" -ForegroundColor Cyan
                }
            } else {
                Write-Host "账号密码: " -ForegroundColor White -NoNewline
                Write-Host "未找到密码记录" -ForegroundColor Red
            }
        } catch {
            Write-Host "读取账号文件失败: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "账号密码: " -ForegroundColor White -NoNewline
        Write-Host "账号文件不存在" -ForegroundColor Red
    }

    Write-Host ""
}

# 启动沙盒的函数
function Start-SandboxMode {
    Write-Host "启动续杯模式..." -ForegroundColor Green

$wsbFilePath = "$PSScriptRoot\sandbox_config.wsb"

$wsbContent = @"
<Configuration>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>$PSScriptRoot\sandbox_files</HostFolder>
      <SandboxFolder>C:\sandbox_files</SandboxFolder>
      <ReadOnly>false</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <LogonCommand>
    <Command>powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell.exe -ArgumentList '-NoExit -ExecutionPolicy Bypass -File C:\sandbox_files\install.ps1' -WindowStyle Normal"</Command>
  </LogonCommand>
  <AudioInput>false</AudioInput>
  <ClipboardRedirection>true</ClipboardRedirection>
</Configuration>
"@

$wsbContent | Out-File -FilePath $wsbFilePath -Encoding UTF8 -Force

Write-Host "Sandbox 配置文件已生成: $wsbFilePath" -ForegroundColor Green
Write-Host "正在启动 Windows Sandbox，请稍等..." -ForegroundColor Yellow
Start-Process -FilePath $wsbFilePath

Write-Host "Sandbox 已启动！" -ForegroundColor Cyan
Write-Host "稍后会自动弹出一个 PowerShell 窗口，显示蓝色安装进度。" -ForegroundColor Magenta
Write-Host "请耐心等待 Python 下载和安装（约 1~3 分钟）。" -ForegroundColor Yellow

# 开始监控 OAuth 目录并管理 AWS SSO Cache
Write-Host "`n开始监控 OAuth 文件并管理 AWS SSO Cache..." -ForegroundColor Green
$oauthDir = "$PSScriptRoot\sandbox_files\OAuth"
$awsSsoCacheDir = "$env:USERPROFILE\.aws\sso\cache"

# 确保 OAuth 目录存在
if (!(Test-Path $oauthDir)) {
    New-Item -ItemType Directory -Path $oauthDir -Force | Out-Null
    Write-Host "已创建 OAuth 目录: $oauthDir" -ForegroundColor Yellow
}

# 确保 AWS SSO Cache 目录存在
if (!(Test-Path $awsSsoCacheDir)) {
    New-Item -ItemType Directory -Path $awsSsoCacheDir -Force -Recurse | Out-Null
    Write-Host "已创建 AWS SSO Cache 目录: $awsSsoCacheDir" -ForegroundColor Yellow
}

Write-Host "监控目录: $oauthDir" -ForegroundColor Cyan
Write-Host "AWS SSO Cache 目录: $awsSsoCacheDir" -ForegroundColor Cyan
Write-Host "功能说明: 检测到 OAuth 新增 JSON 文件时，备份 AWS SSO Cache 中的 JSON 文件，然后复制新文件到 Cache" -ForegroundColor Cyan
Write-Host "按 Ctrl+C 停止监控" -ForegroundColor Yellow

# 文件监控循环
$lastFileCount = 0
while ($true) {
    try {
        # 检查 OAuth 目录中的所有文件（不仅限于JSON）
        $oauthJsonFiles = Get-ChildItem -Path $oauthDir -Filter "*.json" -ErrorAction SilentlyContinue
        $currentFileCount = $oauthJsonFiles.Count

        if ($currentFileCount -gt $lastFileCount) {
            Write-Host "`n[检测到新文件] OAuth 目录中有 $currentFileCount 个 JSON 文件" -ForegroundColor Green

            # 步骤1: 备份 AWS SSO Cache 中的 JSON 文件
            $awsSsoJsonFiles = Get-ChildItem -Path $awsSsoCacheDir -Filter "*.json" -ErrorAction SilentlyContinue
            if ($awsSsoJsonFiles.Count -gt 0) {
                Write-Host "正在备份 AWS SSO Cache 中的 $($awsSsoJsonFiles.Count) 个 JSON 文件..." -ForegroundColor Yellow

                # 生成带时间戳的ZIP文件名
                $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
                $backupZipPath = "$awsSsoCacheDir\aws_sso_backup_$timestamp.zip"

                try {
                    # 将 AWS SSO Cache 中的所有 JSON 文件压缩到 ZIP 文件中
                    $awsSsoJsonFiles | Compress-Archive -DestinationPath $backupZipPath -Force
                    Write-Host "AWS SSO Cache 备份完成: $backupZipPath" -ForegroundColor Green

                    # 步骤2: 删除已备份的 JSON 文件
                    $deletedCount = 0
                    foreach ($file in $awsSsoJsonFiles) {
                        try {
                            Remove-Item -Path $file.FullName -Force
                            Write-Host "已删除 AWS SSO Cache 文件: $($file.Name)" -ForegroundColor Cyan
                            $deletedCount++
                        } catch {
                            Write-Host "删除 AWS SSO Cache 文件失败 $($file.Name): $($_.Exception.Message)" -ForegroundColor Red
                        }
                    }

                    if ($deletedCount -gt 0) {
                        Write-Host "成功删除 AWS SSO Cache 中的 $deletedCount 个 JSON 文件" -ForegroundColor Green
                    }

                } catch {
                    Write-Host "备份 AWS SSO Cache 文件失败: $($_.Exception.Message)" -ForegroundColor Red
                }
            } else {
                Write-Host "AWS SSO Cache 目录中没有 JSON 文件需要备份" -ForegroundColor Yellow
            }

            # 步骤3: 将 OAuth 中的 JSON 文件复制到 AWS SSO Cache
            Write-Host "正在复制 OAuth JSON 文件到 AWS SSO Cache..." -ForegroundColor Yellow
            $copiedCount = 0
            foreach ($file in $oauthJsonFiles) {
                try {
                    $destinationPath = Join-Path $awsSsoCacheDir $file.Name
                    Copy-Item -Path $file.FullName -Destination $destinationPath -Force
                    Write-Host "已复制: $($file.Name) -> AWS SSO Cache" -ForegroundColor Cyan
                    $copiedCount++
                } catch {
                    Write-Host "复制文件失败 $($file.Name): $($_.Exception.Message)" -ForegroundColor Red
                }
            }

            if ($copiedCount -gt 0) {
                Write-Host "成功复制 $copiedCount 个 JSON 文件到 AWS SSO Cache" -ForegroundColor Green
                Write-Host "OAuth 到 AWS SSO Cache 同步完成！" -ForegroundColor Green

                # 步骤4: 将 OAuth 文件夹中的 JSON 文件移动到备份目录
                $backupDir = "$PSScriptRoot\OAuth_Processed"
                if (!(Test-Path $backupDir)) {
                    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
                    Write-Host "已创建备份目录: $backupDir" -ForegroundColor Yellow
                }

                Write-Host "正在将 OAuth 文件移动到备份目录..." -ForegroundColor Yellow
                $movedCount = 0
                $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'

                foreach ($file in $oauthJsonFiles) {
                    try {
                        # 生成带时间戳的文件名避免重名
                        $fileBaseName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
                        $fileExtension = [System.IO.Path]::GetExtension($file.Name)
                        $newFileName = "${fileBaseName}_${timestamp}${fileExtension}"
                        $backupPath = Join-Path $backupDir $newFileName

                        Move-Item -Path $file.FullName -Destination $backupPath -Force
                        Write-Host "已移动 OAuth 文件: $($file.Name) -> $newFileName" -ForegroundColor Cyan
                        $movedCount++
                    } catch {
                        Write-Host "移动 OAuth 文件失败 $($file.Name): $($_.Exception.Message)" -ForegroundColor Red
                    }
                }

                if ($movedCount -gt 0) {
                    Write-Host "成功移动 $movedCount 个 JSON 文件到备份目录" -ForegroundColor Green
                    Write-Host "备份目录: $backupDir" -ForegroundColor Green
                    Write-Host "OAuth 文件夹已清理完成！" -ForegroundColor Green
                }
            }

            $lastFileCount = $currentFileCount  # 更新文件计数
        }

        # 每5秒检查一次
        Start-Sleep -Seconds 5

    } catch {
        Write-Host "监控过程中发生错误: $($_.Exception.Message)" -ForegroundColor Red
        Start-Sleep -Seconds 10
    }
}
}

# 主程序执行逻辑
# 程序启动时，智能检查和初始化固化环境（只执行一次）
$envReady = Ensure-PythonEnvironment

while ($true) {
    $choice = Show-MainMenu

    switch ($choice) {
        "sandbox" {
            # 续杯模式 - 启动沙盒并直接进入账号管理
            Write-Host "启动续杯模式..." -ForegroundColor Green

            # 启动沙盒 - 使用固化环境
            if ($envReady) {
                Write-Host "🚀 使用固化环境启动沙盒..." -ForegroundColor Green
                $wsbFilePath = "$PSScriptRoot\sandbox_config.wsb"
                $wsbContent = @"
<Configuration>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>$PSScriptRoot\python_env</HostFolder>
      <SandboxFolder>C:\python_env</SandboxFolder>
      <ReadOnly>true</ReadOnly>
    </MappedFolder>
    <MappedFolder>
      <HostFolder>$PSScriptRoot\sandbox_files</HostFolder>
      <SandboxFolder>C:\sandbox_files</SandboxFolder>
      <ReadOnly>false</ReadOnly>
    </MappedFolder>
    <MappedFolder>
      <HostFolder>$PSScriptRoot\VirtualBrowser</HostFolder>
      <SandboxFolder>C:\VirtualBrowser</SandboxFolder>
      <ReadOnly>false</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <LogonCommand>
    <Command>powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "

      # 创建桌面快捷方式
      try {
        `$desktopPath = [Environment]::GetFolderPath('Desktop')
        `$shell = New-Object -ComObject WScript.Shell

        # 创建VirtualBrowser快捷方式
        `$shortcutPath = `$desktopPath + '\VirtualBrowser.lnk'
        `$shortcut = `$shell.CreateShortcut(`$shortcutPath)
        `$shortcut.TargetPath = 'C:\VirtualBrowser\VirtualBrowser.exe'
        `$shortcut.WorkingDirectory = 'C:\VirtualBrowser'
        `$shortcut.Description = 'VirtualBrowser - 虚拟浏览器'
        `$shortcut.Save()
        Write-Host '✅ VirtualBrowser桌面快捷方式已创建' -ForegroundColor Green

        # 创建注册信息生成器快捷方式
        if (Test-Path 'C:\sandbox_files\dist\RegistrationInfoGenerator_v2.exe') {
          `$regGenShortcutPath = `$desktopPath + '\注册信息生成器.lnk'
          `$regGenShortcut = `$shell.CreateShortcut(`$regGenShortcutPath)
          `$regGenShortcut.TargetPath = 'C:\sandbox_files\dist\RegistrationInfoGenerator_v2.exe'
          `$regGenShortcut.WorkingDirectory = 'C:\sandbox_files\dist'
          `$regGenShortcut.Description = '注册信息生成器 - Registration Info Generator'
          `$regGenShortcut.Save()
          Write-Host '✅ 注册信息生成器桌面快捷方式已创建' -ForegroundColor Green
        } else {
          Write-Host '💡 注册信息生成器EXE文件未找到，跳过快捷方式创建' -ForegroundColor Gray
        }
      } catch {
        Write-Host '⚠️ 创建桌面快捷方式失败: ' + `$_.Exception.Message -ForegroundColor Yellow
      }

      # 设置VirtualBrowser为默认浏览器
      try {
        `$browserPath = 'C:\VirtualBrowser\VirtualBrowser.exe'
        `$browserName = 'VirtualBrowser'

        Write-Host '🔧 正在设置VirtualBrowser为默认浏览器...' -ForegroundColor Cyan

        # 注册浏览器能力
        New-Item -Path \"HKLM:\SOFTWARE\Clients\StartMenuInternet\`$browserName\" -Force | Out-Null
        Set-ItemProperty -Path \"HKLM:\SOFTWARE\Clients\StartMenuInternet\`$browserName\" -Name '(Default)' -Value `$browserName -Force

        New-Item -Path \"HKLM:\SOFTWARE\Clients\StartMenuInternet\`$browserName\Capabilities\" -Force | Out-Null
        Set-ItemProperty -Path \"HKLM:\SOFTWARE\Clients\StartMenuInternet\`$browserName\Capabilities\" -Name 'ApplicationName' -Value `$browserName -Force
        Set-ItemProperty -Path \"HKLM:\SOFTWARE\Clients\StartMenuInternet\`$browserName\Capabilities\" -Name 'ApplicationDescription' -Value 'VirtualBrowser - 虚拟浏览器' -Force

        New-Item -Path \"HKLM:\SOFTWARE\Clients\StartMenuInternet\`$browserName\shell\open\command\" -Force | Out-Null
        Set-ItemProperty -Path \"HKLM:\SOFTWARE\Clients\StartMenuInternet\`$browserName\shell\open\command\" -Name '(Default)' -Value \"\`\"`$browserPath\`\" \`\"%1\`\"\" -Force

        # 设置HTTP协议关联
        New-Item -Path 'HKLM:\SOFTWARE\Classes\http\shell\open\command' -Force | Out-Null
        Set-ItemProperty -Path 'HKLM:\SOFTWARE\Classes\http\shell\open\command' -Name '(Default)' -Value \"\`\"`$browserPath\`\" \`\"%1\`\"\" -Force

        # 设置HTTPS协议关联
        New-Item -Path 'HKLM:\SOFTWARE\Classes\https\shell\open\command' -Force | Out-Null
        Set-ItemProperty -Path 'HKLM:\SOFTWARE\Classes\https\shell\open\command' -Name '(Default)' -Value \"\`\"`$browserPath\`\" \`\"%1\`\"\" -Force

        # 设置为默认浏览器
        Set-ItemProperty -Path 'HKLM:\SOFTWARE\Clients\StartMenuInternet' -Name '(Default)' -Value `$browserName -Force

        # 设置用户级别的默认浏览器
        New-Item -Path 'HKCU:\SOFTWARE\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice' -Force | Out-Null
        Set-ItemProperty -Path 'HKCU:\SOFTWARE\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice' -Name 'ProgId' -Value 'VirtualBrowserHTML' -Force

        New-Item -Path 'HKCU:\SOFTWARE\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice' -Force | Out-Null
        Set-ItemProperty -Path 'HKCU:\SOFTWARE\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice' -Name 'ProgId' -Value 'VirtualBrowserHTML' -Force

        # 创建ProgId
        New-Item -Path 'HKLM:\SOFTWARE\Classes\VirtualBrowserHTML' -Force | Out-Null
        Set-ItemProperty -Path 'HKLM:\SOFTWARE\Classes\VirtualBrowserHTML' -Name '(Default)' -Value 'VirtualBrowser HTML Document' -Force
        New-Item -Path 'HKLM:\SOFTWARE\Classes\VirtualBrowserHTML\shell\open\command' -Force | Out-Null
        Set-ItemProperty -Path 'HKLM:\SOFTWARE\Classes\VirtualBrowserHTML\shell\open\command' -Name '(Default)' -Value \"\`\"`$browserPath\`\" \`\"%1\`\"\" -Force

        Write-Host '✅ VirtualBrowser已设置为默认浏览器' -ForegroundColor Green
      } catch {
        Write-Host '⚠️ 设置默认浏览器失败: ' + `$_.Exception.Message -ForegroundColor Yellow
        Write-Host '💡 VirtualBrowser仍可通过桌面快捷方式使用' -ForegroundColor Gray
      }

      # 启动主安装脚本
      Start-Process powershell.exe -ArgumentList '-NoExit -ExecutionPolicy Bypass -File C:\sandbox_files\install.ps1' -WindowStyle Normal
    "</Command>
  </LogonCommand>
  <AudioInput>false</AudioInput>
  <ClipboardRedirection>true</ClipboardRedirection>
</Configuration>
"@
            } else {
                Write-Host "⚠️  固化环境未就绪，使用传统模式启动沙盒..." -ForegroundColor Yellow
                $wsbFilePath = "$PSScriptRoot\sandbox_config.wsb"
                $wsbContent = @"
<Configuration>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>$PSScriptRoot\sandbox_files</HostFolder>
      <SandboxFolder>C:\sandbox_files</SandboxFolder>
      <ReadOnly>false</ReadOnly>
    </MappedFolder>
    <MappedFolder>
      <HostFolder>$PSScriptRoot\VirtualBrowser</HostFolder>
      <SandboxFolder>C:\VirtualBrowser</SandboxFolder>
      <ReadOnly>false</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <LogonCommand>
    <Command>powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "

      # 创建桌面快捷方式
      try {
        `$desktopPath = [Environment]::GetFolderPath('Desktop')
        `$shell = New-Object -ComObject WScript.Shell

        # 创建VirtualBrowser快捷方式
        `$shortcutPath = `$desktopPath + '\VirtualBrowser.lnk'
        `$shortcut = `$shell.CreateShortcut(`$shortcutPath)
        `$shortcut.TargetPath = 'C:\VirtualBrowser\VirtualBrowser.exe'
        `$shortcut.WorkingDirectory = 'C:\VirtualBrowser'
        `$shortcut.Description = 'VirtualBrowser - 虚拟浏览器'
        `$shortcut.Save()
        Write-Host '✅ VirtualBrowser桌面快捷方式已创建' -ForegroundColor Green

        # 创建注册信息生成器快捷方式
        if (Test-Path 'C:\sandbox_files\dist\RegistrationInfoGenerator_v2.exe') {
          `$regGenShortcutPath = `$desktopPath + '\注册信息生成器.lnk'
          `$regGenShortcut = `$shell.CreateShortcut(`$regGenShortcutPath)
          `$regGenShortcut.TargetPath = 'C:\sandbox_files\dist\RegistrationInfoGenerator_v2.exe'
          `$regGenShortcut.WorkingDirectory = 'C:\sandbox_files\dist'
          `$regGenShortcut.Description = '注册信息生成器 - Registration Info Generator'
          `$regGenShortcut.Save()
          Write-Host '✅ 注册信息生成器桌面快捷方式已创建' -ForegroundColor Green
        } else {
          Write-Host '💡 注册信息生成器EXE文件未找到，跳过快捷方式创建' -ForegroundColor Gray
        }
      } catch {
        Write-Host '⚠️ 创建桌面快捷方式失败: ' + `$_.Exception.Message -ForegroundColor Yellow
      }

      # 设置VirtualBrowser为默认浏览器
      try {
        `$browserPath = 'C:\VirtualBrowser\VirtualBrowser.exe'
        `$browserName = 'VirtualBrowser'

        Write-Host '🔧 正在设置VirtualBrowser为默认浏览器...' -ForegroundColor Cyan

        # 注册浏览器能力
        New-Item -Path \"HKLM:\SOFTWARE\Clients\StartMenuInternet\`$browserName\" -Force | Out-Null
        Set-ItemProperty -Path \"HKLM:\SOFTWARE\Clients\StartMenuInternet\`$browserName\" -Name '(Default)' -Value `$browserName -Force

        New-Item -Path \"HKLM:\SOFTWARE\Clients\StartMenuInternet\`$browserName\Capabilities\" -Force | Out-Null
        Set-ItemProperty -Path \"HKLM:\SOFTWARE\Clients\StartMenuInternet\`$browserName\Capabilities\" -Name 'ApplicationName' -Value `$browserName -Force
        Set-ItemProperty -Path \"HKLM:\SOFTWARE\Clients\StartMenuInternet\`$browserName\Capabilities\" -Name 'ApplicationDescription' -Value 'VirtualBrowser - 虚拟浏览器' -Force

        New-Item -Path \"HKLM:\SOFTWARE\Clients\StartMenuInternet\`$browserName\shell\open\command\" -Force | Out-Null
        Set-ItemProperty -Path \"HKLM:\SOFTWARE\Clients\StartMenuInternet\`$browserName\shell\open\command\" -Name '(Default)' -Value \"\`\"`$browserPath\`\" \`\"%1\`\"\" -Force

        # 设置HTTP协议关联
        New-Item -Path 'HKLM:\SOFTWARE\Classes\http\shell\open\command' -Force | Out-Null
        Set-ItemProperty -Path 'HKLM:\SOFTWARE\Classes\http\shell\open\command' -Name '(Default)' -Value \"\`\"`$browserPath\`\" \`\"%1\`\"\" -Force

        # 设置HTTPS协议关联
        New-Item -Path 'HKLM:\SOFTWARE\Classes\https\shell\open\command' -Force | Out-Null
        Set-ItemProperty -Path 'HKLM:\SOFTWARE\Classes\https\shell\open\command' -Name '(Default)' -Value \"\`\"`$browserPath\`\" \`\"%1\`\"\" -Force

        # 设置为默认浏览器
        Set-ItemProperty -Path 'HKLM:\SOFTWARE\Clients\StartMenuInternet' -Name '(Default)' -Value `$browserName -Force

        # 设置用户级别的默认浏览器
        New-Item -Path 'HKCU:\SOFTWARE\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice' -Force | Out-Null
        Set-ItemProperty -Path 'HKCU:\SOFTWARE\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice' -Name 'ProgId' -Value 'VirtualBrowserHTML' -Force

        New-Item -Path 'HKCU:\SOFTWARE\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice' -Force | Out-Null
        Set-ItemProperty -Path 'HKCU:\SOFTWARE\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice' -Name 'ProgId' -Value 'VirtualBrowserHTML' -Force

        # 创建ProgId
        New-Item -Path 'HKLM:\SOFTWARE\Classes\VirtualBrowserHTML' -Force | Out-Null
        Set-ItemProperty -Path 'HKLM:\SOFTWARE\Classes\VirtualBrowserHTML' -Name '(Default)' -Value 'VirtualBrowser HTML Document' -Force
        New-Item -Path 'HKLM:\SOFTWARE\Classes\VirtualBrowserHTML\shell\open\command' -Force | Out-Null
        Set-ItemProperty -Path 'HKLM:\SOFTWARE\Classes\VirtualBrowserHTML\shell\open\command' -Name '(Default)' -Value \"\`\"`$browserPath\`\" \`\"%1\`\"\" -Force

        Write-Host '✅ VirtualBrowser已设置为默认浏览器' -ForegroundColor Green
      } catch {
        Write-Host '⚠️ 设置默认浏览器失败: ' + `$_.Exception.Message -ForegroundColor Yellow
        Write-Host '💡 VirtualBrowser仍可通过桌面快捷方式使用' -ForegroundColor Gray
      }

      # 启动主安装脚本
      Start-Process powershell.exe -ArgumentList '-NoExit -ExecutionPolicy Bypass -File C:\sandbox_files\install.ps1' -WindowStyle Normal
    "</Command>
  </LogonCommand>
  <AudioInput>false</AudioInput>
  <ClipboardRedirection>true</ClipboardRedirection>
</Configuration>
"@
            }

            $wsbContent | Out-File -FilePath $wsbFilePath -Encoding UTF8 -Force
            Write-Host "Sandbox 配置文件已生成: $wsbFilePath" -ForegroundColor Green
            Write-Host "正在启动 Windows Sandbox，请稍等..." -ForegroundColor Yellow
            Start-Process -FilePath $wsbFilePath
            Write-Host "Sandbox 已启动！" -ForegroundColor Cyan
            Write-Host "稍后会自动弹出一个 PowerShell 窗口，显示蓝色安装进度。" -ForegroundColor Magenta
            Write-Host "请耐心等待 Python 下载和安装（约 1~3 分钟）。" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "沙盒已启动，现在进入账号管理界面..." -ForegroundColor Green
            Start-Sleep -Seconds 2

            # 直接进入账号管理
            Show-AccountManager
        }
        "account" {
            # 账号管理
            Show-AccountManager
        }
        "settings" {
            # 系统设置
            Show-SystemSettings
        }
        "exit" {
            # 退出程序
            Write-Host "感谢使用 Kiro 自动化沙盒管理系统！" -ForegroundColor Green
            exit 0
        }
    }
}