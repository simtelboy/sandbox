# Registration Info Generator v2.0

## What's New in v2.0

### Fixed Issues
- ✅ Path resolution: Files now save to C:/sandbox_files/ consistently
- ✅ Password generation: Simplified to use only +.> special characters
- ✅ File formatting: Proper line breaks in account.txt
- ✅ Email service: Fully integrated into EXE

### Features
- Generate registration info (email, username, password, name)
- Receive verification codes from AWS, GitHub, Google
- Save account info to C:/sandbox_files/account.txt
- Manage OAuth files in C:/sandbox_files/OAuth/

## Usage Instructions

### Quick Start
1. Run RegistrationInfoGenerator_v2.exe
2. Click "Generate Registration Info"
3. Copy the generated information as needed
4. Use "Get Verification Code" for email verification

### File Locations
- Account info: C:/sandbox_files/account.txt
- OAuth files: C:/sandbox_files/OAuth/
- Program will create directories automatically

### Password Format
- Length: 6-8 characters
- Contains: letters, numbers, and simple symbols (+.>)
- Example: Abc123+, Def456., Ghi789>

### Email Service Configuration
If you want to use email verification features, ensure your .env file contains:
```
[EMAIL]
IMAP_SERVER=your.imap.server
IMAP_PORT=993
IMAP_USER=your@email.com
IMAP_PASS=your_password
IMAP_USE_SSL=true
```

## Requirements
- Windows 7 or later
- No additional Python installation required
- Internet connection for email verification (optional)

## Troubleshooting
- If files don't save to expected location, check C:/sandbox_files/
- If email service fails, verify .env configuration
- For any issues, check the console output for error messages

Built with PyInstaller 6.16.0
Generated on: 2025-11-06 22:54:46
