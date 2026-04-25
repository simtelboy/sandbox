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
```
EMAIL_DOMAIN=kt167.cc
SMS_WEBSITE=https://sms-activate.org/
```

## Requirements
- Windows 7 or later
- No additional Python installation required
- Internet connection for email verification (optional)

## Troubleshooting
- If files don't save to expected location, check C:/sandbox_files/
- If email service fails, verify .env configuration
- For any issues, check the console output for error messages

Built with PyInstaller 6.5.0
Generated on: 2025-04-25
