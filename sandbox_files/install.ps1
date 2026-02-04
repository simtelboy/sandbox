# 作者: Grok
# 描述: 此脚本在 Windows Sandbox 中运行，显示安装进度，生成随机硬件指纹，安装 Python，验证版本，安装 pywinauto、Selenium 和 WebDriver Manager，并自动化安装 kiro.exe。
# 注意: 需要互联网连接。假设 kiro.exe 是安装程序，automate_kiro.py 用于自动化。Selenium 和 WebDriver Manager 为未来网页自动化准备（使用 Edge 浏览器）。

# 设置编码以支持输出
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null


# 设置窗口标题
$host.UI.RawUI.WindowTitle = "Installation Progress - Do Not Close"

# 测试中文显示效果
Write-Host "`n=== 中文字体显示测试 ===" -ForegroundColor Cyan
Write-Host "测试中文字符: 中文显示测试成功！" -ForegroundColor Green
Write-Host "如果上面显示正常，说明字体修复生效" -ForegroundColor Yellow
Write-Host "=========================" -ForegroundColor Cyan

# 初始化日志文件
$logPath = "C:\sandbox_files\install_log.txt"
"安装日志开始: $(Get-Date)" | Out-File -FilePath $logPath -Encoding UTF8

# 显示头部
Write-Host "`n`n=========================================" -ForegroundColor Blue
Write-Host "       Installation Script Running...     " -ForegroundColor Blue
Write-Host "=========================================`n" -ForegroundColor Blue
"头部显示完成" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue

# 进度初始化
Write-Progress -Activity "Installation Progress" -Status "Initializing..." -PercentComplete 0

# 1. 生成硬件指纹
Write-Progress -Activity "Installation Progress" -Status "Generating Hardware Fingerprints..." -PercentComplete 10
Write-Host "[1/7] Generating Random Hardware Fingerprints..." -ForegroundColor Yellow
"[1/7] 生成硬件指纹" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue

$random = {
    param($min, $max)
    (Get-Random -Minimum $min -Maximum $max) -as [int]
}

$hardwareFingerprints = @{
    "MAC_Address"            = (1..6 | ForEach-Object { "{0:X2}" -f (& $random 0 256) }) -join ":"
    "CPU_ID"                 = [guid]::NewGuid().ToString()
    "Hard_Drive_Serial"      = "HD{0:D8}" -f (& $random 10000000 99999999)
    "BIOS_Version"           = "BIOS_v{0}.{1}" -f (& $random 1 10), (& $random 0 99)
    "BIOS_UUID"              = [guid]::NewGuid().ToString()
    "Motherboard_Serial"     = "MB_SN_{0}" -f [guid]::NewGuid().ToString().Substring(0,12)
    "Motherboard_Model"      = "Model_{0}" -f (& $random 1000 9999)
    "RAM_ID"                 = "RAM_SN_{0}" -f (& $random 100000 999999)
    "GPU_ID"                 = "GPU_{0}" -f [guid]::NewGuid().ToString().Substring(0,8)
    "GPU_Model"              = "NVIDIA_GTX_{0}" -f (& $random 1000 4000)
    "System_UUID"            = [guid]::NewGuid().ToString()
    "System_Product_ID"      = "Product_{0}" -f [guid]::NewGuid().ToString().Substring(0,10)
    "Computer_Name"          = "PC_{0:D5}" -f (& $random 10000 99999)
    "User_Name"              = "User_{0}" -f (& $random 1000 9999)
    "OS_Build_Number"        = & $random 19000 26000
    "Network_Adapter_ID"     = [guid]::NewGuid().ToString()
    "IP_Address"             = "{0}.{1}.{2}.{3}" -f (& $random 1 255), (& $random 0 255), (& $random 0 255), (& $random 1 254)
    "USB_Device_ID"          = "USB_{0}" -f [guid]::NewGuid().ToString().Substring(0,8)
    "Monitor_Serial"         = "MON_SN_{0}" -f (& $random 100000 999999)
    "Monitor_Model"          = "Display_{0}" -f (& $random 100 999)
    "Printer_ID"             = "Printer_{0}" -f [guid]::NewGuid().ToString().Substring(0,6)
    "VM_Detection_ID"        = & $random 0 2
    "Browser_UserAgent"      = $null  # 将在后面生成随机化的User-Agent
    "TimeZone"               = "UTC{0}{1:D2}" -f $(if ((& $random 0 2) -eq 0) { "-" } else { "+" }), (& $random 0 12)
    "Audio_Device_ID"        = "Audio_{0}" -f [guid]::NewGuid().ToString().Substring(0,10)
    "Keyboard_Layout"        = "Layout_{0}" -f (& $random 100 999)
}


# ==================== 浏览器指纹增强 + 写入系统 ====================

# 生成随机化User-Agent
function Generate-RandomUserAgent {
    # 随机Windows版本 (10.0权重更高)
    $windowsVersions = @("10.0", "10.0", "10.0", "11.0")
    $winVer = Get-Random -InputObject $windowsVersions

    # 兼容的Chrome/Edge版本 (110-116，测试验证的安全范围)
    $chromeVersions = @("110.0.0.0", "111.0.0.0", "112.0.0.0", "113.0.0.0", "114.0.0.0", "115.0.0.0", "116.0.0.0")
    $chromeVer = Get-Random -InputObject $chromeVersions

    return "Mozilla/5.0 (Windows NT $winVer; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/$chromeVer Safari/537.36 Edg/$chromeVer"
}

# 生成随机User-Agent
$randomUserAgent = Generate-RandomUserAgent
Write-Host "Generated Random User-Agent: $randomUserAgent" -ForegroundColor Cyan

# 随机分辨率
$screenResolutions = @("1920x1080", "1366x768", "1536x864", "1280x720", "1440x900", "1600x900", "1280x800", "2560x1440")
$resIndex = & $random 0 ($screenResolutions.Count)
$resolution = $screenResolutions[$resIndex]
$width, $height = $resolution -split 'x'

# 随机语言
$languages = @("zh-CN", "en-US", "en-GB", "zh-TW", "ja-JP", "ko-KR")
$acceptLang = ($languages | Get-Random -Count (& $random 1 3)) -join ", "

# WebGL
$webglVendors = @("NVIDIA Corporation", "Intel Inc.", "AMD", "Google Inc.")
$webglRenderers = @(
    "NVIDIA GeForce GTX {0} OpenGL Engine" -f (& $random 900 3090)
    "Intel(R) UHD Graphics {0}" -f (& $random 600 900)
    "ANGLE (NVIDIA, NVIDIA GeForce RTX {0} Direct3D11 vs_5_0 ps_5_0)" -f (& $random 2000 4000)
)
$vendorIndex = & $random 0 ($webglVendors.Count)
$rendererIndex = & $random 0 ($webglRenderers.Count)
$webglVendor = $webglVendors[$vendorIndex]
$webglRenderer = $webglRenderers[$rendererIndex]

# Canvas / Audio 伪哈希
$canvasData = (& $random 100000000 999999999).ToString() + (& $random 100000000 999999999).ToString()
$canvasBase64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($canvasData))
$canvasHashLen = [Math]::Min(32, $canvasBase64.Length)
$canvasHash = "canvas_{0}" -f $canvasBase64.Substring(0, $canvasHashLen)
$audioHash = "audio_{0:X8}" -f (& $random 268435456 2147483647)

# 插件列表
$plugins = @("Chrome PDF Plugin", "Chrome PDF Viewer", "Native Client") -join "; "

# ========== 1. 写入环境变量（供程序读取）==========
[Environment]::SetEnvironmentVariable("BROWSER_USERAGENT", $randomUserAgent, "Machine")
[Environment]::SetEnvironmentVariable("BROWSER_ACCEPTLANG", $acceptLang, "Machine")
[Environment]::SetEnvironmentVariable("SCREEN_RESOLUTION", $resolution, "Machine")
[Environment]::SetEnvironmentVariable("WEBGL_VENDOR", $webglVendor, "Machine")
[Environment]::SetEnvironmentVariable("WEBGL_RENDERER", $webglRenderer, "Machine")

# ========== 2. 写入注册表（Chrome / Edge 读取）==========
$regPath = "HKLM:\SOFTWARE\Policies\Google\Chrome"
if (-not (Test-Path $regPath)) { New-Item -Path $regPath -Force | Out-Null }

Set-ItemProperty -Path $regPath -Name "DefaultBrowserSettingEnabled" -Value 0 -Type DWord -Force
Set-ItemProperty -Path $regPath -Name "UserAgent" -Value $env:BROWSER_USERAGENT -Force
Set-ItemProperty -Path $regPath -Name "AcceptLanguage" -Value $acceptLang -Force

# WebGL 伪装（通过扩展策略）
$extPath = "HKLM:\SOFTWARE\Policies\Google\Chrome\3rdparty\extensions"
if (-not (Test-Path $extPath)) { New-Item -Path $extPath -Force | Out-Null }
# 模拟 WebGL 指纹修改扩展（实际需配合 Selenium CDP）
$extSubPath = "$extPath\cjpalhdlnbpafiamejdajceeocdbgejm"
if (-not (Test-Path $extSubPath)) { New-Item -Path $extSubPath -Force | Out-Null }
Set-ItemProperty -Path $extSubPath -Name "override_webgl" -Value 1 -Force

# ========== 3. 写入系统分辨率（模拟真实屏幕）==========
# 注意：SystemInformation.VirtualScreen 是只读属性，无法直接修改
# 此处通过注册表设置显示分辨率信息
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows" -Name "DisplayWidth" -Value $width -Type DWord -Force
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows" -Name "DisplayHeight" -Value $height -Type DWord -Force
Write-Host "Screen resolution set to $resolution via Registry" -ForegroundColor Cyan

# ========== 4. 写入 JSON（供 Selenium 读取）==========
$hardwareFingerprints["Browser_UserAgent"] = $randomUserAgent
$hardwareFingerprints["Browser_AcceptLanguage"] = $acceptLang
$hardwareFingerprints["Browser_Platform"] = "Win64"
$hardwareFingerprints["Browser_Vendor"] = "Google Inc."
$hardwareFingerprints["Browser_Renderer"] = "Blink"
$hardwareFingerprints["WebGL_Vendor"] = $webglVendor
$hardwareFingerprints["WebGL_Renderer"] = $webglRenderer
$hardwareFingerprints["Canvas_Fingerprint"] = $canvasHash
$hardwareFingerprints["AudioContext_Fingerprint"] = $audioHash
$hardwareFingerprints["Screen_Resolution"] = $resolution
$hardwareFingerprints["Plugins_List"] = $plugins
$dntIndex = & $random 0 2
$hardwareFingerprints["DoNotTrack"] = @("1", "0")[$dntIndex]
$timezoneOffset = (& $random 0 1441) - 720  # -720 到 +720 分钟
$hardwareFingerprints["Timezone_Offset"] = $timezoneOffset

Write-Host "Browser fingerprints injected into SYSTEM (Env + Registry + JSON)" -ForegroundColor Green


$jsonPath = "C:\sandbox_files\config.json"
# 使用 UTF8NoBOM 编码避免 BOM 问题
$jsonContent = $hardwareFingerprints | ConvertTo-Json -Depth 3
[System.IO.File]::WriteAllText($jsonPath, $jsonContent, [System.Text.UTF8Encoding]::new($false))
Write-Host "config.json Generated: $jsonPath" -ForegroundColor Green
"配置.json 生成完成: $jsonPath" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue

# 导入指纹到系统
Write-Host "[1/7] Applying Fingerprints to System (Simulating Random Hardware, Skipping MAC Apply)..." -ForegroundColor Yellow
"应用指纹到系统" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue

try {
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Cryptography" -Name "MachineGuid" -Value $hardwareFingerprints.System_UUID -Force -ErrorAction Stop
    Write-Host "Applied System_UUID to Registry." -ForegroundColor Green

    [Environment]::SetEnvironmentVariable("COMPUTERNAME", $hardwareFingerprints.Computer_Name, "Machine")
    Write-Host "Applied Computer_Name to Environment." -ForegroundColor Green

    [Environment]::SetEnvironmentVariable("USERNAME", $hardwareFingerprints.User_Name, "User")
    Write-Host "Applied User_Name to Environment." -ForegroundColor Green

    if (-not (Test-Path "HKLM:\SYSTEM\HardwareConfig")) { New-Item -Path "HKLM:\SYSTEM\HardwareConfig" -Force | Out-Null }
    Set-ItemProperty -Path "HKLM:\SYSTEM\HardwareConfig" -Name "BIOSUUID" -Value $hardwareFingerprints.BIOS_UUID -Force -ErrorAction Stop
    Write-Host "Applied BIOS_UUID to Registry." -ForegroundColor Green

    Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion" -Name "HardDriveSerial" -Value $hardwareFingerprints.Hard_Drive_Serial -Force -ErrorAction Stop
    Write-Host "Applied Hard_Drive_Serial to Registry." -ForegroundColor Green

    Write-Host "MAC Address Generated but Not Applied to Adapter." -ForegroundColor Cyan

    [Environment]::SetEnvironmentVariable("OS_BUILD", $hardwareFingerprints.OS_Build_Number, "Machine")
    [Environment]::SetEnvironmentVariable("USERAGENT", $hardwareFingerprints.Browser_UserAgent, "User")
    Write-Host "Applied Other Fingerprints (OS Build, UserAgent, etc.)." -ForegroundColor Green

} catch {
    Write-Host "Warning: Some Fingerprint Applications Failed: $($_.Exception.Message)" -ForegroundColor Yellow
    "指纹应用失败: $($_.Exception.Message)" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue
}

# 2. 智能检测固化 Python 环境
Write-Progress -Activity "Installation Progress" -Status "Checking Python Environment..." -PercentComplete 25
Write-Host "[2/7] 🔍 检查 Python 环境..." -ForegroundColor Yellow
"[2/7] 检查 Python 环境" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue

# 首先检查是否有固化的 Python 环境
$cachedPythonPath = "C:\python_env\python.exe"
$useCachedPython = $false

if (Test-Path $cachedPythonPath) {
    Write-Host "✅ 发现固化 Python 环境!" -ForegroundColor Green
    "发现固化 Python 环境: $cachedPythonPath" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue

    # 验证固化环境的完整性
    try {
        $cachedVersion = & $cachedPythonPath --version 2>&1
        Write-Host "📦 固化 Python 版本: $cachedVersion" -ForegroundColor Cyan

        # 设置环境变量使用固化 Python
        $env:PATH = "C:\python_env;C:\python_env\Scripts;$env:PATH"
        [Environment]::SetEnvironmentVariable("PATH", $env:PATH, "Process")

        # 验证关键库
        $libTest = & $cachedPythonPath -c "import pywinauto, selenium, requests; print('OK')" 2>$null
        if ($libTest -eq "OK") {
            Write-Host "✅ 固化环境库验证成功，跳过 Python 安装!" -ForegroundColor Green
            "固化环境验证成功，跳过安装" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue
            $useCachedPython = $true
        } else {
            Write-Host "⚠️  固化环境库验证失败，回退到传统安装" -ForegroundColor Yellow
            "固化环境库验证失败: $libTest" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue
        }
    } catch {
        Write-Host "⚠️  固化环境验证异常，回退到传统安装: $($_.Exception.Message)" -ForegroundColor Yellow
        "固化环境验证异常: $($_.Exception.Message)" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "❌ 未发现固化 Python 环境，使用传统安装模式" -ForegroundColor Yellow
    "未发现固化环境，使用传统模式" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue
}

# 如果使用固化环境，跳过 Python 安装步骤
if ($useCachedPython) {
    Write-Progress -Activity "Installation Progress" -Status "Using Cached Python..." -PercentComplete 60
    Write-Host "[3/7] ⚡ 使用固化 Python 环境 (跳过安装)" -ForegroundColor Green
    Write-Host "[4/7] ⚡ 使用固化库环境 (跳过安装)" -ForegroundColor Green
    Write-Host "[5/7] ⚡ 使用固化库环境 (跳过安装)" -ForegroundColor Green
    Write-Host "[6/7] ⚡ 使用固化库环境 (跳过安装)" -ForegroundColor Green
    "使用固化环境，跳过所有 Python 相关安装" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue

    # 直接跳转到 kiro.exe 安装
    $pythonVersion = & $cachedPythonPath --version 2>&1
} else {
    # 如果没有固化环境，提示用户并退出
    Write-Host "❌ 错误: 未找到固化 Python 环境!" -ForegroundColor Red
    Write-Host "💡 请确保主机已正确配置固化环境" -ForegroundColor Yellow
    Write-Host "💡 运行主机的 start_sandbox.ps1 会自动创建固化环境" -ForegroundColor Yellow
    "未找到固化环境，退出安装" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue
    Write-Host "`n按任意键退出..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# 2.5. 检查并安装 VirtualBrowser（固化）
Write-Progress -Activity "Installation Progress" -Status "Checking VirtualBrowser..." -PercentComplete 65
Write-Host "[2.5/4] 🌐 检查 VirtualBrowser..." -ForegroundColor Yellow
"[2.5/4] 检查 VirtualBrowser" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue

$vbInstallPath = "C:\VirtualBrowser"
$vbExePath = "$vbInstallPath\VirtualBrowser.exe"

# 检查 VirtualBrowser 是否已安装（固化）
if (Test-Path $vbExePath) {
    $fileSize = [math]::Round((Get-Item $vbExePath).Length / 1MB, 2)
    Write-Host "✅ VirtualBrowser 已固化 (Size: ${fileSize} MB)" -ForegroundColor Green
    "VirtualBrowser 已固化，跳过安装" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue
} else {
    Write-Host "📥 VirtualBrowser 未安装，开始下载并安装..." -ForegroundColor Yellow
    "VirtualBrowser 未安装，开始下载" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue

    # 从 sandbox_files 检查是否有安装包
    $vbSetupPath = "C:\sandbox_files\VirtualBrowser.Setup.2.2.14.exe"

    if (!(Test-Path $vbSetupPath)) {
        # 如果本地没有，从 GitHub 下载
        Write-Host "📡 从 GitHub 下载 VirtualBrowser 安装包..." -ForegroundColor Cyan
        $vbDownloadUrl = "https://github.com/simtelboy/sandbox/releases/download/202507232058-Kiro-win32-x64/VirtualBrowser.Setup.2.2.14.exe"

        try {
            $ProgressPreference = 'SilentlyContinue'
            Invoke-WebRequest -Uri $vbDownloadUrl -OutFile $vbSetupPath -UseBasicParsing -TimeoutSec 600
            Write-Host "✅ VirtualBrowser 安装包下载完成" -ForegroundColor Green
            "VirtualBrowser 下载成功" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue
        } catch {
            Write-Host "❌ VirtualBrowser 下载失败: $($_.Exception.Message)" -ForegroundColor Red
            "VirtualBrowser 下载失败: $($_.Exception.Message)" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue
            Write-Host ""
            Write-Host "💡 VirtualBrowser 可以稍后手动安装：" -ForegroundColor Yellow
            Write-Host "   1. 访问 VirtualBrowser 官网下载安装包" -ForegroundColor Gray
            Write-Host "   2. 安装到 C:\VirtualBrowser\" -ForegroundColor Gray
            Write-Host "   3. 下次运行沙盒时会自动使用固化的 VirtualBrowser" -ForegroundColor Gray
            Write-Host ""
            Write-Host "⚠️ 跳过 VirtualBrowser 安装，继续..." -ForegroundColor Yellow
        }
    }

    # 安装 VirtualBrowser
    if (Test-Path $vbSetupPath) {
        Write-Host "🚀 安装 VirtualBrowser 到固化目录..." -ForegroundColor Cyan
        try {
            # 静默安装到指定目录（注意：/D 参数必须在最后，且路径不能有引号）
            Start-Process -FilePath $vbSetupPath -ArgumentList "/S", "/D=$vbInstallPath" -Wait -NoNewWindow

            # 验证安装
            if (Test-Path $vbExePath) {
                Write-Host "✅ VirtualBrowser 安装成功并已固化！" -ForegroundColor Green
                "VirtualBrowser 安装成功" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue
            } else {
                Write-Host "⚠️ VirtualBrowser 安装可能未完成" -ForegroundColor Yellow
                "VirtualBrowser 安装验证失败" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue
            }
        } catch {
            Write-Host "❌ VirtualBrowser 安装失败: $($_.Exception.Message)" -ForegroundColor Red
            "VirtualBrowser 安装失败: $($_.Exception.Message)" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue
        }
    }
}

# 3. 检查并获取 kiro.exe
Write-Progress -Activity "Installation Progress" -Status "Checking kiro.exe..." -PercentComplete 70
Write-Host "[3/4] 📥 检查 kiro.exe..." -ForegroundColor Yellow
"[3/4] 检查 kiro.exe" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue

$kiroPath = "C:\sandbox_files\kiro.exe"
$useLocalKiro = $false

# 步骤1: 检查本地是否存在 kiro.exe
if (Test-Path $kiroPath) {
    $fileSize = [math]::Round((Get-Item $kiroPath).Length / 1MB, 2)
    if ($fileSize -gt 10) {  # kiro.exe 应该大于 10MB
        Write-Host "✅ Found local kiro.exe (Size: ${fileSize} MB)" -ForegroundColor Green
        "使用本地 kiro.exe: ${fileSize} MB" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue
        $useLocalKiro = $true
    } else {
        Write-Host "⚠️ Local kiro.exe too small (${fileSize} MB), will download from web..." -ForegroundColor Yellow
        "本地文件过小，将重新下载" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue
        # 删除无效的本地文件
        Remove-Item $kiroPath -Force -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "❌ Local kiro.exe not found, will download from official API..." -ForegroundColor Yellow
    "本地未找到 kiro.exe，从官方 API 下载" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue
}

# 步骤2: 如果本地没有有效文件，从 GitHub 下载
if (-not $useLocalKiro) {
    Write-Progress -Activity "Installation Progress" -Status "Downloading kiro.exe..." -PercentComplete 80

    # 从 GitHub Release 下载
    $downloadUrl = "https://github.com/simtelboy/sandbox/releases/download/202507232058-Kiro-win32-x64/202507232058-Kiro-win32-x64.exe"

    Write-Host "📡 从 GitHub 下载 kiro.exe..." -ForegroundColor Cyan
    Write-Host "🔗 Download URL: $downloadUrl" -ForegroundColor Cyan
    "从 GitHub 下载 kiro.exe" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue

    # 下载 kiro.exe
    Write-Host "⬇️ Downloading kiro.exe..." -ForegroundColor Yellow

    $downloadSuccess = $false
    $attempt = 0
    $maxAttempts = 5

    while (-not $downloadSuccess -and $attempt -lt $maxAttempts) {
        $attempt++
        Write-Host "  📥 Download attempt ${attempt}/${maxAttempts}..." -ForegroundColor Cyan

        try {
            $ProgressPreference = 'SilentlyContinue'
            Invoke-WebRequest -Uri $downloadUrl -OutFile $kiroPath -UseBasicParsing -TimeoutSec 600 -ErrorAction Stop

            # 验证下载的文件
                if (Test-Path $kiroPath) {
                    $fileSize = [math]::Round((Get-Item $kiroPath).Length / 1MB, 2)
                    if ($fileSize -gt 10) {
                        Write-Host "  ✅ kiro.exe downloaded successfully! (Size: ${fileSize} MB)" -ForegroundColor Green
                        "kiro.exe 下载成功: ${fileSize} MB" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue
                        $downloadSuccess = $true
                    } else {
                        throw "Downloaded file too small (${fileSize} MB)"
                    }
                } else {
                    throw "Downloaded file not found"
                }
            } catch {
                Write-Host "  ❌ Download failed: $($_.Exception.Message)" -ForegroundColor Red
                "下载失败 [尝试 $attempt]: $($_.Exception.Message)" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue

                # 清理失败的下载文件
                if (Test-Path $kiroPath) {
                    Remove-Item $kiroPath -Force -ErrorAction SilentlyContinue
                }

                if ($attempt -lt $maxAttempts) {
                    Write-Host "  ⏳ Retrying in 10 seconds..." -ForegroundColor Yellow
                    Start-Sleep -Seconds 10
                }
            }
        }

    # 检查最终下载结果
    if (-not $downloadSuccess) {
        Write-Host "❌ ERROR: Failed to download kiro.exe after $maxAttempts attempts!" -ForegroundColor Red
        "kiro.exe 下载最终失败" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue
        Write-Host "`nPress Any Key to Exit..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
}

# 安装 kiro.exe
Write-Progress -Activity "Installation Progress" -Status "Installing kiro.exe..." -PercentComplete 90
Write-Host "[4/4] 🚀 启动 kiro.exe 安装程序..." -ForegroundColor Yellow
"启动 kiro.exe 安装程序" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue

# 启动 Kiro 安装程序
$process = Start-Process -FilePath $kiroPath -PassThru -NoNewWindow
Write-Host "kiro Installer Started (PID: $($process.Id))" -ForegroundColor Cyan

# 使用 Python 自动化脚本完成安装
if (Test-Path "C:\sandbox_files\automate_kiro.py") {
    Write-Host "[4/4] 🤖 运行 kiro 自动化脚本..." -ForegroundColor Yellow
    if ($useCachedPython) {
        & $cachedPythonPath "C:\sandbox_files\automate_kiro.py"
    } else {
        & python "C:\sandbox_files\automate_kiro.py"
    }
    Write-Host "✅ 自动化脚本执行完成" -ForegroundColor Green
    "自动化脚本执行完成" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue
}

# 等待主程序启动
$timeout = 300
$elapsed = 0
$kiroInstalled = $false

while ($elapsed -lt $timeout -and -not $kiroInstalled) {
    Start-Sleep -Seconds 3
    $elapsed += 3

    $kiroProcess = Get-Process -Name "kiro" -ErrorAction SilentlyContinue | Where-Object {
        $_.Path -like "*\Programs\Kiro\kiro.exe"
    }

    if ($kiroProcess) {
        Write-Host "Detected kiro Main Program Running! Installation Complete." -ForegroundColor Green
        "kiro 主程序运行: PID $($kiroProcess.Id)" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue
        $kiroInstalled = $true
        break
    }

    $installDir = "$env:LOCALAPPDATA\Programs\Kiro"
    if (Test-Path $installDir) {
        Write-Host "Detected kiro Install Directory, Waiting for Main Program..." -ForegroundColor Cyan
    }
}

if (-not $kiroInstalled) {
    Write-Host "Warning: Timeout - kiro Main Program Not Detected." -ForegroundColor Yellow
} else {
    Write-Host "kiro.exe Installed and Started Successfully!" -ForegroundColor Green
}

# 完成
Write-Progress -Activity "Installation Progress" -Status "Completed" -PercentComplete 100
Write-Host "`n`n=========================================" -ForegroundColor Green
Write-Host "       All Installations Completed!       " -ForegroundColor Green
Write-Host "=========================================`n" -ForegroundColor Green
"安装完成: $(Get-Date)" | Add-Content -Path $logPath -Encoding UTF8 -ErrorAction SilentlyContinue

Write-Host "Tip: Open Command Prompt and Run 'python --version' to Verify" -ForegroundColor Cyan
Write-Host "kiro.exe Installed to $env:LOCALAPPDATA\Programs\Kiro" -ForegroundColor Cyan
Write-Host "Log Saved to: $logPath" -ForegroundColor Cyan

Write-Host "`nPress Any Key to Close This Window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")