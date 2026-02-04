#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google 注册自动化脚本
功能：自动化 Google 账号注册流程（基于GitHub版本架构）
作者：Claude Code Assistant
使用 Edge 浏览器进行网页自动化

🎛️ 新功能：可视化控制面板
- 运行时会在屏幕右上角显示控制面板
- 暂停/继续按钮：可随时暂停或恢复自动化流程
- 退出当前页按钮：退出当前页面操作，等待页面变化后继续
- 实时状态显示：显示当前自动化状态
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

# 导入自动化框架
from web_automation_framework import (
    WebAutomationFramework,
    ActionSequence,
    InputAction,
    ClickAction,
    DelayAction,
    PageContext,
    ActionResult,
    SequenceAction
)

class GoogleRegistrationAutomator:
    def __init__(self, initial_url=None):
        self.driver = None
        self.wait = None
        self.framework = None
        self.fingerprints = {}
        self.initial_url = initial_url or "https://accounts.google.com/signup"  # 新框架方法：使用传入的URL
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
        """加载硬件指纹配置（完全照搬GitHub版本）"""
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

    def setup_edge_driver(self):
        """配置 Edge 浏览器驱动（完全照搬GitHub版本）"""
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

            # 执行 CDP 命令隐藏自动化特征并应用完整指纹虚拟（完全照搬GitHub版本）
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

    def create_workflow_config(self) -> dict:
        """创建工作流程配置（重构版 - 原子操作组合优先）"""
        workflow_config = {
            "name": "Google Registration Workflow v2.0",
            "pages": [
                {
                    "id": "google_signin_page",
                    "description": "Google 登录页面（需要点击创建账号）",
                    "primary_identifier": {
                        "type": "url",
                        "pattern": r"accounts\.google\.com/v3/signin",
                        "confidence": 0.9
                    },
                    "fallback_identifiers": [
                        {
                            "type": "title",
                            "pattern": r"登录.*Google|Sign in.*Google|ログイン.*Google|로그인.*Google",
                            "confidence": 0.7
                        }
                    ],
                    "actions": [
                        {"type": "delay", "duration": 2.0, "description": "等待页面完全加载"},

                        # 方案一：恢复为原有callback格式（稳定优先）
                        {
                            "type": "callback",
                            "callback_function": self.find_create_account_button_callback,
                            "timeout": 30,
                            "retry_count": 3,
                            "description": "智能查找并点击创建账号按钮"
                        },

                        {"type": "delay", "duration": 3.0, "description": "等待页面跳转到注册页面"}
                    ],
                    "next_pages": ["google_name_page"]
                },
                {
                    "id": "google_name_page",
                    "description": "Google 姓名填写页面",
                    "primary_identifier": {
                        "type": "url",
                        "pattern": r"accounts\.google\.com/lifecycle/steps/signup/name",
                        "confidence": 0.9
                    },
                    "fallback_identifiers": [
                        {
                            "type": "title",
                            "pattern": r"建立.*Google.*帳戶|Create.*Google.*Account|Google.*アカウント.*作成|Google.*계정.*만들기",
                            "confidence": 0.7
                        }
                    ],
                    "actions": [
                        {"type": "delay", "duration": 2.0, "description": "等待姓名页面完全加载"},

                        # 等待表单元素出现
                        {"type": "wait_for_element", "selector": "#firstName", "condition": "visible", "timeout": 15},

                        # 生成姓名数据（简化回调函数）
                        {"type": "callback", "callback_function": self.generate_name_data_callback, "description": "生成随机姓名数据"},

                        # 使用原子操作序列填写姓名表单（修复：正确的填写顺序）
                        {
                            "type": "sequence",
                            "description": "填写姓名表单（先姓氏后名字）",
                            "actions": [
                                {"type": "scroll", "direction": "to_element", "selector": "#lastName"},
                                {"type": "input", "selector": "#lastName", "value": "{lastName}", "typing_style": "human", "description": "填写姓氏（上面的字段）"},
                                {"type": "input", "selector": "#firstName", "value": "{firstName}", "typing_style": "human", "description": "填写名字（下面的字段）"},
                                {"type": "delay", "duration": 1.0, "description": "填写完成后短暂停顿"},
                                {"type": "click", "selector": "#collectNameNext > div > button"}
                            ]
                        },

                        # 修复：删除错误的条件检测
                        # .VfPpkd-Jh9lGc 是按钮内部组件，不是错误提示
                        # 页面跳转是正常流程，不需要重试机制

                        {"type": "delay", "duration": 3.0, "description": "等待页面跳转"}
                    ],
                    "next_pages": ["google_birthday_gender_page"]
                },
                {
                    "id": "google_gmail_selection_page",
                    "description": "Gmail 邮箱选择页面",
                    "primary_identifier": {
                        "type": "url",
                        "pattern": r"accounts\.google\.com/lifecycle/steps/signup/username",
                        "confidence": 0.9
                    },
                    "fallback_identifiers": [
                        {
                            "type": "title",
                            "pattern": r"选择您的.*Gmail.*邮箱|Choose.*Gmail.*address|Gmail.*アドレス.*選択|Gmail.*주소.*선택",
                            "confidence": 0.7
                        }
                    ],
                    "actions": [
                        {"type": "delay", "duration": 2.0, "description": "等待Gmail选择页面完全加载"},

                        # 使用callback处理多语言Gmail选择
                        {"type": "callback", "callback_function": self.handle_gmail_selection_callback, "description": "处理Gmail邮箱选择（多语言支持）"},

                        {"type": "delay", "duration": 3.0, "description": "等待页面跳转"}
                    ],
                    "next_pages": []
                },
                {
                    "id": "google_birthday_gender_page",
                    "description": "Google 生日性别填写页面",
                    "primary_identifier": {
                        "type": "url",
                        "pattern": r"accounts\.google\.com/lifecycle/steps/signup/birthdaygender",
                        "confidence": 0.9
                    },
                    "fallback_identifiers": [
                        {
                            "type": "title",
                            "pattern": r"基本.*信息.*出生日期.*性别|Basic.*information.*birthday.*gender|基本.*資訊.*出生日期.*性別|基本.*情報.*生年月日.*性別|기본.*정보.*생년월일.*성별",
                            "confidence": 0.7
                        }
                    ],
                    "actions": [
                        {"type": "delay", "duration": 2.0, "description": "等待生日性别页面完全加载"},

                        # 等待表单元素出现
                        {"type": "wait_for_element", "selector": "#year", "condition": "visible", "timeout": 15},

                        # 生成生日数据（简化回调函数）
                        {"type": "callback", "callback_function": self.generate_birthday_data_callback, "description": "生成随机生日数据"},

                        # 使用原子操作序列填写生日信息（修复：按年→月→日的人类习惯顺序）
                        {
                            "type": "sequence",
                            "description": "填写生日信息（年→月→日顺序）",
                            "actions": [
                                {"type": "scroll", "direction": "to_element", "selector": "#year"},
                                {"type": "input", "selector": "#year", "value": "{birthYear}", "typing_style": "human", "description": "填写年份"},
                                {"type": "callback", "callback_function": self.handle_month_dropdown_callback, "description": "选择月份下拉框"},
                                {"type": "input", "selector": "#day", "value": "{birthDay}", "typing_style": "human", "description": "填写日期"}
                            ]
                        },

                        # 处理性别下拉框（分离出来，只处理性别）
                        {"type": "callback", "callback_function": self.handle_gender_dropdown_callback, "description": "处理性别下拉框"},

                        # 使用原子操作点击下一步
                        {
                            "type": "sequence",
                            "description": "提交生日性别表单",
                            "actions": [
                                {"type": "delay", "duration": 1.0, "description": "填写完成后停顿"},
                                {"type": "scroll", "direction": "to_element", "selector": "#birthdaygenderNext"},
                                {"type": "click", "selector": "#birthdaygenderNext > div > button"}
                            ]
                        },

                        # 智能错误处理
                        {
                            "type": "conditional",
                            "description": "检查提交结果",
                            "condition": {
                                "type": "element_exists",
                                "selector": ".VfPpkd-Jh9lGc"
                            },
                            "if_true": [
                                {
                                    "type": "retry",
                                    "description": "重新尝试提交",
                                    "actions": [
                                        {"type": "click", "selector": "#birthdaygenderNext > div > button"}
                                    ],
                                    "max_attempts": 2,
                                    "retry_delay": 2.0
                                }
                            ]
                        },

                        {"type": "delay", "duration": 3.0, "description": "等待页面跳转"}
                    ],
                    "next_pages": ["google_gmail_selection_page"]
                }
            ]
        }

        return workflow_config

    def execute_workflow(self) -> bool:
        """执行完整的工作流程（重构版）"""
        try:
            print("🚀 开始执行 Google 注册自动化工作流程 v2.0")

            # 1. 设置 WebDriver
            if not self.setup_edge_driver():
                return False

            # 2. 导航到初始URL
            if not self.navigate_to_url(self.initial_url):
                return False

            # 3. 初始化表单数据存储
            self.current_form_data = {}

            # 4. 创建并设置框架（启用控制面板）
            workflow_config = self.create_workflow_config()
            self.framework = WebAutomationFramework(
                workflow_config=workflow_config,
                enable_control_panel=True  # 🎛️ 启用可视化控制面板
            )
            self.framework.set_driver(self.driver)

            # 5. 设置动态变量获取器
            self.framework.dynamic_variable_getter = self.get_dynamic_variable_value

            # 5.1. 设置上下文提供者（新增：低耦合设计）
            self.framework.set_context_provider(self)

            # 6. 执行工作流程
            print("\n🎬 开始执行自动化工作流程...")
            result = self.framework.execute_workflow()

            if result:
                print("✅ 自动化工作流程执行成功！")
                print("📄 应该已经跳转到下一个页面")

                # 获取跳转后的页面信息
                time.sleep(2)
                self.get_current_page_info()

                return True
            else:
                print("❌ 工作流程执行失败")
                return False

        except Exception as e:
            print(f"❌ 工作流程执行失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def human_like_type(self, element, text, min_delay=0.05, max_delay=0.15):
        """模拟人类打字，逐字符输入（完全照搬GitHub版本）"""
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

    def load_names_from_file(self):
        """从name.txt文件加载姓名列表（完全照搬GitHub版本）"""
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

    def generate_random_name_data(self):
        """生成随机的姓名、邮箱、用户名和密码（完全照搬GitHub版本）"""
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

            # 生成用户名（符合Google规则：只能包含字母数字和点号）
            # 将空格替换为点号，并添加随机数字
            username_base = selected_name.replace(' ', '.').replace('_', '.').lower()
            random_digits = ''.join(random.choices(string.digits, k=random.randint(2, 4)))
            username = f"{username_base}{random_digits}"

            # 确保用户名不以点号开头或结尾
            username = username.strip('.')
            if not username or username.startswith('.') or username.endswith('.'):
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

    def load_names_from_file(self):
        """从name.txt文件加载姓名列表（与GitHub版本保持一致）"""
        try:
            # 尝试多个可能的name.txt文件路径
            possible_paths = [
                "C:\\sandbox_files\\name.txt",
                "sandbox_files\\name.txt",
                "name.txt"
            ]

            name_file_path = None
            for path in possible_paths:
                if Path(path).exists():
                    name_file_path = path
                    break

            if not name_file_path:
                name_file_path = possible_paths[0]  # 默认使用第一个路径
                print(f"[WARNING] name.txt文件不存在，将使用默认路径: {name_file_path}")
                return None, []

            with open(name_file_path, 'r', encoding='utf-8-sig') as f:
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

    def generate_random_name_data(self):
        """生成随机的姓名、邮箱、用户名和密码（与GitHub版本保持一致）"""
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

            # 生成用户名（符合Google Gmail规则：只能包含字母数字和点号）
            # 将空格和下划线替换为点号，并添加随机数字
            username_base = selected_name.replace(' ', '.').replace('_', '.').lower()
            random_digits = ''.join(random.choices(string.digits, k=random.randint(2, 4)))
            username = f"{username_base}{random_digits}"

            # 确保用户名不以点号开头或结尾，且不包含连续点号
            username = username.strip('.')
            # 移除连续的点号
            while '..' in username:
                username = username.replace('..', '.')

            if not username or username.startswith('.') or username.endswith('.'):
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

    # ==================== 简化的回调函数（重构版） ====================

    def find_create_account_button_callback(self, driver, page_context):
        """查找并点击创建账号按钮（简化版回调函数）"""
        try:
            print("[CALLBACK] 智能查找创建账号按钮")

            # 测试多个可能的选择器
            selectors_to_try = [
                "#yDmH0d > c-wiz > main > div.JYXaTc > div > div.FO2vFd > div > div > div > button > span",
                "//*[@id='yDmH0d']/c-wiz/main/div[3]/div/div[2]/div/div/div/button/span",
                "//span[contains(text(), '创建账号') or contains(text(), 'Create account') or contains(text(), 'アカウント作成') or contains(text(), '계정 만들기')]",
                "//button[contains(@class, 'VfPpkd-LgbsSe')]//span[contains(text(), '创建') or contains(text(), 'Create')]"
            ]

            for i, selector in enumerate(selectors_to_try):
                try:
                    print(f"[INFO] 尝试选择器 {i+1}: {selector[:50]}...")

                    if selector.startswith("//"):
                        element = driver.find_element(By.XPATH, selector)
                    else:
                        element = driver.find_element(By.CSS_SELECTOR, selector)

                    if element.is_displayed() and element.is_enabled():
                        print(f"[SUCCESS] 找到创建账号按钮: {element.text}")

                        # 滚动到元素位置并点击
                        driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        time.sleep(random.uniform(0.5, 1.0))
                        driver.execute_script("arguments[0].click();", element)

                        print("[SUCCESS] 创建账号按钮点击完成")
                        return ActionSequence([DelayAction(2.0, "点击后等待页面响应")])

                except Exception as e:
                    print(f"[WARNING] 选择器 {i+1} 失败: {e}")
                    continue

            return ActionSequence.failed("未找到创建账号按钮")

        except Exception as e:
            print(f"[ERROR] 查找创建账号按钮失败: {e}")
            return ActionSequence.failed(str(e))

    def generate_name_data_callback(self, driver, page_context):
        """生成姓名数据（专用数据生成回调）"""
        try:
            print("[CALLBACK] 生成随机姓名数据")

            # 生成随机姓名数据
            name_data = self.generate_random_name_data()
            if not name_data:
                return ActionSequence.failed("无法生成姓名数据")

            # 从姓名中分离姓氏和名字（修复版：正确理解name.txt格式）
            # name.txt格式：每行是 "名字 姓氏"
            full_name = name_data.get('name', '张三')
            name_parts = full_name.split(' ')

            if len(name_parts) >= 2:
                # name.txt格式：第一部分是名字，第二部分是姓氏
                actual_first_name = name_parts[0]  # 真正的名字
                actual_last_name = ' '.join(name_parts[1:])  # 真正的姓氏
                print(f"[DEBUG] 姓名分离: 名字='{actual_first_name}', 姓氏='{actual_last_name}'")
            else:
                # 对于中文名或单个词：判断是否包含中文字符
                if any('\u4e00' <= char <= '\u9fff' for char in full_name):
                    # 中文名：前面是姓，后面是名
                    if len(full_name) >= 2:
                        actual_first_name = full_name[1:]  # 名字（后面部分）
                        actual_last_name = full_name[0]    # 姓氏（第一个字）
                        print(f"[DEBUG] 中文姓名分离: 名字='{actual_first_name}', 姓氏='{actual_last_name}'")
                    else:
                        actual_first_name = full_name
                        actual_last_name = "氏"
                        print(f"[DEBUG] 单字姓名: 名字='{actual_first_name}', 姓氏='{actual_last_name}'")
                else:
                    # 英文单词：作为名字，添加默认姓氏
                    actual_first_name = full_name
                    actual_last_name = "Smith"  # 默认英文姓氏
                    print(f"[DEBUG] 单词英文名: 名字='{actual_first_name}', 姓氏='{actual_last_name}'")

            print(f"[INFO] 最终姓名分离结果: 名字='{actual_first_name}', 姓氏='{actual_last_name}'")

            # 修复：正确的页面字段映射
            # 页面布局：上面是#lastName(姓氏字段)，下面是#firstName(名字字段)
            # 填写顺序：先填#lastName(姓氏)，再填#firstName(名字)
            self.current_form_data = {
                'firstName': actual_first_name,  # #firstName字段填入名字
                'lastName': actual_last_name,    # #lastName字段填入姓氏
                'username': name_data.get('username', ''),  # Gmail用户名
                'full_name_data': name_data
            }

            print(f"[INFO] 页面字段映射: #lastName -> '{actual_last_name}' (姓氏), #firstName -> '{actual_first_name}' (名字)")
            print(f"[INFO] 填写顺序: 先填姓氏字段(#lastName)，再填名字字段(#firstName)")
            print(f"[INFO] Gmail用户名: {name_data.get('username', '')}")

            return ActionSequence([DelayAction(0.5, "数据生成完成")])

        except Exception as e:
            print(f"[ERROR] 生成姓名数据失败: {e}")
            return ActionSequence.failed(str(e))

    def generate_birthday_data_callback(self, driver, page_context):
        """生成生日数据（专用数据生成回调）"""
        try:
            print("[CALLBACK] 生成随机生日数据")

            # 生成随机生日数据
            birth_year = random.randint(1980, 1999)
            birth_month = random.randint(1, 9)
            birth_day = random.randint(1, 28)

            print(f"[INFO] 生成的生日: {birth_year}年{birth_month}月{birth_day}日")

            # 将数据存储到全局变量中供后续使用
            if not hasattr(self, 'current_form_data'):
                self.current_form_data = {}

            self.current_form_data.update({
                'birthYear': str(birth_year),
                'birthMonth': birth_month,
                'birthDay': str(birth_day)
            })

            return ActionSequence([DelayAction(0.5, "生日数据生成完成")])

        except Exception as e:
            print(f"[ERROR] 生成生日数据失败: {e}")
            return ActionSequence.failed(str(e))

    def handle_month_dropdown_callback(self, driver, page_context):
        """处理月份下拉框（分离出来的月份处理）"""
        try:
            print("[CALLBACK] 处理月份下拉框")

            # 获取之前生成的数据
            if not hasattr(self, 'current_form_data'):
                return ActionSequence.failed("未找到生日数据")

            birth_month = self.current_form_data.get('birthMonth', 1)

            # 处理月份下拉框
            month_selectors = [
                "#month > div > div.VfPpkd-TkwUic > div",
                "//*[@id='month']/div/div[1]/div"
            ]

            month_element = None
            for selector in month_selectors:
                try:
                    if selector.startswith("//"):
                        month_element = driver.find_element(By.XPATH, selector)
                    else:
                        month_element = driver.find_element(By.CSS_SELECTOR, selector)

                    if month_element.is_displayed():
                        print(f"[SUCCESS] 找到月份下拉框: {selector}")
                        break
                except:
                    continue

            if not month_element:
                return ActionSequence.failed("未找到月份下拉框")

            # 点击月份下拉框
            print(f"[INFO] 选择月份: {birth_month}")
            month_element.click()
            time.sleep(random.uniform(1.0, 2.0))

            # 选择月份选项
            try:
                month_option_selectors = [
                    f"li[data-value='{birth_month}']",
                    f"//li[@data-value='{birth_month}']",
                    f"//span[contains(text(), '{birth_month} 月')]"
                ]

                month_option = None
                for option_selector in month_option_selectors:
                    try:
                        if option_selector.startswith("//"):
                            month_option = driver.find_element(By.XPATH, option_selector)
                        else:
                            month_option = driver.find_element(By.CSS_SELECTOR, option_selector)

                        if month_option.is_displayed():
                            print(f"[SUCCESS] 找到月份选项: {option_selector}")
                            break
                    except:
                        continue

                if month_option:
                    driver.execute_script("arguments[0].click();", month_option)
                    print(f"[SUCCESS] 月份选择完成: {birth_month}月")
                else:
                    # 备用方法：键盘输入
                    from selenium.webdriver.common.keys import Keys
                    month_element.send_keys(str(birth_month))
                    time.sleep(0.3)
                    month_element.send_keys(Keys.ENTER)
                    print(f"[SUCCESS] 月份选择完成（键盘方式）: {birth_month}月")

                return ActionSequence([DelayAction(0.5, "月份选择完成")])

            except Exception as e:
                print(f"[ERROR] 选择月份失败: {e}")
                return ActionSequence.failed(f"选择月份失败: {e}")

        except Exception as e:
            print(f"[ERROR] 处理月份下拉框失败: {e}")
            return ActionSequence.failed(str(e))

    def handle_gender_dropdown_callback(self, driver, page_context):
        """处理性别下拉框（分离出来的性别处理）"""
        try:
            print("[CALLBACK] 处理性别下拉框")

            # 处理性别下拉框
            time.sleep(random.uniform(0.5, 1.0))

            gender_selectors = [
                "#gender > div > div.VfPpkd-TkwUic > div",
                "//*[@id='gender']/div/div[1]/div"
            ]

            gender_element = None
            for selector in gender_selectors:
                try:
                    if selector.startswith("//"):
                        gender_element = driver.find_element(By.XPATH, selector)
                    else:
                        gender_element = driver.find_element(By.CSS_SELECTOR, selector)

                    if gender_element.is_displayed():
                        print(f"[SUCCESS] 找到性别下拉框: {selector}")
                        break
                except:
                    continue

            if not gender_element:
                return ActionSequence.failed("未找到性别下拉框")

            # 点击性别下拉框
            print("[INFO] 选择性别（随机选择）")
            gender_element.click()
            time.sleep(random.uniform(1.0, 2.0))

            # 随机选择性别
            try:
                gender_options = ["1", "2", "3"]  # 男、女、不愿透露
                selected_gender = random.choice(gender_options)
                gender_names = {"1": "男", "2": "女", "3": "不愿透露"}

                print(f"[INFO] 随机选择性别: {gender_names[selected_gender]}")

                # 性别选项位置映射
                gender_position_map = {"1": 2, "2": 1, "3": 3}
                li_position = gender_position_map[selected_gender]

                gender_option_selectors = [
                    f"#gender > div > div.VfPpkd-xl07Ob-XxIAqe.VfPpkd-xl07Ob-XxIAqe-OWXEXe-tsQazb.VfPpkd-xl07Ob.VfPpkd-YPmvEd.s8kOBc.dmaMHc.VfPpkd-xl07Ob-XxIAqe-OWXEXe-uxVfW-FNFY6c-uFfGwd.VfPpkd-xl07Ob-XxIAqe-OWXEXe-FNFY6c > ul > li:nth-child({li_position})",
                    f"//*[@id='gender']/div/div[2]/ul/li[{li_position}]",
                    f"li[data-value='{selected_gender}']",
                    f"//span[contains(text(), '{gender_names[selected_gender]}')]"
                ]

                gender_option = None
                for option_selector in gender_option_selectors:
                    try:
                        if option_selector.startswith("//"):
                            gender_option = driver.find_element(By.XPATH, option_selector)
                        else:
                            gender_option = driver.find_element(By.CSS_SELECTOR, option_selector)

                        if gender_option.is_displayed():
                            print(f"[SUCCESS] 找到性别选项: {option_selector}")
                            break
                    except:
                        continue

                if gender_option:
                    driver.execute_script("arguments[0].click();", gender_option)
                    print(f"[SUCCESS] 性别选择完成: {gender_names[selected_gender]}")
                else:
                    # 备用方法：键盘导航
                    from selenium.webdriver.common.keys import Keys
                    for i in range(3):
                        gender_element.send_keys(Keys.ARROW_DOWN)
                        time.sleep(random.uniform(0.5, 1.0))
                    gender_element.send_keys(Keys.ENTER)
                    print("[SUCCESS] 性别选择完成（键盘方式）")

                return ActionSequence([DelayAction(1.0, "性别选择完成")])

            except Exception as e:
                print(f"[ERROR] 选择性别失败: {e}")
                return ActionSequence.failed(f"选择性别失败: {e}")

        except Exception as e:
            print(f"[ERROR] 处理性别下拉框失败: {e}")
            return ActionSequence.failed(str(e))

    # ==================== 变量替换机制 ====================

    def get_dynamic_variable_value(self, variable_name):
        """获取动态变量值（用于原子操作的变量替换）"""
        if hasattr(self, 'current_form_data') and variable_name in self.current_form_data:
            return self.current_form_data[variable_name]
        return f"{{missing_{variable_name}}}"

    def get_current_page_info(self):
        """获取当前页面信息"""
        try:
            current_url = self.driver.current_url
            page_title = self.driver.title

            print(f"\n📄 当前页面信息:")
            print(f"   URL: {current_url}")
            print(f"   标题: {page_title}")

            return {
                "url": current_url,
                "title": page_title
            }

        except Exception as e:
            print(f"❌ 获取页面信息失败: {e}")
            return {}

    def detect_gmail_page_variant(self, driver):
        """检测Gmail选择页面的变体类型"""
        try:
            print("[INFO] 检测Gmail页面变体...")

            # 检测是否存在radio按钮组（变体1的特征）
            radio_selectors = [
                'input[name="usernameRadio"]',
                'input[type="radio"]',
                '[role="radiogroup"]'
            ]

            has_radio_buttons = False
            for selector in radio_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"[DEBUG] 找到radio元素: {len(elements)}个，选择器: {selector}")
                        has_radio_buttons = True
                        break
                except Exception as e:
                    print(f"[DEBUG] radio检测失败 {selector}: {e}")
                    continue

            if has_radio_buttons:
                # 进一步检测是否有自定义选项
                custom_option_indicators = [
                    'input[value="custom"]',
                    '[data-value="custom"]',
                    # 多语言文本检测
                    "//*[contains(text(), '创建您自己的')]",
                    "//*[contains(text(), '自分で')]",
                    "//*[contains(text(), 'Create your own')]",
                    "//*[contains(text(), '나만의')]"
                ]

                has_custom_option = False
                for indicator in custom_option_indicators:
                    try:
                        if indicator.startswith('//'):
                            # XPath
                            element = driver.find_element(By.XPATH, indicator)
                        else:
                            # CSS Selector
                            element = driver.find_element(By.CSS_SELECTOR, indicator)

                        if element and element.is_displayed():
                            print(f"[DEBUG] 找到自定义选项指示器: {indicator}")
                            has_custom_option = True
                            break
                    except Exception as e:
                        print(f"[DEBUG] 自定义选项检测失败 {indicator}: {e}")
                        continue

                if has_custom_option:
                    print("[INFO] 检测结果: 变体1 - 有已登录账号的页面")
                    return "variant_1_with_accounts"

            # 检测是否直接有用户名输入框（变体2的特征）
            direct_input_selectors = [
                'input[name="Username"]',
                'input[aria-label*="Gmail"]',
                'input[aria-label*="gmail"]'
            ]

            has_direct_input = False
            for selector in direct_input_selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.is_displayed():
                        print(f"[DEBUG] 找到直接输入框: {selector}")
                        has_direct_input = True
                        break
                except Exception as e:
                    print(f"[DEBUG] 直接输入框检测失败 {selector}: {e}")
                    continue

            if has_direct_input and not has_radio_buttons:
                print("[INFO] 检测结果: 变体2 - 直接输入框页面")
                return "variant_2_direct_input"

            # 如果有输入框但也有radio按钮，可能是变体1点击后的状态
            if has_direct_input and has_radio_buttons:
                print("[INFO] 检测结果: 变体1 - 有已登录账号的页面（可能已点击自定义选项）")
                return "variant_1_with_accounts"

            print("[WARNING] 无法确定页面变体，默认为变体2")
            return "variant_2_direct_input"

        except Exception as e:
            print(f"[ERROR] 页面变体检测失败: {e}")
            return "variant_2_direct_input"  # 默认为变体2

    def handle_gmail_selection_callback(self, driver, page_context):
        """处理Gmail邮箱选择（多语言支持，兼容两种页面变体）"""
        try:
            print("[CALLBACK] 处理Gmail邮箱选择（多语言支持，兼容两种变体）")

            # 首先检测页面变体
            page_variant = self.detect_gmail_page_variant(driver)
            print(f"[INFO] 检测到页面变体: {page_variant}")

            if page_variant == "variant_1_with_accounts":
                # 变体1：有已登录账号，需要点击自定义选项
                print("[INFO] 处理变体1：有已登录账号的页面")

                # 策略1：直接点击radio按钮（最简单最稳定）
                custom_clicked = False

                # 方法1：直接点击最后一个radio按钮（通常是自定义选项）
                try:
                    print("[INFO] 查找所有radio按钮...")
                    radio_elements = driver.find_elements(By.CSS_SELECTOR, 'input[name="usernameRadio"]')
                    print(f"[INFO] 找到 {len(radio_elements)} 个radio按钮")

                    if radio_elements:
                        last_radio = radio_elements[-1]  # 最后一个通常是自定义选项
                        print(f"[INFO] 尝试点击最后一个radio按钮（索引: {len(radio_elements)-1}）")

                        # 确保元素可见和可点击
                        if last_radio.is_displayed() and last_radio.is_enabled():
                            # 滚动到元素位置
                            driver.execute_script("arguments[0].scrollIntoView(true);", last_radio)
                            time.sleep(0.5)

                            # 点击radio按钮
                            driver.execute_script("arguments[0].click();", last_radio)
                            print("✅ 成功点击最后一个radio按钮")
                            custom_clicked = True
                        else:
                            print("[DEBUG] 最后一个radio按钮不可见或不可点击")
                except Exception as e:
                    print(f"[DEBUG] 点击最后一个radio失败: {e}")

                # 方法2：尝试通过value="custom"点击
                if not custom_clicked:
                    try:
                        print("[INFO] 尝试通过value='custom'查找radio...")
                        custom_radio = driver.find_element(By.CSS_SELECTOR, 'input[value="custom"]')
                        if custom_radio and custom_radio.is_displayed():
                            driver.execute_script("arguments[0].scrollIntoView(true);", custom_radio)
                            time.sleep(0.5)
                            driver.execute_script("arguments[0].click();", custom_radio)
                            print("✅ 成功通过value='custom'点击radio")
                            custom_clicked = True
                    except Exception as e:
                        print(f"[DEBUG] value='custom'方法失败: {e}")

                # 方法3：遍历所有radio，查找value="custom"
                if not custom_clicked:
                    try:
                        print("[INFO] 遍历所有radio查找custom选项...")
                        all_radios = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
                        for i, radio in enumerate(all_radios):
                            try:
                                value = radio.get_attribute('value')
                                print(f"[DEBUG] Radio {i}: value='{value}'")
                                if value == 'custom':
                                    driver.execute_script("arguments[0].scrollIntoView(true);", radio)
                                    time.sleep(0.5)
                                    driver.execute_script("arguments[0].click();", radio)
                                    print(f"✅ 成功点击custom radio（索引: {i}）")
                                    custom_clicked = True
                                    break
                            except Exception as e:
                                print(f"[DEBUG] 检查radio {i}失败: {e}")
                                continue
                    except Exception as e:
                        print(f"[DEBUG] 遍历radio失败: {e}")


                if not custom_clicked:
                    return ActionSequence.failed("无法找到或点击自定义Gmail选项")

                # 等待输入框出现
                time.sleep(1.0)

            elif page_variant == "variant_2_direct_input":
                # 变体2：没有已登录账号，直接显示输入框
                print("[INFO] 处理变体2：直接输入框页面，无需点击选项")
                # 直接跳到输入框处理

            else:
                return ActionSequence.failed(f"未知的页面变体: {page_variant}")

            # 查找用户名输入框
            username_input_selectors = [
                'input[name="Username"]',
                'input[aria-label*="Gmail"]',
                'input[aria-label*="gmail"]',
                '.whsOnd.zHQkBf'  # 根据HTML源码的class
            ]

            username_input = None
            for selector in username_input_selectors:
                try:
                    print(f"[INFO] 查找用户名输入框: {selector}")
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.is_displayed():
                        username_input = element
                        print(f"✅ 找到用户名输入框: {selector}")
                        break
                except Exception as e:
                    print(f"[DEBUG] 输入框选择器 {selector} 失败: {e}")
                    continue

            if not username_input:
                return ActionSequence.failed("无法找到用户名输入框")

            # 获取用户名
            username = self.get_dynamic_variable_value('username')
            if not username or username.startswith('{missing_'):
                return ActionSequence.failed("无法获取用户名数据")

            print(f"[INFO] 填写Gmail用户名: {username}")

            # 清空输入框并输入用户名
            username_input.clear()
            time.sleep(0.5)

            # 模拟人类输入
            for char in username:
                username_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            time.sleep(1.0)

            # 查找并点击下一步按钮
            next_button_selectors = [
                '#next > div > button',
                'button[type="button"]:contains("下一步")',
                'button[type="button"]:contains("Next")',
                'button[type="button"]:contains("次へ")',
                '.VfPpkd-LgbsSe:contains("下一步")',
                '.VfPpkd-LgbsSe:contains("Next")',
                '.VfPpkd-LgbsSe:contains("次へ")'
            ]

            next_clicked = False
            for selector in next_button_selectors:
                try:
                    print(f"[INFO] 尝试点击下一步按钮: {selector}")
                    if ':contains(' in selector:
                        # 使用XPath处理contains
                        text = selector.split(':contains("')[1].split('")')[0]
                        xpath = f"//button[contains(text(), '{text}')]"
                        element = driver.find_element(By.XPATH, xpath)
                    else:
                        element = driver.find_element(By.CSS_SELECTOR, selector)

                    if element and element.is_displayed():
                        driver.execute_script("arguments[0].click();", element)
                        print(f"✅ 成功点击下一步按钮: {selector}")
                        next_clicked = True
                        break
                except Exception as e:
                    print(f"[DEBUG] 下一步按钮选择器 {selector} 失败: {e}")
                    continue

            if not next_clicked:
                return ActionSequence.failed("无法找到或点击下一步按钮")

            print("✅ Gmail邮箱选择处理完成")
            return ActionSequence([DelayAction(1.0, "Gmail选择完成")])

        except Exception as e:
            print(f"❌ Gmail邮箱选择处理失败: {e}")
            return ActionSequence.failed(str(e))

    def cleanup(self):
        """清理资源"""
        try:
            if self.driver:
                print("🧹 正在清理 WebDriver...")
                # 不自动关闭浏览器，让用户手动关闭
                # self.driver.quit()
                print("ℹ️ 浏览器保持打开状态")
        except Exception as e:
            print(f"⚠️ 清理过程中出现错误: {e}")


def main():
    """主函数 - 用于测试"""
    try:
        print("🧪 Google 注册自动化 - 第一个页面测试")

        # 创建自动化器实例
        automator = GoogleRegistrationAutomator()

        # 加载硬件指纹
        automator.load_hardware_fingerprints()

        # 执行工作流程
        result = automator.execute_workflow()

        if result:
            print("\n🎉 第一个页面自动化测试成功！")
            print("📝 请检查浏览器是否已跳转到注册页面")
            print("🔄 浏览器将保持打开状态供您查看结果")
        else:
            print("\n❌ 第一个页面自动化测试失败")

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()