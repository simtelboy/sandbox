#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kiro 登录自动化脚本 - 集成版
功能：连接到 Kiro 应用程序，检测登录按钮，自动启动 EdgeDriver 并完成完整的登录流程
作者：Claude Code Assistant
"""

import time
import sys
import json
import subprocess
import configparser
import os
from pathlib import Path
from pywinauto import Application

class KiroLoginAutomator:
    def __init__(self):
        self.app = None
        self.window = None
        self.login_buttons = []
        self.edge_driver = None
        self.github_automator = None
        self.google_automator = None
        self.aws_automator = None
        self.default_login_method = self.load_default_login_method()

    def load_default_login_method(self):
        """从.env文件加载默认登录方式"""
        try:
            env_path = Path(__file__).parent / '.env'
            if not env_path.exists():
                print("⚠️ .env文件不存在，使用默认值: 2 (GitHub)")
                return 2

            print(f"📁 读取配置文件: {env_path}")

            # 读取.env文件内容
            with open(env_path, 'r', encoding='utf-8') as f:  # 使用utf-8读取不带BOM的.env文件
                content = f.read()
                print(f"📄 .env文件内容预览:\n{content[:200]}...")

            # 手动解析.env文件（避免configparser的BOM问题）
            default_login_method = 2  # 默认值

            lines = content.split('\n')
            current_section = None

            for line_num, line in enumerate(lines, 1):
                line = line.strip()

                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue

                # 检查section标题
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1].strip()
                    print(f"🔍 找到section: [{current_section}]")
                    continue

                # 解析键值对
                if '=' in line and current_section == 'LOGIN':
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    print(f"🔑 LOGIN section - {key} = {value}")

                    if key == 'DEFAULT_LOGIN_METHOD':
                        try:
                            method = int(value)
                            print(f"✅ 找到DEFAULT_LOGIN_METHOD: {method}")

                            # 验证方法值的有效性
                            if method in [1, 2, 3]:
                                method_names = {1: 'Google', 2: 'GitHub', 3: 'AWS Builder ID'}
                                print(f"✅ 登录方式验证通过: {method} = {method_names[method]}")
                                return method
                            else:
                                print(f"⚠️ 无效的登录方式值: {method}，使用默认值: 2 (GitHub)")
                                return 2
                        except ValueError:
                            print(f"⚠️ DEFAULT_LOGIN_METHOD值无法转换为整数: '{value}'，使用默认值: 2 (GitHub)")
                            return 2

            print("⚠️ 未找到LOGIN section中的DEFAULT_LOGIN_METHOD，使用默认值: 2 (GitHub)")
            return 2

        except Exception as e:
            print(f"⚠️ 加载.env配置失败: {e}，使用默认值: 2 (GitHub)")
            import traceback
            print(f"详细错误信息: {traceback.format_exc()}")
            return 2

    def load_manual_mode_setting(self):
        """从.env文件加载手动化模式设置"""
        try:
            env_path = Path(__file__).parent / '.env'
            if not env_path.exists():
                print("⚠️ .env文件不存在，使用默认值: false (自动化)")
                return False

            # 读取.env文件内容
            with open(env_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')
            current_section = None

            for line in lines:
                line = line.strip()

                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue

                # 检查section标题
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1].strip()
                    continue

                # 解析键值对
                if '=' in line and current_section == 'REGISTRATION':
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    if key == 'ENABLE_MANUAL_MODE':
                        manual_mode = value.lower() in ['true', '1', 'yes', 'on']
                        mode_text = "手动化" if manual_mode else "自动化"
                        print(f"✅ 找到ENABLE_MANUAL_MODE: {value} -> {mode_text}")
                        return manual_mode

            print("⚠️ 未找到REGISTRATION section中的ENABLE_MANUAL_MODE，使用默认值: false (自动化)")
            return False

        except Exception as e:
            print(f"⚠️ 加载手动化模式设置失败: {e}，使用默认值: false (自动化)")
            return False

    def click_login_button_and_handle_automation(self, button):
        """点击登录按钮，捕获URL，根据登录方式调用相应的自动化脚本"""
        try:
            print(f"🖱️ 点击 '{button['description']}' 按钮...")

            # 点击登录按钮
            ctrl = button['ctrl']

            # 验证按钮是否仍然有效
            try:
                if not ctrl.exists():
                    print("❌ 按钮不存在")
                    return False
                if not ctrl.is_visible():
                    print("❌ 按钮不可见")
                    return False
                if not ctrl.is_enabled():
                    print("❌ 按钮被禁用")
                    return False
                print("✅ 按钮验证通过")
            except Exception as e:
                print(f"⚠️ 按钮验证失败: {e}")

            print("🖱️ 执行按钮点击...")

            # 尝试多种点击方法
            click_success = False

            # 方法1：设置焦点后发送回车键
            try:
                ctrl.set_focus()
                time.sleep(0.5)
                ctrl.type_keys("{ENTER}")
                click_success = True
                print("✅ 登录按钮点击成功 (方法1: 焦点+回车)")
            except Exception as e:
                print(f"⚠️ 方法1失败: {e}")

                # 方法2：直接点击
                try:
                    ctrl.click()
                    click_success = True
                    print("✅ 登录按钮点击成功 (方法2: 直接点击)")
                except Exception as e2:
                    print(f"⚠️ 方法2失败: {e2}")

                    # 方法3：坐标点击
                    try:
                        rect = ctrl.rectangle()
                        center_x = rect.left + rect.width() // 2
                        center_y = rect.top + rect.height() // 2
                        print(f"🔍 尝试坐标点击: ({center_x}, {center_y})")
                        ctrl.click_input(coords=(center_x, center_y))
                        click_success = True
                        print("✅ 登录按钮点击成功 (方法3: 坐标点击)")
                    except Exception as e3:
                        print(f"⚠️ 方法3失败: {e3}")

            if not click_success:
                print("❌ 所有点击方法都失败了")
                return False

            # 根据按钮类型确定期望的平台类型
            button_name = button['name'].lower()
            match_type = button.get('match_type', 'github')

            # 确定平台类型和默认URL
            if 'google' in button_name or match_type == 'google':
                platform_type = 'google'
                default_url = "https://accounts.google.com/signin"
                platform_name = "Google"
            elif 'aws' in button_name or 'builder' in button_name or match_type == 'aws':
                platform_type = 'aws'
                default_url = "https://us-east-1.signin.aws/platform/login"
                platform_name = "AWS Builder ID"
            else:
                platform_type = 'github'
                default_url = "https://github.com/login"
                platform_name = "GitHub"

            # 等待系统浏览器启动并捕获正确的平台URL
            print(f"⏳ 等待系统浏览器启动并完成重定向到{platform_name}...")
            oauth_url = None
            max_wait_time = 45  # 增加到45秒，给重定向更多时间
            check_interval = 2  # 每2秒检查一次，减少频率

            for elapsed in range(0, max_wait_time, check_interval):
                time.sleep(check_interval)

                # 尝试捕获系统浏览器URL
                captured_url = self.capture_system_browser_url()

                if captured_url:
                    print(f"🔍 捕获到URL: {captured_url[:100]}...")

                    # 检查URL特征，确保是正确的平台URL
                    if self.is_valid_platform_url(captured_url, platform_type):
                        print(f"✅ 确认为有效的{platform_name} URL")
                        oauth_url = captured_url

                        # 关闭系统浏览器
                        self.close_system_browser()
                        break
                    else:
                        print(f"⏳ 等待重定向到{platform_name}... (当前: {self.get_url_type(captured_url)})")

                if elapsed % 6 == 0:  # 每6秒报告一次
                    print(f"⏳ 等待{platform_name}重定向... ({elapsed}s)")

            if not oauth_url:
                print(f"⚠️ 未捕获到有效的{platform_name} URL，使用默认{platform_name}登录页面")
                oauth_url = default_url

            # 保存捕获的URL为实例变量，供后续自动化脚本使用
            self.captured_oauth_url = oauth_url
            print(f"📋 已保存OAuth URL: {oauth_url[:80]}...")

            # 检查是否启用手动化模式
            manual_mode = self.load_manual_mode_setting()
            mode_text = "手动化" if manual_mode else "自动化"
            print(f"🎛️ 注册模式: {mode_text}")

            if manual_mode:
                # 手动化模式：调用手动注册自动化脚本
                print(f"🖐️ 启用手动化模式，将调用手动注册脚本...")
                return self.execute_manual_automation(oauth_url, platform_name)
            else:
                # 自动化模式：根据按钮类型决定调用哪个自动化脚本
                print(f"🤖 启用自动化模式，根据登录方式 '{button['name']}' 初始化相应的自动化脚本...")

            try:
                sys.path.append(str(Path(__file__).parent))

                if platform_type == 'github':
                    # GitHub 自动化 - 新的分离式流程
                    from github_registration_automation import GitHubRegistrationAutomator
                    self.github_automator = GitHubRegistrationAutomator()  # 不传入URL
                    self.github_automator.load_hardware_fingerprints()

                    # 步骤1：先初始化EdgeDriver（不导航）
                    if self.github_automator.setup_edge_driver():
                        print("✅ GitHub EdgeDriver 初始化成功")

                        # 步骤2：然后导航到捕获的URL
                        if self.github_automator.navigate_to_url(oauth_url):
                            print("✅ 成功导航到GitHub页面")
                            time.sleep(3)
                            return self.execute_github_automation()
                        else:
                            print("❌ 导航到GitHub页面失败")
                            return False
                    else:
                        print("❌ GitHub EdgeDriver 初始化失败")
                        return False

                elif platform_type == 'google':
                    # Google 自动化
                    try:
                        from google_registration_automation import GoogleRegistrationAutomator
                        self.google_automator = GoogleRegistrationAutomator(initial_url=oauth_url)
                        print("✅ Google 自动化模块已加载")
                        return self.execute_google_automation()
                    except ImportError:
                        print("⚠️ google_registration_automation.py 文件不存在，Google自动化功能暂不可用")
                        print("💡 请在浏览器中手动完成 Google 注册流程")
                        return True

                elif platform_type == 'aws':
                    # AWS Builder ID 自动化
                    try:
                        from aws_registration_automation import AWSRegistrationAutomator
                        self.aws_automator = AWSRegistrationAutomator(initial_url=oauth_url)
                        print("✅ AWS Builder ID 自动化模块已加载")
                        return self.execute_aws_automation()
                    except ImportError:
                        print("⚠️ aws_registration_automation.py 文件不存在，AWS Builder ID自动化功能暂不可用")
                        print("💡 请在浏览器中手动完成 AWS Builder ID 注册流程")
                        return True

                else:
                    print(f"⚠️ 未识别的登录方式: {button['name']}，尝试使用GitHub自动化")
                    from github_registration_automation import GitHubRegistrationAutomator
                    self.github_automator = GitHubRegistrationAutomator(initial_url=oauth_url)
                    self.github_automator.load_hardware_fingerprints()

                    if self.github_automator.setup_edge_driver():
                        print("✅ 默认GitHub EdgeDriver 初始化成功")
                        time.sleep(3)
                        return self.execute_github_automation()
                    else:
                        print("❌ 默认GitHub EdgeDriver 初始化失败")
                        return False

            except Exception as e:
                print(f"❌ 自动化脚本初始化过程失败: {e}")
                return False

        except Exception as e:
            print(f"❌ 点击按钮并处理自动化失败: {e}")
            return False

    def execute_github_automation(self):
        """执行GitHub自动化流程"""
        try:
            print("🌐 开始执行 GitHub 注册自动化...")

            # 等待 GitHub 登录页面
            if self.github_automator.wait_for_github_login_page():
                print("✅ GitHub 登录页面加载成功")

                # 获取当前页面信息
                self.github_automator.get_current_page_info()

                # 点击 "Create an account" 链接
                if self.github_automator.click_create_account_link():
                    print("✅ 成功点击 'Create an account' 链接")

                    # 等待注册页面加载
                    if self.github_automator.wait_for_registration_page():
                        print("✅ GitHub 注册页面加载成功")
                        self.github_automator.get_current_page_info()

                        # 执行自动填写注册表单
                        print("\n📝 开始自动填写注册表单...")
                        if self.github_automator.fill_registration_form():
                            print("✅ 注册表单填写成功")

                            # 处理提交后的页面
                            print("\n🔍 处理提交后的页面...")
                            self.github_automator.handle_post_submission()

                            print("\n🎉 完整的GitHub注册自动化流程执行成功!")
                            print("💡 表单已自动填写并提交")
                            print("🔄 EdgeDriver浏览器将保持打开状态供您查看结果")
                            print("ℹ️ 如需关闭浏览器，请手动关闭窗口")
                        else:
                            print("❌ 注册表单填写失败")
                            print("💡 您可以在浏览器中手动完成注册")

                        return True
                    else:
                        print("❌ 注册页面加载失败")
                else:
                    print("❌ 点击 'Create an account' 链接失败")
            else:
                print("❌ GitHub 登录页面加载失败")

            return False

        except Exception as e:
            print(f"❌ GitHub 自动化过程中发生错误: {e}")
            return False

    def execute_google_automation(self):
        """执行Google自动化流程（完全使用新框架）"""
        try:
            print("🌐 开始执行 Google 注册自动化...")

            # 导入Google自动化模块
            from google_registration_automation import GoogleRegistrationAutomator
            self.google_automator = GoogleRegistrationAutomator(initial_url=self.captured_oauth_url)

            # 加载硬件指纹
            self.google_automator.load_hardware_fingerprints()

            # 直接执行工作流程，让新框架处理一切（EdgeDriver初始化、导航、操作）
            print("🚀 使用新框架执行完整工作流程...")
            return self.google_automator.execute_workflow()

        except Exception as e:
            print(f"❌ Google 自动化过程中发生错误: {e}")
            return False

    def execute_aws_automation(self):
        """执行AWS Builder ID自动化流程"""
        try:
            print("🌐 开始执行 AWS Builder ID 注册自动化...")

            # 加载硬件指纹
            self.aws_automator.load_hardware_fingerprints()

            # 直接执行工作流程，让新框架处理一切（EdgeDriver初始化、导航、操作）
            print("🚀 使用新框架执行完整工作流程...")
            return self.aws_automator.execute_workflow()

        except Exception as e:
            print(f"❌ AWS Builder ID 自动化过程中发生错误: {e}")
            return False

    def execute_manual_automation(self, oauth_url, platform_name):
        """执行手动注册自动化流程"""
        try:
            print(f"🖐️ 开始执行手动注册模式 - {platform_name}...")

            # 导入手动注册自动化模块
            try:
                from manual_registration_automation import ManualRegistrationAutomator
                self.manual_automator = ManualRegistrationAutomator(initial_url=oauth_url)
                print("✅ 手动注册自动化模块已加载")
            except ImportError:
                print("❌ manual_registration_automation.py 文件不存在，手动注册功能不可用")
                print("💡 请检查文件是否存在于正确位置")
                return False

            # 加载硬件指纹
            self.manual_automator.load_hardware_fingerprints()

            # 执行手动注册工作流程
            print("🚀 启动手动注册模式...")
            result = self.manual_automator.execute_workflow()

            if result:
                print(f"✅ 手动注册模式启动成功 - {platform_name}")
                print("🌐 浏览器已打开并导航到目标页面")
                print("📝 请手动完成注册流程")
                print("🔄 浏览器将保持打开状态供您操作")
                return True
            else:
                print(f"❌ 手动注册模式启动失败 - {platform_name}")
                return False

        except Exception as e:
            print(f"❌ 手动注册自动化过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False

    def connect_to_kiro(self):
        """连接到 Kiro 应用程序"""
        print("🔗 正在连接到 Kiro 应用程序...")

        # 使用成功的连接方法（方法9：通过 Kiro 标题连接）
        connection_attempts = [
            lambda: Application(backend="uia").connect(title_re=".*Kiro.*", timeout=10),
            lambda: Application(backend="win32").connect(title_re=".*Kiro.*", timeout=10),
            lambda: Application(backend="uia").connect(title_re=".*Getting started.*", timeout=10),
            lambda: Application(backend="win32").connect(title_re=".*Getting started.*", timeout=10),
        ]

        for i, attempt in enumerate(connection_attempts, 1):
            try:
                print(f"   尝试方法 {i}...")
                self.app = attempt()
                print(f"✅ 连接成功! (方法{i}) PID: {self.app.process}")
                return True
            except Exception as e:
                print(f"   方法 {i} 失败: {str(e)[:50]}...")
                continue

        print("❌ 所有连接方法都失败了")
        return False

    def get_window(self):
        """获取 Kiro 窗口"""
        try:
            windows = self.app.windows()
            if len(windows) == 0:
                print("❌ 未找到窗口")
                return False

            self.window = windows[0]
            window_title = self.window.window_text()
            print(f"✅ 获取到窗口: '{window_title}'")
            return True
        except Exception as e:
            print(f"❌ 获取窗口失败: {e}")
            return False

    def analyze_login_buttons(self):
        """分析登录按钮"""
        print("\n🔍 分析登录按钮...")


        try:
            controls = self.window.descendants()
            print(f"📊 找到 {len(controls)} 个控件")

            # 查找可能的登录按钮
            potential_buttons = []

            # 首先显示所有控件信息以便调试
            print("🔍 显示所有控件信息（前20个）:")
            for i, ctrl in enumerate(controls[:20]):
                try:
                    # 获取控件信息
                    ctrl_type = ""
                    ctrl_name = ""
                    ctrl_text = ""
                    ctrl_class = ""

                    if hasattr(ctrl, 'element_info'):
                        try:
                            ctrl_type = ctrl.element_info.control_type
                            ctrl_name = ctrl.element_info.name or ""
                        except:
                            pass

                    try:
                        ctrl_text = ctrl.window_text() or ""
                    except:
                        pass

                    try:
                        ctrl_class = ctrl.class_name() if hasattr(ctrl, 'class_name') else ""
                    except:
                        pass

                    print(f"   {i}: 类型={ctrl_type}, 名称='{ctrl_name}', 文本='{ctrl_text}', 类名='{ctrl_class}'")

                except Exception as e:
                    print(f"   {i}: 获取信息失败: {e}")

            print("\n🔍 查找登录相关控件...")

            for i, ctrl in enumerate(controls):
                try:
                    # 获取控件信息
                    ctrl_type = ""
                    ctrl_name = ""
                    ctrl_text = ""

                    if hasattr(ctrl, 'element_info'):
                        try:
                            ctrl_type = ctrl.element_info.control_type
                            ctrl_name = ctrl.element_info.name or ""
                        except:
                            pass

                    try:
                        ctrl_text = ctrl.window_text() or ""
                    except:
                        pass

                    # 扩展登录关键词，包含更多可能的文本
                    login_keywords = [
                        "sign in", "google", "github", "aws", "builder", "login", "登录",
                        "sign", "continue", "get started", "start", "begin", "connect",
                        "authenticate", "account", "oauth", "sso"
                    ]
                    combined_text = f"{ctrl_name} {ctrl_text}".lower()

                    # 降低检测门槛：只要包含任何一个关键词就加入候选
                    if any(keyword in combined_text for keyword in login_keywords) or \
                       (ctrl_type and "button" in ctrl_type.lower()) or \
                       (ctrl_text and len(ctrl_text.strip()) > 0):
                        potential_buttons.append({
                            'index': i,
                            'ctrl': ctrl,
                            'type': ctrl_type,
                            'name': ctrl_name,
                            'text': ctrl_text,
                            'combined': combined_text,
                            'class': ctrl.class_name() if hasattr(ctrl, 'class_name') else ""
                        })

                except Exception as e:
                    continue

            print(f"🔍 找到 {len(potential_buttons)} 个可能的登录按钮:")

            # 显示找到的按钮
            for i, btn in enumerate(potential_buttons, 1):
                print(f"   {i}. 类型: {btn['type']}")
                print(f"      名称: '{btn['name']}'")
                print(f"      文本: '{btn['text']}'")
                print(f"      类名: '{btn['class']}'")
                print(f"      索引: {btn['index']}")
                print()

            # 尝试识别具体的登录按钮，放宽条件
            self.login_buttons = []
            seen_buttons = set()  # 用于去重

            for btn in potential_buttons:
                combined = btn['combined']

                # 放宽条件：不仅限于Button类型，也包含其他可点击控件
                if btn['type'] and btn['type'] in ['Document', 'Text', 'Group']:
                    continue  # 跳过明显不可点击的控件

                # 获取按钮位置信息用于去重
                try:
                    rect = btn['ctrl'].rectangle()
                    position_key = f"{rect.left}_{rect.top}_{rect.width()}_{rect.height()}"
                except:
                    position_key = f"{btn['index']}"

                button_info = None

                # 改进的匹配条件 - 更精确的关键词匹配
                button_info = None

                # 优先匹配具体的登录方式
                if "google" in combined and "google" not in seen_buttons:
                    button_info = {
                        'name': 'Google',
                        'description': 'Sign in with Google',
                        'ctrl': btn['ctrl'],
                        'info': btn,
                        'position': position_key,
                        'match_type': 'google'
                    }
                    seen_buttons.add("google")
                elif "github" in combined and "github" not in seen_buttons:
                    button_info = {
                        'name': 'Github',
                        'description': 'Sign in with Github',
                        'ctrl': btn['ctrl'],
                        'info': btn,
                        'position': position_key,
                        'match_type': 'github'
                    }
                    seen_buttons.add("github")
                elif ("aws" in combined or "builder" in combined) and "aws" not in seen_buttons:
                    button_info = {
                        'name': 'AWS Builder ID',
                        'description': 'Sign in with AWS Builder ID',
                        'ctrl': btn['ctrl'],
                        'info': btn,
                        'position': position_key,
                        'match_type': 'aws'
                    }
                    seen_buttons.add("aws")
                elif "organization" in combined and "organization" not in seen_buttons:
                    button_info = {
                        'name': 'Organization',
                        'description': 'Sign in with your organization identity',
                        'ctrl': btn['ctrl'],
                        'info': btn,
                        'position': position_key,
                        'match_type': 'organization'
                    }
                    seen_buttons.add("organization")
                elif any(keyword in combined for keyword in ["connect", "start", "continue"]) and \
                     btn['type'] and "button" in btn['type'].lower() and "generic" not in seen_buttons:
                    # 通用登录按钮
                    button_info = {
                        'name': 'Generic Login',
                        'description': f'通用登录按钮 ({btn["name"] or btn["text"] or "未知"})',
                        'ctrl': btn['ctrl'],
                        'info': btn,
                        'position': position_key,
                        'match_type': 'generic'
                    }
                    seen_buttons.add("generic")

                if button_info:
                    self.login_buttons.append(button_info)

            print(f"✅ 识别出 {len(self.login_buttons)} 个登录选项:")
            for i, btn in enumerate(self.login_buttons, 1):
                try:
                    rect = btn['ctrl'].rectangle()
                    position_info = f"位置: ({rect.left},{rect.top}) 大小: {rect.width()}x{rect.height()}"
                except:
                    position_info = f"索引: {btn['info']['index']}"
                print(f"   {i}. {btn['description']} ({position_info})")

            return len(self.login_buttons) > 0

        except Exception as e:
            print(f"❌ 分析登录按钮失败: {e}")
            return False

    def auto_select_login_method(self):
        """根据.env配置自动选择登录方式（支持用户5秒内手动选择）"""
        if not self.login_buttons:
            print("❌ 未找到登录按钮")
            return None

        print("\n🎯 自动选择登录方式:")
        for i, btn in enumerate(self.login_buttons, 1):
            try:
                rect = btn['ctrl'].rectangle()
                position_info = f"位置: ({rect.left},{rect.top})"
            except:
                position_info = f"索引: {btn['info']['index']}"
            print(f"   {i}. {btn['description']} ({position_info})")

        # 根据.env配置的默认方式选择按钮
        method_names = {
            1: 'google',
            2: 'github',
            3: 'aws'
        }

        default_method_name = method_names.get(self.default_login_method, 'github')
        print(f"📋 .env配置的默认登录方式: {self.default_login_method} ({default_method_name})")

        # 查找对应的按钮 - 使用match_type进行精确匹配
        selected_button = None
        print(f"🔍 在 {len(self.login_buttons)} 个按钮中查找 '{default_method_name}' 登录方式...")

        # 首先尝试使用match_type进行精确匹配
        for btn in self.login_buttons:
            match_type = btn.get('match_type', '')
            print(f"   检查按钮: description='{btn['description']}', match_type='{match_type}'")

            if default_method_name == match_type:
                selected_button = btn
                print(f"   ✅ 精确匹配到{default_method_name}按钮")
                break

        # 如果精确匹配失败，尝试描述文本匹配
        if not selected_button:
            print(f"⚠️ 精确匹配失败，尝试描述文本匹配...")

            for btn in self.login_buttons:
                btn_description = btn['description'].lower()
                print(f"   文本匹配检查: '{btn['description']}'")

                if default_method_name == 'google' and 'google' in btn_description:
                    selected_button = btn
                    print(f"   ✅ 文本匹配到Google按钮")
                    break
                elif default_method_name == 'github' and 'github' in btn_description:
                    selected_button = btn
                    print(f"   ✅ 文本匹配到GitHub按钮")
                    break
                elif default_method_name == 'aws' and ('aws' in btn_description or 'builder' in btn_description):
                    selected_button = btn
                    print(f"   ✅ 文本匹配到AWS Builder ID按钮")
                    break

        if not selected_button:
            # 最后的备用方案：选择第一个可用的按钮
            if self.login_buttons:
                selected_button = self.login_buttons[0]
                print(f"⚠️ 所有匹配都失败，自动选择第一个可用选项: {selected_button['description']}")
            else:
                print("❌ 没有可用的登录按钮")
                return None

        print(f"🤖 自动选择: {selected_button['description']}")
        print("⏰ 您有5秒时间手动选择其他选项（按Ctrl+C中断自动选择）...")

        # 给用户5秒时间手动选择
        try:
            for i in range(5, 0, -1):
                print(f"   {i}秒后将自动选择 {selected_button['description']}")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⚠️ 用户中断了自动选择")
            return None

        return selected_button

    def is_valid_platform_url(self, url, platform_type):
        """检查URL是否为有效的平台URL"""
        try:
            if not url:
                return False

            if platform_type == 'github':
                # GitHub URL特征
                github_indicators = [
                    "github.com/login",
                    "github.com/signup",
                    "github.com/session"
                ]

                # 检查是否包含GitHub域名和相关路径
                for indicator in github_indicators:
                    if indicator in url:
                        return True

                # 检查是否是GitHub域名但路径不同
                if "github.com" in url and ("client_id=" in url or "oauth" in url):
                    return True

            elif platform_type == 'google':
                # Google URL特征
                google_indicators = [
                    "accounts.google.com",
                    "accounts.google.com/signin",
                    "accounts.google.com/signup",
                    "accounts.google.com/v3/signin"
                ]

                # 检查是否包含Google域名和相关路径
                for indicator in google_indicators:
                    if indicator in url:
                        return True

            elif platform_type == 'aws':
                # AWS Builder ID URL特征
                aws_indicators = [
                    "signin.aws",
                    "us-east-1.signin.aws",
                    "signin.aws/platform",
                    "builder"
                ]

                # 检查是否包含AWS域名和相关路径
                for indicator in aws_indicators:
                    if indicator in url:
                        return True

            return False

        except Exception as e:
            print(f"[ERROR] URL验证失败: {e}")
            return False

    def get_url_type(self, url):
        """获取URL类型描述"""
        try:
            if not url:
                return "空URL"

            if "github.com" in url:
                return "GitHub"
            elif "accounts.google.com" in url:
                return "Google"
            elif "signin.aws" in url:
                return "AWS Builder ID"
            elif "kiro" in url or "auth.desktop" in url:
                return "Kiro认证服务器"
            elif "localhost" in url:
                return "本地回调"
            else:
                return "其他"

        except:
            return "未知"

    def capture_system_browser_url(self):
        """使用 pywinauto 捕获系统浏览器地址栏 URL"""
        print("🔍 开始捕获系统浏览器地址栏 URL...")

        try:
            from pywinauto import Application, findwindows

            # 查找 Edge 窗口
            edge_windows = []

            # 策略A：通过标题查找
            title_patterns = [
                ".*Microsoft Edge.*",
                ".*Edge.*",
                ".*msedge.*",
                ".*- Microsoft Edge$"
            ]

            for pattern in title_patterns:
                try:
                    handles = findwindows.find_windows(title_re=pattern)
                    if handles:
                        print(f"   通过标题模式找到 {len(handles)} 个窗口")
                        edge_windows.extend(handles)
                except:
                    continue

            # 去重
            edge_windows = list(set(edge_windows))
            print(f"📊 总共找到 {len(edge_windows)} 个唯一的 Edge 窗口")

            if not edge_windows:
                print("❌ 未找到 Edge 浏览器窗口")
                return None

            # 尝试从每个窗口提取 URL
            for attempt, handle in enumerate(edge_windows, 1):
                print(f"🔄 尝试窗口 {attempt}/{len(edge_windows)}")

                try:
                    # 连接到窗口
                    app = Application(backend="uia").connect(handle=handle)
                    window = app.top_window()
                    window_title = window.window_text()
                    print(f"   窗口标题: '{window_title}'")

                    # 尝试激活窗口
                    try:
                        window.set_focus()
                        time.sleep(0.5)
                        print("   ✅ 窗口已激活")
                    except:
                        print("   ⚠️ 无法激活窗口，继续尝试...")

                    # 使用测试中成功的方法D：查找第一个 Edit 控件
                    try:
                        print("   🔍 尝试方法D: 查找第一个 Edit 控件...")
                        edit_ctrl = window.child_window(control_type="Edit", found_index=0)
                        url = edit_ctrl.get_value()

                        if url and len(url.strip()) > 0:
                            print(f"   ✅ 获取到内容: {url}")

                            # 验证 URL 格式
                            if url.startswith(('http://', 'https://')):
                                print(f"   ✅ URL 格式验证通过")
                                return url
                            else:
                                print(f"   ⚠️ 内容不是 URL 格式: {url}")
                        else:
                            print(f"   ❌ 未获取到内容或内容为空")

                    except Exception as e:
                        print(f"   ❌ 方法D失败: {e}")

                except Exception as e:
                    print(f"   ❌ 连接窗口 {attempt} 失败: {e}")

            print("❌ 所有窗口的 URL 提取都失败了")
            return None

        except Exception as e:
            print(f"❌ URL 捕获过程失败: {e}")
            return None

    def close_system_browser(self):
        """通过点击关闭按钮关闭系统浏览器窗口"""
        try:
            print("🔒 正在关闭系统浏览器...")

            # 重用URL捕获时的窗口查找逻辑
            from pywinauto import Application

            app = Application(backend="uia")
            edge_windows = []

            # 查找Edge窗口（复用capture_system_browser_url的逻辑）
            try:
                # 通过标题模式查找Edge窗口
                windows = app.windows()
                for window in windows:
                    title = window.window_text()
                    if "Microsoft​ Edge" in title:
                        edge_windows.append(window)

                print(f"   找到 {len(edge_windows)} 个Edge窗口")

                # 关闭系统浏览器窗口
                closed_count = 0
                for window in edge_windows:
                    try:
                        title = window.window_text()
                        # 只关闭包含"无标题"的系统浏览器，不关闭自动化浏览器
                        if "无标题" in title:
                            print(f"   🎯 准备关闭窗口: {title}")

                            # 查找并点击关闭按钮
                            try:
                                # 查找关闭按钮（通常是窗口右上角的X按钮）
                                close_button = window.child_window(title="关闭", control_type="Button")
                                if close_button.exists():
                                    close_button.click()
                                    closed_count += 1
                                    print(f"   ✅ 已点击关闭按钮关闭窗口")
                                else:
                                    # 尝试其他可能的关闭按钮标识
                                    try:
                                        close_button = window.child_window(title="Close", control_type="Button")
                                        if close_button.exists():
                                            close_button.click()
                                            closed_count += 1
                                            print(f"   ✅ 已点击Close按钮关闭窗口")
                                        else:
                                            # 备用方案：直接关闭窗口
                                            window.close()
                                            closed_count += 1
                                            print(f"   ✅ 已直接关闭窗口")
                                    except:
                                        window.close()
                                        closed_count += 1
                                        print(f"   ✅ 已直接关闭窗口")

                            except Exception as e:
                                print(f"   ⚠️ 点击关闭按钮失败，尝试直接关闭: {e}")
                                window.close()
                                closed_count += 1
                                print(f"   ✅ 已直接关闭窗口")

                    except Exception as e:
                        print(f"   ⚠️ 关闭窗口失败: {e}")

                if closed_count > 0:
                    print(f"✅ 成功关闭 {closed_count} 个系统浏览器窗口")
                else:
                    print("ℹ️ 未找到需要关闭的系统浏览器窗口")

            except Exception as e:
                print(f"⚠️ 查找Edge窗口失败: {e}")

        except Exception as e:
            print(f"❌ 关闭系统浏览器失败: {e}")

    def run_integrated_automation(self):
        """运行集成的完整自动化流程（无人看守模式）"""
        print("🚀 Kiro 登录自动化脚本 - 集成版")
        print("=" * 50)

        # 步骤1：连接到 Kiro
        print("\n🔗 步骤1：连接到 Kiro 应用程序...")
        if not self.connect_to_kiro():
            return False

        # 步骤2：获取窗口
        print("\n🪟 步骤2：获取 Kiro 窗口...")
        if not self.get_window():
            return False

        # 步骤3：等待界面稳定
        print("\n⏳ 步骤3：等待界面稳定...")
        time.sleep(3)

        # 步骤4：分析登录按钮
        print("\n🔍 步骤4：分析登录按钮...")
        if not self.analyze_login_buttons():
            print("❌ 未找到登录按钮，可能需要手动操作")
            return False

        # 步骤5：根据.env配置自动选择登录方式
        print("\n🎯 步骤5：自动选择登录方式...")
        selected_button = self.auto_select_login_method()
        if not selected_button:
            print("❌ 无法选择登录按钮")
            return False

        # 步骤6：点击按钮并捕获系统浏览器URL，然后初始化EdgeDriver并执行完整自动化
        print("\n🖱️ 步骤6：点击登录按钮并处理后续流程...")
        if not self.click_login_button_and_handle_automation(selected_button):
            print("❌ 登录按钮点击或后续自动化失败")
            return False

        print("\n🎉 所有步骤完成！")
        return True

    def run(self):
        """运行主程序（保持向后兼容）"""
        return self.run_integrated_automation()

def main():
    """主函数"""
    try:
        automator = KiroLoginAutomator()
        automator.run()
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()