#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 注册自动化脚本
功能：自动化 GitHub 账号注册流程
作者：Claude Code Assistant
使用 Edge 浏览器进行网页自动化
"""

import time
import sys
import json
import random
import string
import os
import shutil
import glob
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from webdriver_manager.microsoft import EdgeChromiumDriverManager

class GitHubRegistrationAutomator:
    def __init__(self, initial_url=None):
        self.driver = None
        self.wait = None
        self.fingerprints = {}
        self.initial_url = initial_url
        # 尝试多个可能的name.txt文件路径
        possible_paths = [
            "C:\\sandbox_files\\name.txt",
            "sandbox_files\\name.txt",
            "name.txt"
        ]
        self.name_file_path = None
        for path in possible_paths:
            if Path(path).exists():
                self.name_file_path = path
                break
        if not self.name_file_path:
            self.name_file_path = possible_paths[0]  # 默认使用第一个路径

    def get_email_domain_from_env(self):
        """从.env文件读取邮箱域名配置"""
        try:
            env_path = Path(__file__).parent / ".env"
            if not env_path.exists():
                print(f"[WARNING] .env文件不存在: {env_path}")
                return None

            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if line.startswith('EMAIL_DOMAIN='):
                    email_domain = line.split('=', 1)[1].strip()
                    print(f"[INFO] 从.env文件读取邮箱域名: {email_domain}")
                    return email_domain

            print("[WARNING] .env文件中未找到EMAIL_DOMAIN配置")
            return None

        except Exception as e:
            print(f"[ERROR] 读取.env文件失败: {e}")
            return None

    def load_hardware_fingerprints(self):
        """加载硬件指纹配置"""
        config_path = Path(__file__).parent / "config.json"
        try:
            with open(config_path, 'r', encoding='utf-8-sig') as f:
                self.fingerprints = json.load(f)
                print("[INFO] 硬件指纹配置加载成功")
                print(f"[INFO] User-Agent: {self.fingerprints.get('Browser_UserAgent', 'null')}")
                print(f"[INFO] 语言设置: {self.fingerprints.get('Browser_AcceptLanguage', 'null')}")
                print(f"[INFO] 屏幕分辨率: {self.fingerprints.get('Screen_Resolution', 'null')}")
                print(f"[INFO] WebGL供应商: {self.fingerprints.get('WebGL_Vendor', 'null')}")
                print(f"[INFO] WebGL渲染器: {self.fingerprints.get('WebGL_Renderer', 'null')}")
                print(f"[INFO] Canvas指纹: {self.fingerprints.get('Canvas_Fingerprint', 'null')}")
                print(f"[INFO] 音频指纹: {self.fingerprints.get('AudioContext_Fingerprint', 'null')}")
                print(f"[INFO] 时区偏移: {self.fingerprints.get('Timezone_Offset', 'null')}")
                print(f"[INFO] DoNotTrack: {self.fingerprints.get('DoNotTrack', 'null')}")
        except Exception as e:
            print(f"[WARNING] 无法加载硬件指纹配置: {e}")
            self.fingerprints = {}

    def copy_aws_sso_cache_files(self):
        """将AWS SSO缓存文件拷贝到sandbox_files/OAuth目录并重命名"""
        try:
            print("[INFO] 开始查找AWS SSO缓存文件...")

            # 直接获取当前用户主目录
            user_home = os.path.expanduser("~")
            print(f"[INFO] 当前用户主目录: {user_home}")

            # AWS SSO缓存目录路径
            aws_sso_cache_dir = os.path.join(user_home, ".aws", "sso", "cache")
            print(f"[INFO] AWS SSO缓存目录: {aws_sso_cache_dir}")

            # 目标目录
            target_dir = os.path.join(os.path.dirname(__file__), "OAuth")
            os.makedirs(target_dir, exist_ok=True)
            print(f"[INFO] 目标目录: {target_dir}")

            # 检查AWS SSO缓存目录是否存在
            if not os.path.exists(aws_sso_cache_dir):
                print(f"[WARNING] AWS SSO缓存目录不存在: {aws_sso_cache_dir}")
                print("[INFO] 可能的原因：")
                print("  1. 还没有进行过AWS SSO登录")
                print("  2. AWS CLI未安装或未配置")
                return False

            # 查找所有json文件
            json_files = glob.glob(os.path.join(aws_sso_cache_dir, "*.json"))
            print(f"[INFO] 找到 {len(json_files)} 个JSON文件")

            if not json_files:
                print(f"[WARNING] AWS SSO缓存目录中没有找到json文件")
                print("[INFO] 可能的原因：")
                print("  1. 缓存文件已过期被清理")
                print("  2. 还没有进行过AWS SSO登录")
                return False

            # 获取账号信息用于文件命名
            test_data = self.get_last_test_data()
            if not test_data:
                print("[WARNING] 无法获取账号信息，使用默认命名")
                email = "unknown@example.com"
                account_type = "github"
            else:
                email = test_data.get('email', 'unknown@example.com')
                account_type = "github"  # 当前固定为github

            # 生成时间戳
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            print(f"[INFO] 开始拷贝并重命名AWS SSO缓存文件...")
            print(f"[INFO] 账号信息: {email} ({account_type})")
            print(f"[INFO] 注册时间: {timestamp}")

            copied_count = 0
            for json_file in json_files:
                try:
                    original_filename = os.path.basename(json_file)
                    file_base = os.path.splitext(original_filename)[0]  # 去掉.json扩展名

                    # 生成新的文件名: 原文件名__邮箱__账号类型__注册时间.json
                    new_filename = f"{file_base}__{email}__{account_type}__{timestamp}.json"
                    target_path = os.path.join(target_dir, new_filename)

                    # 显示文件信息
                    file_size = os.path.getsize(json_file)
                    print(f"[INFO] 正在拷贝: {original_filename} -> {new_filename}")
                    print(f"[INFO] 文件大小: {file_size} bytes")

                    shutil.copy2(json_file, target_path)
                    print(f"[SUCCESS] 已拷贝并重命名: {new_filename}")
                    copied_count += 1

                except Exception as e:
                    print(f"[ERROR] 拷贝文件失败 {json_file}: {e}")

            if copied_count > 0:
                print(f"[SUCCESS] AWS SSO缓存文件拷贝完成，共拷贝 {copied_count} 个文件")

                # 验证拷贝结果
                target_files = glob.glob(os.path.join(target_dir, "*.json"))
                print(f"[VERIFY] 目标目录中现有 {len(target_files)} 个JSON文件")
                for target_file in target_files:
                    filename = os.path.basename(target_file)
                    file_size = os.path.getsize(target_file)
                    print(f"[VERIFY] - {filename} ({file_size} bytes)")

                return True
            else:
                print("[ERROR] 没有成功拷贝任何文件")
                return False

        except Exception as e:
            print(f"[ERROR] AWS SSO缓存文件拷贝过程中发生错误: {e}")
            return False

    def setup_edge_driver(self):
        """配置 Edge 浏览器驱动"""
        print("[INFO] 配置 Edge 浏览器驱动...")

        try:
            # Edge 选项配置
            edge_options = EdgeOptions()

            # 基本设置
            edge_options.add_argument("--no-sandbox")
            edge_options.add_argument("--disable-dev-shm-usage")
            edge_options.add_argument("--disable-blink-features=AutomationControlled")

            edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            edge_options.add_experimental_option('useAutomationExtension', False)

            # 应用硬件指纹 - 确保即使没有配置文件也有默认处理
            user_agent = None
            if self.fingerprints:
                # 检查并应用 User-Agent
                user_agent = self.fingerprints.get('Browser_UserAgent')
                if not user_agent or user_agent == "null":
                    # 生成随机User-Agent作为fallback
                    user_agent = self.generate_random_user_agent()
                    print(f"[INFO] 使用随机生成的 User-Agent: {user_agent[:50]}...")
                else:
                    print(f"[INFO] 应用配置文件中的 User-Agent: {user_agent[:50]}...")

                # 检查并应用语言设置
                accept_language = self.fingerprints.get('Browser_AcceptLanguage')
                if accept_language and accept_language != "null":
                    edge_options.add_argument(f"--lang={accept_language.split(',')[0]}")
                    print(f"[INFO] 应用语言设置: {accept_language}")
                else:
                    print("[WARNING] Browser_AcceptLanguage 为空或 null，跳过设置")

                # 检查并应用屏幕分辨率
                screen_resolution = self.fingerprints.get('Screen_Resolution')
                if screen_resolution and screen_resolution != "null":
                    width, height = screen_resolution.split('x')
                    edge_options.add_argument(f"--window-size={width},{height}")
                    print(f"[INFO] 应用屏幕分辨率: {width}x{height}")
                else:
                    print("[WARNING] Screen_Resolution 为空或 null，跳过设置")
            else:
                # 没有配置文件时的默认处理 - 生成完整随机指纹
                print("[WARNING] 未加载硬件指纹配置，生成随机指纹")
                self.fingerprints = self.generate_random_fingerprints()
                user_agent = self.fingerprints.get('Browser_UserAgent')
                print(f"[INFO] 使用随机生成的完整指纹集")
                print(f"[INFO] User-Agent: {user_agent[:50]}...")
                print(f"[INFO] WebGL: {self.fingerprints.get('WebGL_Vendor')} / {self.fingerprints.get('WebGL_Renderer')[:30]}...")
                print(f"[INFO] 屏幕分辨率: {self.fingerprints.get('Screen_Resolution')}")

                # 应用随机生成的指纹
                accept_language = self.fingerprints.get('Browser_AcceptLanguage')
                if accept_language:
                    edge_options.add_argument(f"--lang={accept_language.split(',')[0]}")
                    print(f"[INFO] 应用随机语言设置: {accept_language}")

                screen_resolution = self.fingerprints.get('Screen_Resolution')
                if screen_resolution:
                    width, height = screen_resolution.split('x')
                    edge_options.add_argument(f"--window-size={width},{height}")
                    print(f"[INFO] 应用随机屏幕分辨率: {width}x{height}")

            # 确保总是设置User-Agent
            if user_agent:
                edge_options.add_argument(f"--user-agent={user_agent}")
            else:
                # 最后的fallback
                default_user_agent = self.generate_random_user_agent()
                edge_options.add_argument(f"--user-agent={default_user_agent}")
                print(f"[INFO] 使用最终fallback User-Agent: {default_user_agent[:50]}...")

            # 启动 Edge - 尝试多种方法
            try:
                # 方法1: 使用 WebDriver Manager 自动下载
                print("[INFO] 尝试使用 WebDriver Manager 下载 EdgeDriver...")
                service = EdgeService(EdgeChromiumDriverManager().install())
                self.driver = webdriver.Edge(service=service, options=edge_options)
                print("[SUCCESS] 使用 WebDriver Manager 成功启动 Edge")
            except Exception as e1:
                print(f"[WARNING] WebDriver Manager 失败: {e1}")

                try:
                    # 方法2: 使用系统默认的 EdgeDriver
                    print("[INFO] 尝试使用系统默认 EdgeDriver...")
                    self.driver = webdriver.Edge(options=edge_options)
                    print("[SUCCESS] 使用系统默认 EdgeDriver 成功启动 Edge")
                except Exception as e2:
                    print(f"[ERROR] 系统默认 EdgeDriver 失败: {e2}")
                    raise Exception("无法启动 Edge 浏览器")

            # 初始化WebDriverWait
            self.wait = WebDriverWait(self.driver, 30)

            # 执行 CDP 命令隐藏自动化特征并应用完整指纹虚拟
            fingerprint_script = '''
                // 隐藏webdriver特征
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });

                // 删除自动化相关属性
                delete navigator.__webdriver_script_fn;
                delete navigator.__webdriver_evaluate;
                delete navigator.__webdriver_unwrapped;
                delete navigator.__fxdriver_evaluate;
                delete navigator.__fxdriver_unwrapped;
                delete navigator.__driver_evaluate;
                delete navigator.__webdriver_script_func;
                delete navigator.__webdriver_script_function;
            '''

            # 添加WebGL指纹虚拟
            if self.fingerprints:
                webgl_vendor = self.fingerprints.get('WebGL_Vendor')
                webgl_renderer = self.fingerprints.get('WebGL_Renderer')
                canvas_fingerprint = self.fingerprints.get('Canvas_Fingerprint')
                audio_fingerprint = self.fingerprints.get('AudioContext_Fingerprint')
                timezone_offset = self.fingerprints.get('Timezone_Offset')
                do_not_track = self.fingerprints.get('DoNotTrack')
                plugins_list = self.fingerprints.get('Plugins_List')

                if webgl_vendor and webgl_vendor != "null":
                    fingerprint_script += f'''
                        // WebGL指纹虚拟
                        const getParameter = WebGLRenderingContext.prototype.getParameter;
                        WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                            if (parameter === 37445) {{
                                return '{webgl_vendor}';
                            }}
                            if (parameter === 37446) {{
                                return '{webgl_renderer}';
                            }}
                            return getParameter.call(this, parameter);
                        }};
                    '''

                if canvas_fingerprint and canvas_fingerprint != "null":
                    fingerprint_script += f'''
                        // Canvas指纹虚拟
                        const toDataURL = HTMLCanvasElement.prototype.toDataURL;
                        HTMLCanvasElement.prototype.toDataURL = function() {{
                            return 'data:image/png;base64,{canvas_fingerprint}';
                        }};
                    '''

                if audio_fingerprint and audio_fingerprint != "null":
                    fingerprint_script += f'''
                        // AudioContext指纹虚拟
                        const createAnalyser = AudioContext.prototype.createAnalyser;
                        AudioContext.prototype.createAnalyser = function() {{
                            const analyser = createAnalyser.call(this);
                            const getFloatFrequencyData = analyser.getFloatFrequencyData;
                            analyser.getFloatFrequencyData = function(array) {{
                                getFloatFrequencyData.call(this, array);
                                for (let i = 0; i < array.length; i++) {{
                                    array[i] = array[i] + Math.random() * 0.0001;
                                }}
                            }};
                            return analyser;
                        }};
                    '''

                if timezone_offset and timezone_offset != "null":
                    fingerprint_script += f'''
                        // 时区偏移虚拟
                        Date.prototype.getTimezoneOffset = function() {{
                            return {timezone_offset};
                        }};
                    '''

                if do_not_track and do_not_track != "null":
                    fingerprint_script += f'''
                        // DoNotTrack设置
                        Object.defineProperty(navigator, 'doNotTrack', {{
                            get: () => '{do_not_track}',
                        }});
                    '''

                if plugins_list and plugins_list != "null":
                    fingerprint_script += f'''
                        // 插件列表虚拟
                        Object.defineProperty(navigator, 'plugins', {{
                            get: () => {{
                                const plugins = '{plugins_list}'.split('; ');
                                return plugins.map((name, index) => ({{
                                    name: name,
                                    filename: name.toLowerCase().replace(/\\s+/g, '') + '.dll',
                                    description: name,
                                    length: 1
                                }}));
                            }},
                        }});
                    '''

            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': fingerprint_script
            })

            print("[SUCCESS] Edge 浏览器驱动配置完成（未导航到URL）")
            return True

        except Exception as e:
            print(f"[ERROR] Edge 驱动配置失败: {e}")
            return False

    def navigate_to_url(self, url):
        """导航到指定URL（独立方法）"""
        try:
            print(f"[INFO] 导航到URL...")
            print(f"[INFO] URL: {url[:100]}...")

            if not self.driver:
                print("[ERROR] EdgeDriver未初始化")
                return False

            self.driver.get(url)
            print("[SUCCESS] 成功导航到页面")

            # 等待页面加载
            time.sleep(3)

            # 获取页面信息
            print(f"[INFO] 页面标题: {self.driver.title}")
            print(f"[INFO] 当前URL: {self.driver.current_url[:100]}...")

            return True

        except Exception as e:
            print(f"[ERROR] 导航失败: {e}")
            return False

    def navigate_to_initial_url(self, url):
        """导航到初始URL（兼容性方法）"""
        return self.navigate_to_url(url)

    def wait_for_github_login_page(self):
        """等待 GitHub 登录页面加载"""
        print("[INFO] 等待 GitHub 登录页面加载...")

        try:
            # 等待页面标题包含 "Sign in to GitHub"
            self.wait.until(lambda driver: "Sign in to GitHub" in driver.title)
            print(f"[SUCCESS] 页面加载完成，标题: {self.driver.title}")

            # 等待页面完全加载
            time.sleep(3)
            return True

        except Exception as e:
            print(f"[ERROR] 等待页面加载失败: {e}")
            return False

    def click_create_account_link(self):
        """点击 'Create an account' 链接"""
        print("[INFO] 查找并点击 'Create an account' 链接...")

        # 多种定位策略
        selectors = [
            # 优先级1: 通过 href 属性定位
            'a[href*="/join"]',
            # 优先级2: 通过文本内容定位
            '//a[contains(text(), "Create an account")]',
            # 优先级3: 通过 data-ga-click 属性定位
            'a[data-ga-click*="switch to sign up"]',
            # 优先级4: 通过完整的 CSS 选择器
            'body > div.logged-out.env-production.page-responsive.session-authentication > div.application-main > main > div > div.authentication-footer > div > p > a'
        ]

        for i, selector in enumerate(selectors, 1):
            try:
                print(f"[INFO] 尝试定位策略 {i}: {selector[:50]}...")

                if selector.startswith('//'):
                    # XPath 选择器
                    element = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                else:
                    # CSS 选择器
                    element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))

                # 滚动到元素位置
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(1)

                # 获取元素文本
                element_text = element.text
                print(f"[INFO] 找到链接，文本: '{element_text}'")

                # 点击元素
                element.click()
                print(f"[SUCCESS] 成功点击 'Create an account' 链接 (策略 {i})")


                # 等待页面跳转
                time.sleep(3)
                return True

            except Exception as e:
                print(f"[WARNING] 策略 {i} 失败: {e}")
                continue

        print("[ERROR] 无法找到 'Create an account' 链接")
        return False

    def wait_for_registration_page(self):
        """等待注册页面加载"""
        print("[INFO] 等待注册页面加载...")

        try:
            # 等待 URL 变化到注册页面 - GitHub的注册页面URL包含signup
            def check_signup_page(driver):
                current_url = driver.current_url
                return ("/signup" in current_url or
                        "/join" in current_url or
                        "Sign up for GitHub" in driver.title)

            self.wait.until(check_signup_page)
            print(f"[SUCCESS] 已跳转到注册页面: {self.driver.current_url}")

            # 等待页面标题变化
            time.sleep(3)
            print(f"[INFO] 当前页面标题: {self.driver.title}")

            return True

        except Exception as e:
            print(f"[ERROR] 等待注册页面失败: {e}")
            print(f"[DEBUG] 当前URL: {self.driver.current_url}")
            print(f"[DEBUG] 当前标题: {self.driver.title}")
            return False

    def get_current_page_info(self):
        """获取当前页面信息用于调试"""
        try:
            print("\n" + "="*50)
            print("[DEBUG] 当前页面信息:")
            print(f"URL: {self.driver.current_url}")
            print(f"标题: {self.driver.title}")
            print(f"页面源码长度: {len(self.driver.page_source)} 字符")
            print("="*50 + "\n")
        except Exception as e:
            print(f"[ERROR] 获取页面信息失败: {e}")

    def close_system_browser(self):
        """关闭原来的系统浏览器窗口"""
        try:
            print("[INFO] 尝试关闭原系统浏览器窗口...")

            # 使用JavaScript关闭其他Edge窗口（除了当前自动化窗口）
            try:
                # 获取当前窗口句柄
                current_window = self.driver.current_window_handle
                all_windows = self.driver.window_handles

                print(f"[INFO] 检测到 {len(all_windows)} 个浏览器窗口")

                # 如果有多个窗口，关闭其他窗口
                if len(all_windows) > 1:
                    for window in all_windows:
                        if window != current_window:
                            try:
                                self.driver.switch_to.window(window)
                                self.driver.close()
                                print(f"[INFO] 已关闭一个浏览器窗口")
                            except Exception as e:
                                print(f"[WARNING] 关闭窗口失败: {e}")

                    # 切换回主窗口
                    self.driver.switch_to.window(current_window)
                    print("[SUCCESS] 已关闭其他浏览器窗口")
                else:
                    print("[INFO] 只有一个浏览器窗口，无需关闭")

            except Exception as e:
                print(f"[WARNING] 通过Selenium关闭窗口失败: {e}")

                # 备用方案：尝试通过进程名关闭系统Edge浏览器
                try:
                    import subprocess
                    # 只关闭非自动化的Edge进程（这个比较危险，暂时注释掉）
                    # subprocess.run(['taskkill', '/f', '/im', 'msedge.exe'],
                    #               capture_output=True, text=True)
                    print("[INFO] 备用关闭方案已跳过（避免关闭自动化浏览器）")
                except Exception as e2:
                    print(f"[WARNING] 备用关闭方案失败: {e2}")

        except Exception as e:
            print(f"[ERROR] 关闭系统浏览器失败: {e}")

    def load_names_from_file(self):
        """从name.txt文件加载姓名列表"""
        try:
            with open(self.name_file_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()

            # 所有行都是姓名（邮箱域名现在从.env文件读取）
            names = [line.strip() for line in lines if line.strip()]

            # 从.env文件读取邮箱域名
            email_domain = self.get_email_domain_from_env()
            if not email_domain:
                print("[WARNING] 无法从.env文件读取邮箱域名，使用默认值")
                email_domain = "kt167.lol"

            print(f"[INFO] 成功加载 {len(names)} 个姓名，邮箱域名: {email_domain}")
            return email_domain, names

        except Exception as e:
            print(f"[ERROR] 加载姓名文件失败: {e}")
            return None, []

    def generate_random_user_agent(self):
        """生成随机化的User-Agent（使用兼容的Edge版本）"""
        # 随机Windows版本 (10.0权重更高)
        windows_versions = ["10.0", "10.0", "10.0", "11.0"]
        win_ver = random.choice(windows_versions)

        # 兼容的Chrome/Edge版本 (110-116，测试验证的安全范围)
        chrome_versions = ["110.0.0.0", "111.0.0.0", "112.0.0.0", "113.0.0.0", "114.0.0.0", "115.0.0.0", "116.0.0.0"]
        chrome_ver = random.choice(chrome_versions)

        user_agent = f"Mozilla/5.0 (Windows NT {win_ver}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36 Edg/{chrome_ver}"
        return user_agent

    def generate_random_fingerprints(self):
        """生成随机浏览器指纹（fallback模式）"""
        print("[INFO] 生成随机浏览器指纹...")

        # 随机WebGL供应商和渲染器
        webgl_vendors = ["NVIDIA Corporation", "Intel Inc.", "AMD", "Google Inc."]
        webgl_renderers = [
            f"NVIDIA GeForce GTX {random.randint(900, 3090)} OpenGL Engine",
            f"Intel(R) UHD Graphics {random.randint(600, 900)}",
            f"ANGLE (NVIDIA, NVIDIA GeForce RTX {random.randint(2000, 4000)} Direct3D11 vs_5_0 ps_5_0)"
        ]

        # 随机Canvas指纹
        canvas_data = str(random.randint(100000000, 999999999)) + str(random.randint(100000000, 999999999))
        canvas_hash = f"canvas_{random.randint(10000000, 99999999):08x}"

        # 随机音频指纹
        audio_hash = f"audio_{random.randint(268435456, 2147483647):08x}"

        # 随机时区偏移 (-720 到 +720 分钟)
        timezone_offset = random.randint(-720, 720)

        # 随机DoNotTrack设置
        do_not_track = random.choice(["0", "1"])

        # 随机插件列表
        plugins = ["Chrome PDF Plugin", "Chrome PDF Viewer", "Native Client"]

        # 随机屏幕分辨率
        screen_resolutions = ["1920x1080", "1366x768", "1536x864", "1280x720", "1440x900", "1600x900"]
        screen_resolution = random.choice(screen_resolutions)

        # 随机语言设置
        languages = ["zh-CN", "en-US", "en-GB", "zh-TW", "ja-JP", "ko-KR"]
        accept_language = ", ".join(random.sample(languages, random.randint(1, 3)))

        return {
            'Browser_UserAgent': self.generate_random_user_agent(),
            'Browser_AcceptLanguage': accept_language,
            'Screen_Resolution': screen_resolution,
            'WebGL_Vendor': random.choice(webgl_vendors),
            'WebGL_Renderer': random.choice(webgl_renderers),
            'Canvas_Fingerprint': canvas_hash,
            'AudioContext_Fingerprint': audio_hash,
            'Timezone_Offset': timezone_offset,
            'DoNotTrack': do_not_track,
            'Plugins_List': "; ".join(plugins)
        }

    def generate_random_name_data(self):
        """生成随机的姓名、邮箱、用户名和密码"""
        try:
            email_domain, names = self.load_names_from_file()
            if not names:
                # 如果无法加载姓名数据，使用简化的随机生成
                print("[WARNING] 无法加载姓名数据，使用随机生成")
                return self.generate_test_data()

            # 随机选择一个姓名
            selected_name = random.choice(names)
            print(f"[INFO] 随机选择姓名: {selected_name}")

            # 生成邮箱地址（用下划线替换空格）
            email_username = selected_name.replace(' ', '_').lower()
            email = f"{email_username}@{email_domain}"

            # 生成用户名（符合GitHub规则：只能包含字母数字和单个连字符）
            # 将下划线替换为连字符，并添加随机数字
            username_base = selected_name.replace(' ', '-').replace('_', '-').lower()
            random_digits = ''.join(random.choices(string.digits, k=random.randint(2, 4)))
            username = f"{username_base}{random_digits}"

            # 确保用户名不以连字符开头或结尾
            username = username.strip('-')
            if not username or username.startswith('-') or username.endswith('-'):
                # 如果处理后的用户名不符合规则，使用纯字母数字格式
                clean_name = ''.join(c for c in selected_name if c.isalnum()).lower()
                username = f"{clean_name}{random_digits}"

            # 生成10位密码（确保包含数字和小写字母）
            # 至少包含1个数字、1个小写字母，其余可以是大小写字母和数字
            password_parts = []
            password_parts.append(random.choice(string.digits))  # 至少1个数字
            password_parts.append(random.choice(string.ascii_lowercase))  # 至少1个小写字母

            # 剩余8位从所有字符中随机选择
            remaining_chars = string.ascii_letters + string.digits
            for _ in range(8):
                password_parts.append(random.choice(remaining_chars))

            # 打乱顺序并组合
            random.shuffle(password_parts)
            password = ''.join(password_parts)

            result = {
                'name': selected_name,
                'email': email,
                'username': username,
                'password': password
            }

            print(f"[INFO] 生成的注册信息:")
            print(f"  姓名: {result['name']}")
            print(f"  邮箱: {result['email']}")
            print(f"  用户名: {result['username']}")
            print(f"  密码: {result['password']}")

            return result

        except Exception as e:
            print(f"[ERROR] 生成随机数据失败: {e}")
            return self.generate_test_data()

    def generate_test_data(self):
        """生成测试用的注册数据（fallback方法）"""
        # 从.env文件读取邮箱域名
        email_domain = self.get_email_domain_from_env()
        if not email_domain:
            print("[WARNING] 无法从.env文件读取邮箱域名，使用默认值")
            email_domain = "kt167.lol"

        # 生成随机邮箱
        random_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        email = f"{random_name}@{email_domain}"

        # 生成用户名
        random_digits = ''.join(random.choices(string.digits, k=3))
        username = f"{random_name}{random_digits}"

        # 生成密码（确保包含数字和小写字母）
        password_parts = []
        password_parts.append(random.choice(string.digits))  # 至少1个数字
        password_parts.append(random.choice(string.ascii_lowercase))  # 至少1个小写字母

        # 剩余8位从所有字符中随机选择
        remaining_chars = string.ascii_letters + string.digits
        for _ in range(8):
            password_parts.append(random.choice(remaining_chars))

        # 打乱顺序并组合
        random.shuffle(password_parts)
        password = ''.join(password_parts)

        return {
            'email': email,
            'username': username,
            'password': password
        }

    def human_like_type(self, element, text, min_delay=0.05, max_delay=0.15):
        """模拟人类打字，逐字符输入"""
        try:
            print(f"[INFO] 开始人性化输入文本: {text[:20]}...")

            # 清空输入框
            element.clear()
            time.sleep(random.uniform(0.1, 0.3))

            # 逐字符输入
            for char in text:
                element.send_keys(char)
                # 随机延迟，模拟人类打字速度
                delay = random.uniform(min_delay, max_delay)
                time.sleep(delay)

            # 输入完成后稍作停顿
            time.sleep(random.uniform(0.2, 0.5))
            print(f"[SUCCESS] 完成输入: {text}")

        except Exception as e:
            print(f"[ERROR] 人性化输入失败: {e}")
            raise

    def fill_registration_form(self):
        """填写注册表单（模拟人类逐字符输入）"""
        try:
            print("[INFO] 开始填写注册表单（人性化输入模式）...")

            # 生成测试数据
            test_data = self.generate_random_name_data()
            if not test_data:
                return False
            # 保存到实例变量，供后续登录使用
            self.current_test_data = test_data
            print(f"[INFO] 生成的测试数据:")
            print(f"  邮箱: {test_data['email']}")
            print(f"  用户名: {test_data['username']}")
            print(f"  密码: {test_data['password']}")

            # 等待表单元素加载
            print("[INFO] 等待表单元素加载...")
            time.sleep(2)

            # 填写邮箱
            print("[INFO] 填写邮箱地址...")
            try:
                email_field = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#email")))
                self.driver.execute_script("arguments[0].scrollIntoView(true);", email_field)
                time.sleep(0.5)
                email_field.click()
                time.sleep(random.uniform(0.3, 0.7))
                self.human_like_type(email_field, test_data['email'])
                print(f"[SUCCESS] 邮箱填写完成: {test_data['email']}")
            except Exception as e:
                print(f"[ERROR] 填写邮箱失败: {e}")
                return False

            # 填写密码
            print("[INFO] 填写密码...")
            try:
                password_field = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#password")))
                self.driver.execute_script("arguments[0].scrollIntoView(true);", password_field)
                time.sleep(0.5)
                password_field.click()
                time.sleep(random.uniform(0.3, 0.7))
                self.human_like_type(password_field, test_data['password'])
                print("[SUCCESS] 密码填写完成")
            except Exception as e:
                print(f"[ERROR] 填写密码失败: {e}")
                return False

            # 填写用户名
            print("[INFO] 填写用户名...")
            try:
                username_field = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#login")))
                self.driver.execute_script("arguments[0].scrollIntoView(true);", username_field)
                time.sleep(0.5)
                username_field.click()
                time.sleep(random.uniform(0.3, 0.7))
                self.human_like_type(username_field, test_data['username'])
                print(f"[SUCCESS] 用户名填写完成: {test_data['username']}")
            except Exception as e:
                print(f"[ERROR] 填写用户名失败: {e}")
                return False

            # 表单填写完成后等待一下
            print("[INFO] 表单填写完成，等待3秒...")
            time.sleep(3)

            # 点击提交按钮
            print("[INFO] 点击提交按钮...")

            # 记录点击前的URL
            original_url = self.driver.current_url
            print(f"[INFO] 点击前URL: {original_url}")

            try:
                # 使用第一个选择器（已验证有效）
                submit_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="signup-form"]/form/div[2]/button')))
                self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                time.sleep(1)

                # 获取按钮信息
                button_text = submit_button.text
                print(f"[INFO] 找到按钮，文本: '{button_text}'")

                # 模拟人类点击前的短暂停顿
                time.sleep(random.uniform(0.5, 1.0))

                # 使用JavaScript点击（已验证成功的方法）
                print("[INFO] 使用JavaScript点击提交按钮...")
                self.driver.execute_script("arguments[0].click();", submit_button)

                # 等待页面响应
                time.sleep(3)

                print("[SUCCESS] 表单已提交！")


                print("[INFO] 自动化操作已完成，后续验证请人工处理")
                print("[INFO] 浏览器将保持打开状态，EdgeDriver进程继续运行")
                print("[INFO] 请手动完成验证码验证和邮箱验证等步骤")

            except Exception as e:
                print(f"[ERROR] 提交按钮点击失败: {e}")
                return False

            print("[SUCCESS] 注册表单人性化填写和提交完成")
            return True

        except Exception as e:
            print(f"[ERROR] 填写注册表单过程中发生错误: {e}")
            return False

    def handle_post_submission(self):
        """处理提交后的页面（兼容性方法）"""
        try:
            print("[INFO] 🔍 处理提交后的页面...")

            # 直接调用邮箱验证流程（采用test_的稳定逻辑）
            print("[INFO] 开始邮箱验证流程...")


            return self.handle_email_verification_flow()

        except Exception as e:
            print(f"[ERROR] 处理提交后页面失败: {e}")
            return False

            # 以下是原来的点击提交按钮代码（已注释）
            """
            try:
                submit_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#signup-form > form > div:nth-child(7) > button > span")))
                self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                time.sleep(1)

                # 模拟人类点击前的短暂停顿
                time.sleep(random.uniform(0.5, 1.0))

                # 尝试多种点击方式
                click_success = False

                # 方法1: 普通点击
                try:
                    submit_button.click()
                    print("[INFO] 尝试普通点击...")
                    time.sleep(2)
                    click_success = True
                except Exception as e1:
                    print(f"[WARNING] 普通点击失败: {e1}")

                # 方法2: 双击
                if not click_success:
                    try:
                        from selenium.webdriver.common.action_chains import ActionChains
                        actions = ActionChains(self.driver)
                        actions.double_click(submit_button).perform()
                        print("[INFO] 尝试双击...")
                        time.sleep(2)
                        click_success = True
                    except Exception as e2:
                        print(f"[WARNING] 双击失败: {e2}")

                # 方法3: 焦点+回车
                if not click_success:
                    try:
                        submit_button.click()  # 先获取焦点
                        from selenium.webdriver.common.keys import Keys
                        submit_button.send_keys(Keys.RETURN)
                        print("[INFO] 尝试焦点+回车...")
                        time.sleep(2)
                        click_success = True
                    except Exception as e3:
                        print(f"[WARNING] 焦点+回车失败: {e3}")

                # 方法4: JavaScript点击
                if not click_success:
                    try:
                        self.driver.execute_script("arguments[0].click();", submit_button)
                        print("[INFO] 尝试JavaScript点击...")
                        time.sleep(2)
                        click_success = True
                    except Exception as e4:
                        print(f"[WARNING] JavaScript点击失败: {e4}")

                if click_success:
                    print("[SUCCESS] 提交按钮点击完成")
                    # 等待页面响应更长时间
                    time.sleep(5)
                    return True
                else:
                    print("[ERROR] 所有点击方式都失败")
                    return False

            except Exception as e:
                print(f"[ERROR] 点击提交按钮失败: {e}")
                return False
            """

        except Exception as e:
            print(f"[ERROR] 填写注册表单过程中发生错误: {e}")
            return False

    def check_page_changes(self):
        """检查页面是否有内容变化（验证码、错误信息等）"""
        try:
            # 检查是否出现验证码
            captcha_selectors = [
                "iframe[src*='captcha']",
                ".captcha",
                "#captcha",
                "[data-captcha]",
                ".h-captcha",
                ".g-recaptcha"
            ]

            for selector in captcha_selectors:
                try:
                    captcha_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if captcha_element.is_displayed():
                        print(f"[INFO] 检测到验证码元素: {selector}")
                        return True
                except:
                    continue

            # 检查是否有错误消息
            error_selectors = [
                ".flash-error",
                ".error",
                "[data-testid='error']",
                ".alert-error",
                ".js-flash-alert"
            ]

            for selector in error_selectors:
                try:
                    error_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for error_element in error_elements:
                        if error_element.is_displayed() and error_element.text:
                            print(f"[INFO] 检测到错误消息: {error_element.text}")
                            return True
                except:
                    continue

            # 检查页面是否有新的内容加载
            try:
                # 查找可能的加载指示器或新内容
                loading_selectors = [
                    ".loading",
                    ".spinner",
                    "[data-loading]",
                    ".progress"
                ]

                for selector in loading_selectors:
                    try:
                        loading_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if loading_element.is_displayed():
                            print(f"[INFO] 检测到加载元素: {selector}")
                            return True
                    except:
                        continue

            except:
                pass

            return False

        except Exception as e:
            print(f"[WARNING] 检查页面变化时出错: {e}")
            return False

    def analyze_page_state(self, url, title):
        """分析当前页面状态"""
        try:
            # 邮箱验证页面
            if "account_verifications" in url and "verify your email" in title.lower():
                return "EMAIL_VERIFICATION"

            # 检查是否有验证码输入框
            try:
                code_input = self.driver.find_element(By.CSS_SELECTOR, "#launch-code-0")
                if code_input.is_displayed():
                    return "EMAIL_VERIFICATION"
            except:
                pass

            # CAPTCHA验证页面
            if "signup" in url and ("sign up" in title.lower() or "github" in title.lower()):
                # 检查是否有CAPTCHA元素
                try:
                    captcha_elements = [
                        "iframe[src*='captcha']",
                        ".captcha",
                        "#captcha",
                        "[data-captcha]",
                        ".h-captcha",
                        ".g-recaptcha",
                        ".cf-turnstile"
                    ]

                    for selector in captcha_elements:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if element.is_displayed():
                            return "CAPTCHA_PAGE"
                except:
                    pass

                return "SIGNUP_PAGE"

            # 错误页面
            if "error" in title.lower() or "404" in title or "500" in title:
                return "ERROR_PAGE"

            # GitHub主页或其他页面
            if "github.com" in url:
                if url == "https://github.com/" or "/dashboard" in url:
                    return "SUCCESS_PAGE"
                else:
                    return "UNKNOWN_GITHUB_PAGE"

            # 其他页面
            return "UNKNOWN_PAGE"

        except Exception as e:
            return f"ANALYSIS_ERROR: {e}"

    def wait_for_email_verification_page(self):
        """智能等待邮箱验证页面出现（无超时限制）"""
        print("[WAIT] 智能检测页面状态，等待邮箱验证页面出现...")
        print("[INFO] 将持续监控页面变化，直到检测到邮箱验证页面")

        start_time = time.time()
        check_interval = 3  # 每3秒检查一次
        last_page_state = None
        captcha_detected = False

        while True:
            try:
                current_url = self.driver.current_url
                page_title = self.driver.title
                elapsed = int(time.time() - start_time)

                # 分析当前页面状态
                page_state = self.analyze_page_state(current_url, page_title)

                # 检测到CAPTCHA页面时的特殊处理
                if page_state == "CAPTCHA_PAGE" and not captcha_detected:
                    captcha_detected = True
                    print(f"\n[CAPTCHA] 检测到CAPTCHA验证页面!")
                    print(f"[IMPORTANT] 为避免触发反自动化检测，脚本将进入静默模式")
                    print(f"[INFO] 请手动完成CAPTCHA验证，完成后页面会自动跳转")
                    print(f"[INFO] 脚本将每30秒进行一次轻量检测...")

                    # 进入CAPTCHA静默等待模式
                    return self.wait_captcha_completion()

                # 只在页面状态改变时显示详细信息
                if page_state != last_page_state:
                    print(f"\n[DETECT] {elapsed}s - 页面状态变化:")
                    print(f"[INFO] 当前状态: {page_state}")
                    print(f"[INFO] 页面标题: {page_title}")
                    print(f"[INFO] URL: {current_url[:80]}...")
                    last_page_state = page_state
                else:
                    # 相同状态只显示简单进度
                    print(f"[WAIT] {elapsed}s - {page_state}", end='\r')

                # 检查是否到达邮箱验证页面
                if page_state == "EMAIL_VERIFICATION":
                    print(f"\n[SUCCESS] 检测到邮箱验证页面!")
                    return True

                # 检查是否遇到错误页面
                elif page_state == "ERROR_PAGE":
                    print(f"\n[ERROR] 检测到错误页面，停止等待")
                    return False

                # 如果在注册页面停留太久，给出提示
                elif page_state == "SIGNUP_PAGE":
                    if elapsed > 180:  # 3分钟后提示
                        if elapsed % 60 == 0:  # 每分钟提示一次
                            print(f"\n[INFO] 仍在注册页面，请检查是否需要完成额外步骤...")

            except Exception as e:
                print(f"\n[WARNING] 检查页面时出错: {e}")

            time.sleep(check_interval)

    def wait_captcha_completion(self):
        """CAPTCHA静默等待模式 - 最小化自动化操作"""
        print("[SILENT] 进入CAPTCHA静默等待模式...")

        start_time = time.time()
        check_interval = 30  # 延长到30秒检查一次，减少自动化痕迹

        while True:
            try:
                elapsed = int(time.time() - start_time)

                # 最小化的页面检测 - 只获取基本信息
                try:
                    current_url = self.driver.current_url

                    # 检查是否已经离开CAPTCHA页面
                    if "account_verifications" in current_url:
                        print(f"\n[SUCCESS] CAPTCHA验证完成，已跳转到邮箱验证页面!")
                        return True

                    # 检查是否回到注册页面（可能是验证失败）
                    elif "signup" in current_url:
                        # 进一步检查是否有错误信息
                        try:
                            # 检查是否有CAPTCHA错误提示
                            error_text = self.driver.find_element(By.TAG_NAME, "body").text
                            if "unable to verify" in error_text.lower() or "captcha" in error_text.lower():
                                print(f"\n[ERROR] CAPTCHA验证失败，检测到错误信息")
                                print(f"[INFO] 请重新完成CAPTCHA验证")
                                # 继续等待，不返回False
                            else:
                                print(f"\n[INFO] 仍在注册页面，继续等待CAPTCHA完成...")
                        except:
                            print(f"\n[INFO] 仍在注册页面，继续等待CAPTCHA完成...")

                    # 检查是否到了其他页面
                    else:
                        page_title = self.driver.title
                        if "verify your email" in page_title.lower():
                            print(f"\n[SUCCESS] CAPTCHA验证完成，已到达邮箱验证页面!")
                            return True
                        elif "error" in page_title.lower():
                            print(f"\n[ERROR] 检测到错误页面: {page_title}")
                            return False
                        else:
                            print(f"\n[INFO] 页面跳转到: {page_title}")

                except Exception as e:
                    print(f"\n[WARNING] 轻量检测失败: {e}")

                # 显示等待进度
                minutes = elapsed // 60
                seconds = elapsed % 60
                print(f"[SILENT] 静默等待中... {minutes:02d}:{seconds:02d} (每30秒检测一次)")

                time.sleep(check_interval)

            except Exception as e:
                print(f"\n[ERROR] 静默等待过程中出错: {e}")
                time.sleep(check_interval)

    def get_email_verification_code(self):
        """自动获取邮箱验证码"""
        try:
            # 导入邮箱服务
            import sys
            import os
            sys.path.append(str(Path(__file__).parent))
            from email_service import EmailService

            # 创建GitHub邮箱服务
            email_service = EmailService(
                sender_filter="noreply@github.com",
                subject_filter="GitHub launch code",
                code_pattern=r'\b\d{8}\b',  # GitHub使用8位验证码
                check_interval=20,  # 每20秒检查一次
                max_wait_time=180,  # 最多等待3分钟
                delete_after_read=False  # 不删除邮件
            )

            print("[EMAIL] 连接邮箱服务获取验证码...")
            verification_code = email_service.get_verification_code()

            if verification_code:
                print(f"[SUCCESS] 自动获取到验证码: {verification_code}")
                return verification_code
            else:
                print("[WARNING] 自动获取验证码失败")
                return None

        except Exception as e:
            print(f"[ERROR] 邮箱服务异常: {e}")
            return None

    def fill_email_verification_code(self, verification_code):
        """填写邮箱验证码"""
        try:
            print(f"[INFO] 开始填写邮箱验证码: {verification_code}")

            # 验证码必须是8位数字
            if len(verification_code) != 8 or not verification_code.isdigit():
                print(f"[ERROR] 验证码格式错误，必须是8位数字，当前: {verification_code}")
                return False

            # 逐个填写8个输入框
            for i, digit in enumerate(verification_code):
                try:
                    input_selector = f"#launch-code-{i}"
                    print(f"[INFO] 填写第{i+1}个输入框: {digit}")

                    # 等待输入框可点击
                    input_field = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, input_selector)))

                    # 清空并输入数字
                    input_field.clear()
                    time.sleep(0.1)
                    input_field.send_keys(digit)

                    # 短暂延迟模拟人类输入
                    time.sleep(random.uniform(0.2, 0.5))

                except Exception as e:
                    print(f"[ERROR] 填写第{i+1}个输入框失败: {e}")
                    return False

            print("[SUCCESS] 邮箱验证码填写完成")

            # 等待一下让页面处理
            time.sleep(2)

            # 点击提交按钮
            return self.submit_email_verification()

        except Exception as e:
            print(f"[ERROR] 填写邮箱验证码过程中发生错误: {e}")
            return False

    def submit_email_verification(self):
        """提交邮箱验证码"""
        try:
            # 首先检查页面是否还在邮箱验证页面
            print("[INFO] 检查页面状态...")
            time.sleep(2)  # 等待2秒让页面有时间自动跳转

            current_url = self.driver.current_url
            page_title = self.driver.title

            print(f"[INFO] 当前URL: {current_url[:60]}...")
            print(f"[INFO] 当前标题: {page_title}")

            # 检查是否还在邮箱验证页面
            if "account_verifications" not in current_url and "verify" not in current_url.lower():
                print("[INFO] 页面已自动跳转，无需点击提交按钮")
                print("[SUCCESS] 邮箱验证码自动提交完成")
                return True

            # 检查页面是否包含验证码输入框，如果没有说明已经跳转了
            try:
                verification_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'][maxlength='1']")
                if not verification_inputs:
                    print("[INFO] 未找到验证码输入框，页面可能已跳转")
                    print("[SUCCESS] 邮箱验证码自动提交完成")
                    return True
            except:
                pass

            print("[INFO] 页面仍在邮箱验证状态，查找并点击Continue按钮...")

            # 尝试多个可能的按钮选择器
            button_selectors = [
                "button:contains('Continue')",
                "button[type='submit']",
                "form button",
                ".Primer_Brand__Button-module__Button___lDruK"
            ]

            submit_button = None

            # 尝试找到Continue按钮
            for selector in button_selectors:
                try:
                    if selector == "button:contains('Continue')":
                        # 使用XPath查找包含Continue文本的按钮
                        buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Continue')]")
                        if buttons:
                            submit_button = buttons[0]
                            print(f"[SUCCESS] 找到Continue按钮 (XPath)")
                            break
                    else:
                        submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if submit_button.is_displayed():
                            print(f"[SUCCESS] 找到提交按钮: {selector}")
                            break
                except:
                    continue

            if not submit_button:
                print("[WARNING] 未找到提交按钮，可能页面已自动跳转")
                print("[SUCCESS] 邮箱验证码自动提交完成")
                return True

            # 获取按钮信息
            button_text = submit_button.text
            print(f"[INFO] 按钮文本: '{button_text}'")

            # 滚动到按钮位置
            self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
            time.sleep(1)

            # 使用JavaScript点击
            print("[INFO] 使用JavaScript点击Continue按钮...")
            self.driver.execute_script("arguments[0].click();", submit_button)

            # 等待页面响应
            time.sleep(3)

            print("[SUCCESS] 邮箱验证码已提交!")
            return True

        except Exception as e:
            print(f"[ERROR] 提交邮箱验证码失败: {e}")
            return False

    def get_last_test_data(self):
        """获取最后一次生成的测试数据"""
        # 这里返回当前实例的测试数据
        # 在实际使用中，我们需要保存注册时的数据
        if hasattr(self, 'current_test_data'):
            return self.current_test_data
        else:
            print("[WARNING] 未找到测试数据，将重新生成")
            return self.generate_test_data()

    def save_account_info(self):
        """保存账号信息到文件（邮箱验证成功后立即保存）"""
        try:
            # 获取测试数据
            test_data = self.get_last_test_data()
            if not test_data:
                print("[ERROR] 无法获取账号信息")
                return False

            # 获取当前日期和时间
            from datetime import datetime
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 准备账号信息
            email = test_data['email']
            password = test_data['password']
            platform = "github"
            register_datetime = current_datetime

            account_line = f"{email}\t\t{password}\t{platform}\t{register_datetime}\n"

            # 保存到文件
            account_file = Path(__file__).parent / "账号.txt"

            with open(account_file, 'a', encoding='utf-8') as f:
                f.write(account_line)

            print(f"[SUCCESS] 账号信息已保存到: {account_file}")
            print(f"[INFO] 邮箱: {email}")
            print(f"[INFO] 平台: {platform}")
            print(f"[INFO] 注册时间: {register_datetime}")
            print(f"[INFO] 保存时机: 邮箱验证成功后")

            return True

        except Exception as e:
            print(f"[ERROR] 保存账号信息失败: {e}")
            return False

    def handle_email_verification_flow(self):
        """处理邮箱验证流程"""
        try:
            print("\n" + "="*60)
            print("[EMAIL] 开始邮箱验证流程")
            print("="*60)

            # 1. 先等待30秒让用户完成验证码验证
            print("[WAIT] 等待30秒让用户完成CAPTCHA验证...")
            print("[INFO] 请在这30秒内完成页面上的验证码验证")

            for i in range(30):
                remaining = 30 - i
                print(f"[WAIT] 剩余等待时间: {remaining}秒", end='\r')
                time.sleep(1)

            print("\n[INFO] 等待完成，开始检测邮箱验证页面...")

            # 2. 等待邮箱验证页面出现
            if not self.wait_for_email_verification_page():
                print("[ERROR] 未检测到邮箱验证页面")
                return False

            # 3. 自动获取邮箱验证码
            print("\n[AUTO] 开始自动获取邮箱验证码...")
            verification_code = self.get_email_verification_code()

            if not verification_code:
                # 如果自动获取失败，回退到手动输入
                print("\n[FALLBACK] 自动获取失败，请手动输入验证码")
                print("[INPUT] 请查看邮箱并输入收到的8位验证码")
                print("[INFO] 验证码格式: 12345678 (8位数字)")

                while True:
                    verification_code = input("请输入邮箱验证码: ").strip()

                    if len(verification_code) == 8 and verification_code.isdigit():
                        break
                    else:
                        print("[ERROR] 验证码格式错误，请输入8位数字")

            # 4. 填写并提交验证码
            if self.fill_email_verification_code(verification_code):
                print("[SUCCESS] 邮箱验证完成!")

                # 邮箱验证成功后立即保存账号信息
                print("\n[SAVE] 邮箱验证成功，立即保存账号信息...")
                self.save_account_info()

                # 等待页面跳转完成（可能经过中间页面）
                print("\n[WAIT] 邮箱验证成功，等待页面跳转...")
                print("[INFO] 页面可能会先跳转到中间页面，然后再跳转到登录页面")

                # 监控页面跳转状态
                for i in range(15):
                    time.sleep(1)
                    try:
                        current_url = self.driver.current_url
                        page_title = self.driver.title
                        print(f"[WAIT] {i+1}s - URL: {current_url[:50]}... 标题: {page_title[:30]}...")

                        # 如果已经跳转到登录页面，可以提前结束等待
                        if "/login" in current_url and "Sign in to GitHub" in page_title:
                            print(f"[SUCCESS] 在第{i+1}秒检测到已跳转到登录页面，提前结束等待")
                            break
                    except:
                        pass

                # 5. 检测并处理登录页面
                login_result = self.handle_github_login()
                if login_result == "OAUTH_COMPLETED":
                    print("[SUCCESS] GitHub登录和OAuth授权完成!")

                    # 拷贝AWS SSO缓存文件到sandbox_files/OAuth目录
                    print("[INFO] 开始处理AWS SSO缓存文件...")
                    self.copy_aws_sso_cache_files()

                    print("[SUCCESS] 完整流程已完成，程序将正常退出")
                    return "OAUTH_COMPLETED"
                elif login_result:
                    print("[SUCCESS] GitHub登录完成!")
                    return True
                else:
                    print("[ERROR] GitHub登录失败")
                    return False
            else:
                print("[ERROR] 邮箱验证失败")
                return False

        except Exception as e:
            print(f"[ERROR] 邮箱验证流程出错: {e}")
            return False

    def handle_github_login(self):
        """处理GitHub登录页面"""
        try:
            print("\n" + "="*60)
            print("[LOGIN] 开始GitHub登录流程")
            print("="*60)


            # 由于邮箱验证后已经等待了15秒，这里只需要等待3秒
            print("[WAIT] 等待页面稳定...")
            time.sleep(3)

            # 等待页面跳转到登录页面，最多等待30秒（减少等待时间）
            print("[WAIT] 智能等待GitHub登录页面...")
            max_wait_time = 30
            check_interval = 2

            # 先立即检测一次，可能页面已经准备好了
            print("[INFO] 立即检测当前页面状态...")
            if self.detect_github_login_page():
                print("[SUCCESS] 页面已经是登录页面，无需等待")
            else:
                # 如果不是登录页面，则开始等待
                login_page_found = False
                for elapsed in range(0, max_wait_time, check_interval):
                    time.sleep(check_interval)

                    # 检测登录页面特征
                    if self.detect_github_login_page():
                        print(f"[SUCCESS] 在 {elapsed + check_interval} 秒后检测到GitHub登录页面")
                        login_page_found = True
                        break
                    else:
                        # 检查当前页面状态，提供更详细的信息
                        try:
                            current_url = self.driver.current_url
                            if "account_verifications" in current_url:
                                print(f"[WAIT] 仍在邮箱验证页面... ({elapsed + check_interval}s)")
                            elif "/login" in current_url:
                                print(f"[WAIT] 在登录相关页面，但未完全加载... ({elapsed + check_interval}s)")
                            else:
                                print(f"[WAIT] 等待页面跳转... ({elapsed + check_interval}s)")
                        except:
                            print(f"[WAIT] 等待中... ({elapsed + check_interval}s)")

                if not login_page_found:
                    print("[ERROR] 超时未检测到GitHub登录页面")
                    print("[INFO] 最后检测的页面信息:")
                    try:
                        current_url = self.driver.current_url
                        page_title = self.driver.title
                        print(f"[INFO] 最终URL: {current_url}")
                        print(f"[INFO] 最终标题: {page_title}")

                        # 如果页面仍在account_verifications，尝试手动跳转
                        if "account_verifications" in current_url:
                            print("[INFO] 页面仍在邮箱验证页面，可能需要手动操作")
                            print("[INFO] 尝试查找跳转链接或按钮...")
                            return self.handle_account_verification_redirect()
                    except:
                        pass
                    return False

            # 页面稳定性确认（减少等待时间）
            print("[WAIT] 等待页面完全稳定...")
            time.sleep(2)

            # 二次确认页面仍然是登录页面
            if not self.detect_github_login_page():
                print("[ERROR] 页面稳定性确认失败")
                return False

            print("[SUCCESS] 页面稳定性确认通过")

            # 填写登录表单前再等待3秒
            print("[WAIT] 表单填写前最后等待...")
            time.sleep(3)

            # 填写登录表单
            print("[LOGIN] 开始填写登录表单...")
            if not self.fill_github_login_form():
                print("[ERROR] 填写登录表单失败")
                return False

            # 提交登录前再等待3秒
            print("[WAIT] 登录提交前最后等待...")
            time.sleep(3)

            # 提交登录
            print("[LOGIN] 开始提交登录...")
            if not self.submit_github_login():
                print("[ERROR] 提交登录失败")
                return False

            print("[SUCCESS] GitHub登录流程完成")

            # 检查是否需要处理OAuth授权页面
            if self.handle_oauth_authorization():
                print("[SUCCESS] OAuth授权完成")

                # 拷贝AWS SSO缓存文件到sandbox_files/OAuth目录
                print("[INFO] 开始处理AWS SSO缓存文件...")
                self.copy_aws_sso_cache_files()

                # OAuth完成后，程序可以正常结束，不需要保持运行
                return "OAUTH_COMPLETED"
            else:
                print("[WARNING] OAuth授权可能需要手动处理")

            return True

        except Exception as e:
            print(f"[ERROR] GitHub登录流程出错: {e}")
            return False

    def handle_oauth_authorization(self):
        """处理OAuth授权页面"""
        try:
            print("\n" + "="*60)
            print("[OAUTH] 开始OAuth授权流程")
            print("="*60)


            # 等待页面跳转到授权页面，最多等待15秒
            print("[WAIT] 等待OAuth授权页面...")
            max_wait_time = 15
            check_interval = 2

            for elapsed in range(0, max_wait_time, check_interval):
                time.sleep(check_interval)

                # 检测OAuth授权页面
                if self.detect_oauth_authorization_page():
                    print(f"[SUCCESS] 在 {elapsed + check_interval} 秒后检测到OAuth授权页面")

                    # 等待页面完全加载
                    print("[WAIT] 等待授权页面完全加载...")
                    time.sleep(2)

                    # 点击授权按钮
                    if self.click_oauth_authorize_button():
                        print("[SUCCESS] OAuth授权按钮点击成功")

                        # 等待并检测OAuth回调页面
                        if self.wait_for_oauth_callback():
                            print("[SUCCESS] OAuth授权流程完全完成")
                            return True
                        else:
                            print("[WARNING] OAuth回调页面检测超时，但授权可能已完成")
                            return True
                    else:
                        print("[ERROR] OAuth授权按钮点击失败")
                        return False
                else:
                    print(f"[WAIT] 等待OAuth授权页面... ({elapsed + check_interval}s)")

            print("[WARNING] 未检测到OAuth授权页面，可能已经完成或不需要授权")
            return True

        except Exception as e:
            print(f"[ERROR] OAuth授权流程出错: {e}")
            return False

    def detect_oauth_authorization_page(self):
        """检测OAuth授权页面"""
        try:
            current_url = self.driver.current_url
            page_title = self.driver.title

            print(f"[INFO] 当前URL: {current_url[:80]}...")
            print(f"[INFO] 页面标题: {page_title}")

            # 检查URL是否包含oauth/authorize
            url_contains_oauth = "/oauth/authorize" in current_url

            # 检查页面标题是否为 "Authorize application"
            title_matches = "Authorize application" in page_title

            if url_contains_oauth and title_matches:
                print("[SUCCESS] 检测到OAuth授权页面 (URL + 标题匹配)")

                # 检查授权按钮是否存在
                try:
                    authorize_button = self.driver.find_element(By.CSS_SELECTOR, ".js-oauth-authorize-btn")
                    if authorize_button.is_displayed():
                        print("[SUCCESS] 检测到授权按钮")
                        return True
                    else:
                        print("[ERROR] 授权按钮不可见")
                        return False
                except Exception as e:
                    print(f"[ERROR] 未找到授权按钮: {e}")
                    return False
            else:
                if not url_contains_oauth:
                    print(f"[INFO] URL不包含oauth/authorize")
                if not title_matches:
                    print(f"[INFO] 页面标题不是授权页面")
                return False

        except Exception as e:
            print(f"[ERROR] 检测OAuth授权页面时出错: {e}")
            return False

    def click_oauth_authorize_button(self):
        """点击OAuth授权按钮"""
        try:
            print("[OAUTH] 查找并点击授权按钮...")

            # 使用您提供的选择器
            button_selectors = [
                # 优先使用类名选择器
                ".js-oauth-authorize-btn",
                # 备用选择器
                "button[name='authorize'][value='1']",
                "button[type='submit'].btn-primary",
                # 最后使用完整的CSS路径
                "body > div.logged-in.env-production.page-responsive.color-bg-subtle > div.application-main > main > div > div.px-3.mt-5 > div.Box.color-shadow-small > div.Box-footer.p-3.p-md-4.clearfix > div:nth-child(1) > form > div > button.js-oauth-authorize-btn.btn.btn-primary.width-full.ws-normal"
            ]

            authorize_button = None

            for i, selector in enumerate(button_selectors, 1):
                try:
                    print(f"[INFO] 尝试选择器 {i}: {selector[:50]}...")
                    authorize_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if authorize_button.is_displayed():
                        print(f"[SUCCESS] 找到授权按钮 (选择器 {i})")
                        break
                except Exception as e:
                    print(f"[WARNING] 选择器 {i} 失败: {e}")
                    continue

            if not authorize_button:
                print("[ERROR] 未找到授权按钮")
                return False

            # 获取按钮信息
            button_text = authorize_button.text
            button_class = authorize_button.get_attribute("class")
            print(f"[INFO] 按钮文本: '{button_text}'")
            print(f"[INFO] 按钮类名: '{button_class}'")

            # 滚动到按钮位置
            self.driver.execute_script("arguments[0].scrollIntoView(true);", authorize_button)
            time.sleep(1)

            # 使用JavaScript点击（确保生效）
            print("[OAUTH] 使用JavaScript点击授权按钮...")
            self.driver.execute_script("arguments[0].click();", authorize_button)

            print("[SUCCESS] OAuth授权按钮已点击")


            return True

        except Exception as e:
            print(f"[ERROR] 点击OAuth授权按钮时出错: {e}")
            return False

    def wait_for_oauth_callback(self):
        """等待OAuth回调页面"""
        try:
            print("[WAIT] 等待OAuth回调页面...")
            max_wait_time = 20
            check_interval = 2

            for elapsed in range(0, max_wait_time, check_interval):
                time.sleep(check_interval)

                # 检测OAuth回调页面
                if self.detect_oauth_callback_page():
                    print(f"[SUCCESS] 在 {elapsed + check_interval} 秒后检测到OAuth回调页面")

                    # 等待2秒确保页面完全加载
                    time.sleep(2)

                    # 获取并显示回调URL
                    callback_url = self.driver.current_url
                    print(f"[SUCCESS] OAuth回调URL: {callback_url}")

                    # 检查URL中的参数
                    if "code=" in callback_url and "state=" in callback_url:
                        print("[SUCCESS] OAuth授权码获取成功")
                        print("[INFO] Kiro应用授权完成")

                        # 显示完成信息
                        print("\n" + "="*60)
                        print("[COMPLETE] 🎉 GitHub账号注册和Kiro授权全部完成！")
                        print("="*60)
                        print(f"[INFO] 注册邮箱: {self.get_last_test_data()['email']}")
                        print(f"[INFO] OAuth回调: {callback_url[:80]}...")
                        print("[INFO] 账号信息已在邮箱验证时保存")
                        print("[INFO] 可以关闭浏览器窗口了")

                        # 安全关闭EdgeDriver
                        self.safe_close_driver()
                        return True
                    else:
                        print("[WARNING] OAuth回调URL格式异常")
                        return False
                else:
                    print(f"[WAIT] 等待OAuth回调... ({elapsed + check_interval}s)")

            print("[WARNING] OAuth回调页面检测超时")
            return False

        except Exception as e:
            print(f"[ERROR] 等待OAuth回调时出错: {e}")
            return False

    def detect_oauth_callback_page(self):
        """检测OAuth回调页面"""
        try:
            current_url = self.driver.current_url
            page_title = self.driver.title

            # 检查URL是否为localhost回调
            url_is_callback = (
                "localhost" in current_url and
                "/oauth/callback" in current_url and
                "code=" in current_url
            )

            # 检查页面内容是否包含关闭提示
            try:
                page_body = self.driver.find_element(By.TAG_NAME, "body").text
                body_contains_close = "You can close this window" in page_body
            except:
                body_contains_close = False

            if url_is_callback and body_contains_close:
                print("[SUCCESS] 检测到OAuth回调页面")
                print(f"[INFO] 回调URL: {current_url}")
                print(f"[INFO] 页面内容: {page_body}")
                return True
            else:
                return False

        except Exception as e:
            print(f"[ERROR] 检测OAuth回调页面时出错: {e}")
            return False

    def safe_close_driver(self):
        """安全关闭EdgeDriver"""
        try:
            print("[INFO] 准备安全关闭EdgeDriver...")

            # 等待3秒让用户看到完成信息
            print("[WAIT] 3秒后自动关闭浏览器...")
            for i in range(3, 0, -1):
                print(f"[WAIT] {i}秒后关闭...", end='\r')
                time.sleep(1)

            print("\n[INFO] 正在关闭EdgeDriver...")

            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
                print("[SUCCESS] EdgeDriver已安全关闭")
            else:
                print("[INFO] EdgeDriver已经关闭")

        except Exception as e:
            print(f"[WARNING] 关闭EdgeDriver时出现异常: {e}")
            print("[INFO] 浏览器可能需要手动关闭")

    def detect_github_login_page(self):
        """检测GitHub登录页面"""
        try:
            current_url = self.driver.current_url
            page_title = self.driver.title

            print(f"[INFO] 当前URL: {current_url[:80]}...")
            print(f"[INFO] 页面标题: {page_title}")

            # 检查URL是否包含login路径 - 更宽松的匹配
            url_contains_login = "/login" in current_url and "client_id=" in current_url

            # 检查页面标题 - 更宽松的匹配，包含多种可能的标题格式
            title_matches = ("Sign in to GitHub" in page_title or
                           "GitHub" in page_title and "login" in page_title.lower())

            # 额外检查：是否有成功注册的提示信息
            has_success_message = False
            try:
                success_elements = self.driver.find_elements(By.CSS_SELECTOR, ".flash-success, .flash.flash-success")
                for element in success_elements:
                    if "account was created successfully" in element.text.lower():
                        has_success_message = True
                        print("[INFO] 检测到账号创建成功提示")
                        break
            except:
                pass

            print(f"[DEBUG] URL匹配: {url_contains_login}")
            print(f"[DEBUG] 标题匹配: {title_matches}")
            print(f"[DEBUG] 成功消息: {has_success_message}")

            if url_contains_login and title_matches:
                print("[SUCCESS] 检测到GitHub登录页面 (URL + 标题匹配)")

                # 检查登录表单元素是否存在
                try:
                    login_field = self.driver.find_element(By.CSS_SELECTOR, "#login_field")
                    password_field = self.driver.find_element(By.CSS_SELECTOR, "#password")

                    if login_field.is_displayed() and password_field.is_displayed():
                        print("[SUCCESS] 检测到登录表单")
                        if has_success_message:
                            print("[SUCCESS] 确认这是注册成功后的登录页面")
                        return True
                    else:
                        print("[ERROR] 登录表单不可见")
                        return False
                except Exception as e:
                    print(f"[ERROR] 未找到登录表单: {e}")
                    return False
            else:
                if not url_contains_login:
                    print(f"[WARNING] URL不匹配登录页面，当前URL: {current_url[:100]}...")
                    print("[INFO] 期望URL包含: '/login' 和 'client_id='")
                if not title_matches:
                    print(f"[WARNING] 页面标题不匹配，当前标题: {page_title}")
                    print("[INFO] 期望标题包含: 'Sign in to GitHub'")
                return False

        except Exception as e:
            print(f"[ERROR] 检测登录页面时出错: {e}")
            return False

    def handle_account_verification_redirect(self):
        """处理account_verifications页面的跳转"""
        try:
            print("[INFO] 尝试处理邮箱验证页面跳转...")

            # 查找可能的跳转链接或按钮
            redirect_selectors = [
                "a[href*='/login']",  # 登录链接
                "button:contains('Continue')",  # Continue按钮
                "a:contains('Continue')",  # Continue链接
                "a:contains('Sign in')",  # Sign in链接
                ".btn-primary",  # 主要按钮
                "form button[type='submit']"  # 表单提交按钮
            ]

            for selector in redirect_selectors:
                try:
                    if "contains" in selector:
                        # 使用XPath处理包含文本的选择器
                        if "button" in selector:
                            elements = self.driver.find_elements(By.XPATH, f"//button[contains(text(), '{selector.split(':contains(')[1][2:-2]}')]")
                        else:
                            elements = self.driver.find_elements(By.XPATH, f"//a[contains(text(), '{selector.split(':contains(')[1][2:-2]}')]")
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    if elements:
                        element = elements[0]
                        if element.is_displayed():
                            print(f"[SUCCESS] 找到跳转元素: {selector}")
                            print(f"[INFO] 元素文本: '{element.text}'")

                            # 滚动到元素位置
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                            time.sleep(1)

                            # 点击元素
                            element.click()
                            print("[SUCCESS] 已点击跳转元素")

                            # 等待页面跳转
                            time.sleep(3)
                            return True
                except Exception as e:
                    print(f"[DEBUG] 选择器 {selector} 失败: {e}")
                    continue

            print("[WARNING] 未找到合适的跳转元素")
            return False

        except Exception as e:
            print(f"[ERROR] 处理邮箱验证页面跳转时出错: {e}")
            return False

    def fill_github_login_form(self):
        """填写GitHub登录表单"""
        try:
            print("[LOGIN] 开始填写登录表单...")

            # 获取注册时使用的邮箱和密码
            test_data = self.get_last_test_data()
            if not test_data:
                print("[ERROR] 无法获取注册数据")
                return False

            email = test_data['email']
            password = test_data['password']

            print(f"[INFO] 使用邮箱: {email}")
            print(f"[INFO] 使用密码: {password[:3]}***{password[-3:]}")

            # 填写邮箱
            print("[LOGIN] 定位邮箱输入框...")
            try:
                login_field = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#login_field")))
                print("[SUCCESS] 找到邮箱输入框")

                # 滚动到输入框位置
                self.driver.execute_script("arguments[0].scrollIntoView(true);", login_field)
                time.sleep(0.5)

                # 点击并清空
                login_field.click()
                login_field.clear()
                time.sleep(0.5)

                # 人性化输入
                print("[LOGIN] 开始输入邮箱...")
                self.human_like_type(login_field, email)
                print("[SUCCESS] 邮箱填写完成")
            except Exception as e:
                print(f"[ERROR] 填写邮箱失败: {e}")
                return False

            # 填写密码
            print("[LOGIN] 定位密码输入框...")
            try:
                password_field = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#password")))
                print("[SUCCESS] 找到密码输入框")

                # 滚动到输入框位置
                self.driver.execute_script("arguments[0].scrollIntoView(true);", password_field)
                time.sleep(0.5)

                # 点击并清空
                password_field.click()
                password_field.clear()
                time.sleep(0.5)

                # 人性化输入
                print("[LOGIN] 开始输入密码...")
                self.human_like_type(password_field, password)
                print("[SUCCESS] 密码填写完成")
            except Exception as e:
                print(f"[ERROR] 填写密码失败: {e}")
                return False

            # 等待更长时间让表单稳定
            print("[LOGIN] 表单填写完成，等待5秒让表单稳定...")
            time.sleep(5)

            print("[SUCCESS] 登录表单填写完成")
            return True

        except Exception as e:
            print(f"[ERROR] 填写登录表单时出错: {e}")
            return False

    def submit_github_login(self):
        """提交GitHub登录"""
        try:
            print("[LOGIN] 查找并点击登录按钮...")

            # 使用您提供的精确选择器
            button_selectors = [
                # 优先使用简单的CSS选择器
                "input[type='submit'][value='Sign in']",
                # 备用选择器
                "input[type='submit'][name='commit']",
                ".js-sign-in-button",
                # 最后使用完整的CSS路径
                "body > div.logged-out.env-production.page-responsive.session-authentication > div.application-main > main > div > div.authentication-body.authentication-body--with-form.new-session > form > div:nth-child(4) > input"
            ]

            login_button = None

            for i, selector in enumerate(button_selectors, 1):
                try:
                    print(f"[INFO] 尝试选择器 {i}: {selector[:50]}...")
                    login_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if login_button.is_displayed():
                        print(f"[SUCCESS] 找到登录按钮 (选择器 {i})")
                        break
                except Exception as e:
                    print(f"[WARNING] 选择器 {i} 失败: {e}")
                    continue

            if not login_button:
                print("[ERROR] 未找到登录按钮")
                return False

            # 获取按钮信息
            button_value = login_button.get_attribute("value") or login_button.text
            button_class = login_button.get_attribute("class")
            print(f"[INFO] 按钮文本: '{button_value}'")
            print(f"[INFO] 按钮类名: '{button_class}'")

            # 滚动到按钮位置
            self.driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
            time.sleep(1)

            # 使用JavaScript点击（确保生效）
            print("[LOGIN] 使用JavaScript点击登录按钮...")
            self.driver.execute_script("arguments[0].click();", login_button)

            # 等待页面响应
            time.sleep(5)

            # 检查登录结果
            new_url = self.driver.current_url
            page_title = self.driver.title

            print(f"[INFO] 登录后URL: {new_url[:80]}...")
            print(f"[INFO] 登录后标题: {page_title}")

            # 判断登录是否成功
            if "login" not in new_url.lower() and "Sign in to GitHub" not in page_title:
                print("[SUCCESS] 登录成功，已离开登录页面")
                return True
            else:
                print("[WARNING] 仍在登录页面，可能需要额外验证")
                # 检查是否有错误信息
                try:
                    error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".flash-error, .js-flash-alert")
                    for error_element in error_elements:
                        if error_element.is_displayed():
                            error_text = error_element.text
                            print(f"[ERROR] 检测到登录错误: {error_text}")
                            return False
                except:
                    pass

                return True  # 如果没有错误信息，暂时返回True让流程继续

        except Exception as e:
            print(f"[ERROR] 提交登录时出错: {e}")
            return False

    def get_last_test_data(self):
        """获取最后一次生成的测试数据"""
        # 这里返回当前实例的测试数据
        # 在实际使用中，我们需要保存注册时的数据
        if hasattr(self, 'current_test_data'):
            return self.current_test_data
        else:
            print("[WARNING] 未找到测试数据，将重新生成")
            return self.generate_test_data()

    def run_automation(self):
        """运行自动化流程（独立模式，保持向后兼容）"""
        print("="*50)
        print("[INFO] GitHub 注册自动化开始")
        print("="*50)

        try:
            # 1. 加载硬件指纹
            self.load_hardware_fingerprints()

            # 2. 设置浏览器驱动
            if not self.setup_edge_driver():
                return False

            # 3. 等待用户手动导航到 GitHub 登录页面
            print("\n[INFO] 请手动操作以下步骤:")
            print("1. 运行 start_sandbox.ps1")
            print("2. 等待 Kiro IDE 安装完成")
            print("3. 在 Kiro 中点击注册按钮（如 GitHub）")
            print("4. 等待 Edge 浏览器打开 GitHub 登录页面")
            print("5. 然后按 Enter 键继续自动化...")

            input("\n按 Enter 键继续...")

            # 4. 等待 GitHub 登录页面
            if not self.wait_for_github_login_page():
                print("[ERROR] 未检测到 GitHub 登录页面")
                return False

            # 5. 获取当前页面信息
            self.get_current_page_info()

            # 6. 点击 "Create an account" 链接
            if not self.click_create_account_link():
                return False

            # 7. 等待注册页面加载
            if not self.wait_for_registration_page():
                return False

            # 8. 获取注册页面信息
            self.get_current_page_info()

            # 9. 填写注册表单
            print("\n[INFO] 开始自动填写注册表单...")
            if not self.fill_registration_form():
                print("[ERROR] 注册表单填写失败")
                return False

            # 10. 处理提交后的页面和邮箱验证流程
            if self.handle_post_submission():
                print(f"\n[SUCCESS] 完整注册流程完成!")
                print("[INFO] GitHub账户注册和验证已完成")
            else:
                print(f"\n[PARTIAL] 注册表单已提交，但后续验证未完成")
                print("[INFO] 请手动完成验证步骤")

            print("\n[SUCCESS] GitHub 注册自动化完成!")
            print("[INFO] 表单已自动填写并提交")

            print("[INFO] EdgeDriver进程将保持运行，浏览器窗口保持打开")
            print("[INFO] 完成后可手动关闭浏览器或按Ctrl+C退出程序")

            # 保持程序运行，不关闭EdgeDriver（采用test_文件的稳定机制）
            try:
                print("\n[WAIT] 程序等待中... (按Ctrl+C退出)")
                while True:
                    time.sleep(10)  # 每10秒检查一次，保持进程存活
            except KeyboardInterrupt:
                print("\n[INFO] 用户中断程序，准备退出...")
                return True

        except Exception as e:
            print(f"[ERROR] 自动化过程中发生错误: {e}")
            return False

        finally:
            # 采用test_文件的稳定机制：不主动关闭EdgeDriver
            # 让EdgeDriver保持运行状态，避免闪退
            # 只有在异常情况下才关闭driver（但这里我们选择不关闭以保持稳定性）
            pass

    def execute_workflow(self) -> bool:
        """执行完整的工作流程（新框架统一接口）"""
        print("[INFO] GitHub 注册自动化 - 新框架接口")
        return self.run_integrated_mode()

    def run_integrated_mode(self, existing_driver=None):
        """集成模式运行（被 kiro_login_automation.py 调用）"""
        print("[INFO] GitHub 注册自动化 - 集成模式")

        try:
            # 如果提供了现有的 driver，使用它
            if existing_driver:
                self.driver = existing_driver
                self.wait = WebDriverWait(self.driver, 30)
                print("[INFO] 使用现有的 EdgeDriver 实例")
            else:
                # 否则创建新的 driver
                self.load_hardware_fingerprints()
                if not self.setup_edge_driver():
                    return False

            # 执行核心自动化逻辑（无需用户交互）
            print("[INFO] 开始执行 GitHub 注册自动化...")

            # 等待 GitHub 登录页面
            if not self.wait_for_github_login_page():
                print("[ERROR] 未检测到 GitHub 登录页面")
                return False

            # 获取当前页面信息
            self.get_current_page_info()

            # 点击 "Create an account" 链接
            if not self.click_create_account_link():
                return False

            # 等待注册页面加载
            if not self.wait_for_registration_page():
                return False

            # 获取注册页面信息
            self.get_current_page_info()

            # 填写注册表单
            print("\n[INFO] 开始自动填写注册表单...")
            if not self.fill_registration_form():
                print("[ERROR] 注册表单填写失败")
                return False

            # 注意：fill_registration_form() 已经包含了表单提交
            # 现在直接调用 handle_post_submission() 来处理后续流程
            print("\n[INFO] 处理提交后的页面...")
            post_result = self.handle_post_submission()

            if post_result == "OAUTH_COMPLETED":
                print(f"\n[SUCCESS] 完整注册和OAuth授权流程完成!")

                # 拷贝AWS SSO缓存文件到sandbox_files/OAuth目录
                print("[INFO] 开始处理AWS SSO缓存文件...")
                self.copy_aws_sso_cache_files()

                print("[INFO] GitHub账户注册、验证和Kiro授权已全部完成")
                print("[INFO] EdgeDriver已自动关闭，程序正常退出")
                return True
            elif post_result:
                print(f"\n[SUCCESS] 完整注册流程完成!")
                print("[INFO] GitHub账户注册和验证已完成")

                print("[INFO] EdgeDriver进程将保持运行，浏览器窗口保持打开")
                print("[INFO] 完成后可手动关闭浏览器或按Ctrl+C退出程序")

                # 保持程序运行，不关闭EdgeDriver（采用test_文件的稳定机制）
                try:
                    print("\n[WAIT] 程序等待中... (按Ctrl+C退出)")
                    while True:
                        time.sleep(10)  # 每10秒检查一次，保持进程存活
                except KeyboardInterrupt:
                    print("\n[INFO] 用户中断程序，准备退出...")
                    return True
            else:
                print(f"\n[PARTIAL] 注册表单已提交，但后续验证未完成")
                print("[INFO] 请手动完成验证步骤")

                print("[INFO] EdgeDriver进程将保持运行，浏览器窗口保持打开")
                print("[INFO] 完成后可手动关闭浏览器或按Ctrl+C退出程序")

                # 保持程序运行，不关闭EdgeDriver
                try:
                    print("\n[WAIT] 程序等待中... (按Ctrl+C退出)")
                    while True:
                        time.sleep(10)  # 每10秒检查一次，保持进程存活
                except KeyboardInterrupt:
                    print("\n[INFO] 用户中断程序，准备退出...")
                    return True

        except Exception as e:
            print(f"[ERROR] 集成模式自动化过程中发生错误: {e}")
            return False

        finally:
            # 采用test_文件的稳定机制：不主动关闭EdgeDriver
            # 让EdgeDriver保持运行状态，避免闪退
            # 只有在异常情况下才关闭driver（但这里我们选择不关闭以保持稳定性）
            pass

# 注意：此文件由 kiro_login_automation.py 调用，不需要独立的测试入口