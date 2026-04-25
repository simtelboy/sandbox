# 编译注册信息生成器为 EXE
# 使用 PyInstaller

Write-Host "开始编译 registration_info_generator.py..." -ForegroundColor Green

# 检查 PyInstaller 是否安装
$pyinstallerCheck = python -m pip show pyinstaller 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller 未安装，正在安装..." -ForegroundColor Yellow
    python -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "安装 PyInstaller 失败！" -ForegroundColor Red
        exit 1
    }
}

# 切换到 sandbox_files 目录
Set-Location $PSScriptRoot

# 清理旧的构建文件
if (Test-Path "build") {
    Write-Host "清理旧的 build 目录..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "build"
}

if (Test-Path "dist/RegistrationInfoGenerator_v2.exe") {
    Write-Host "清理旧的 exe 文件..." -ForegroundColor Yellow
    Remove-Item -Force "dist/RegistrationInfoGenerator_v2.exe"
}

# 编译为单个 EXE 文件
Write-Host "正在编译..." -ForegroundColor Cyan
python -m PyInstaller `
    --onefile `
    --windowed `
    --name "RegistrationInfoGenerator_v2" `
    --icon=NONE `
    --add-data "name.txt;." `
    --add-data ".env.example;." `
    --hidden-import=email_service `
    --hidden-import=tkinter `
    --hidden-import=pyperclip `
    registration_info_generator.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n编译成功！" -ForegroundColor Green
    Write-Host "EXE 文件位置: $PSScriptRoot\dist\RegistrationInfoGenerator_v2.exe" -ForegroundColor Green
    
    # 生成 README
    $readmeContent = @"
# Registration Info Generator v2.0

## What's New in v2.0

### Fixed Issues
- ✅ Path resolution: Files now save to C:/sandbox_files/ consistently
- ✅ Password generation: Simplified to use only +.> special characters
- ✅ File formatting: Proper line breaks in account.txt
- ✅ Email service: Fully integrated into EXE
- ✅ Custom email and password: Added customization dialog

### Features
- Generate registration info (email, username, password, name)
- Customize email and password before confirming
- Receive verification codes from AWS, GitHub, Google, etc.
- Save account info to C:/sandbox_files/account.txt
- Manage OAuth files in C:/sandbox_files/OAuth/

## Usage Instructions

### Quick Start
1. Run RegistrationInfoGenerator_v2.exe
2. Click "🎲 生成新的注册信息"
3. Click on any field to copy to clipboard
4. After copying password and any other field, "✏️ 自定义" button becomes available
5. Click "✏️ 自定义" to customize email and password (optional)
6. Click "✅ 确认注册成功" to save account info

### File Locations
- Account info: C:/sandbox_files/account.txt
- OAuth files: C:/sandbox_files/OAuth/
- Program will create directories automatically

### Password Format
- Length: 9 characters
- Contains: letters, numbers, and simple symbols (+.>)
- Example: Abc123+De, Fgh456.Ij

### Email Service Configuration
If you want to use email verification features, ensure your .env file contains:
``````
EMAIL_DOMAIN=kt167.cc
SMS_WEBSITE=https://sms-activate.org/
``````

## Requirements
- Windows 7 or later
- No additional Python installation required
- Internet connection for email verification (optional)

## Troubleshooting
- If files don't save to expected location, check C:/sandbox_files/
- If email service fails, verify .env configuration
- For any issues, check the console output for error messages

Built with PyInstaller
Generated on: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

"@
    
    $readmeContent | Out-File -FilePath "dist/README_v2.txt" -Encoding UTF8
    Write-Host "README 已生成" -ForegroundColor Green
    
} else {
    Write-Host "`n编译失败！请检查错误信息。" -ForegroundColor Red
    exit 1
}
