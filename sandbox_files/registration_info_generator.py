#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立注册信息生成器工具
功能：生成随机注册信息、接收邮件验证码、管理账号信息
作者：Claude Code Assistant
版本：1.0
"""

import time
import json
import random
import string
import os
import sys
import shutil
import glob
import threading
from pathlib import Path
from datetime import datetime

# TK界面和剪贴板支持
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# 尝试导入pyperclip，如果没有则提供fallback
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    print("WARNING: pyperclip not installed, using system clipboard fallback")
    PYPERCLIP_AVAILABLE = False
    # 提供一个简单的fallback
    class pyperclip:
        @staticmethod
        def copy(text):
            # 使用tkinter的剪贴板功能
            root = tk.Tk()
            root.withdraw()  # 隐藏窗口
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()  # 确保剪贴板更新
            root.destroy()

class RegistrationInfoGenerator:
    """独立的注册信息生成器"""

    def __init__(self):
        self.root = None
        self.user_data = {}
        self.status_var = None
        self.copy_tracker = {
            'password_copied': False,
            'other_field_copied': False
        }

        # 默认平台信息
        self.platform_info = {'name': 'GitHub', 'key': 'github'}
        self.detected_platform = None  # 存储检测到的平台

        print("🎯 注册信息生成器已初始化")

    def get_email_domain_from_env(self):
        """从.env文件读取邮箱域名配置"""
        try:
            # 获取可执行文件所在目录
            if getattr(sys, 'frozen', False):
                # 如果是打包后的exe
                exe_dir = Path(sys.executable).parent
            else:
                # 如果是Python脚本
                exe_dir = Path(__file__).parent

            # 尝试多个可能的.env文件路径（优先上级目录）
            possible_paths = [
                exe_dir.parent / ".env",  # 上级目录（优先）
                Path("C:/sandbox_files/.env"),
                exe_dir / ".env",  # 当前目录
                Path(".env")
            ]

            env_path = None
            for path in possible_paths:
                if path.exists():
                    env_path = path
                    print(f"[INFO] 找到.env文件: {path}")
                    break

            if not env_path:
                print(f"[WARNING] .env文件不存在，使用默认域名")
                return "kt167.cc"

            with open(env_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if line.startswith('EMAIL_DOMAIN='):
                    email_domain = line.split('=', 1)[1].strip()
                    print(f"[INFO] 从.env文件读取邮箱域名: {email_domain}")
                    return email_domain

            print("[WARNING] .env文件中未找到EMAIL_DOMAIN配置，使用默认域名")
            return "kt167.cc"

        except Exception as e:
            print(f"[ERROR] 读取.env文件失败: {e}")
            return "kt167.cc"

    def load_names_from_file(self):
        """从name.txt文件加载姓名列表"""
        try:
            # 获取可执行文件所在目录
            if getattr(sys, 'frozen', False):
                # 如果是打包后的exe
                exe_dir = Path(sys.executable).parent
            else:
                # 如果是Python脚本
                exe_dir = Path(__file__).parent

            # 尝试多个可能的name.txt文件路径（优先上级目录）
            possible_paths = [
                exe_dir.parent / "name.txt",  # 上级目录（优先）
                Path("C:/sandbox_files/name.txt"),
                exe_dir / "name.txt",  # 当前目录
                Path("name.txt")
            ]

            name_file_path = None
            for path in possible_paths:
                if path.exists():
                    name_file_path = path
                    print(f"[INFO] 找到name.txt文件: {path}")
                    break

            if not name_file_path:
                print("[WARNING] name.txt文件不存在，将使用随机英文名")
                return None

            with open(name_file_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()

            # 所有行都是姓名
            names = [line.strip() for line in lines if line.strip()]
            print(f"[INFO] 从name.txt加载了 {len(names)} 个姓名")
            return names if names else None

        except Exception as e:
            print(f"[ERROR] 加载姓名文件失败: {e}")
            return None

    def generate_registration_data(self):
        """生成注册数据"""
        try:
            # 从.env文件读取邮箱域名
            email_domain = self.get_email_domain_from_env()

            # 尝试从name.txt文件加载姓名
            name_data = self.load_names_from_file()
            if name_data:
                selected_name = random.choice(name_data)
                print(f"[INFO] 随机选择姓名: {selected_name}")
            else:
                # 生成随机英文名
                first_names = ["John", "Jane", "Mike", "Sarah", "David", "Lisa", "Tom", "Emma", "Alex", "Anna"]
                last_names = ["Smith", "Johnson", "Brown", "Davis", "Wilson", "Miller", "Moore", "Taylor", "Anderson", "Thomas"]
                selected_name = f"{random.choice(first_names)} {random.choice(last_names)}"
                print(f"[INFO] 生成随机姓名: {selected_name}")

            # 生成邮箱地址（用下划线替换空格）
            email_username = selected_name.replace(' ', '_').lower()
            email = f"{email_username}@{email_domain}"

            # 生成用户名（符合GitHub规则：只能包含字母数字和单个连字符）
            username_base = selected_name.replace(' ', '-').replace('_', '-').lower()
            random_digits = ''.join(random.choices(string.digits, k=random.randint(2, 4)))
            username = f"{username_base}{random_digits}"

            # 生成简单密码（固定9位，使用简单字符避免网站兼容性问题）
            password_length = 9
            password_parts = []

            # 至少包含1个数字和1个字母
            password_parts.append(random.choice(string.digits))
            password_parts.append(random.choice(string.ascii_lowercase))
            password_parts.append(random.choice(string.ascii_uppercase))

            # 使用简单的特殊字符，避免兼容性问题
            simple_special_chars = "+.>"
            password_parts.append(random.choice(simple_special_chars))

            # 剩余5位从字母数字中选择
            remaining_chars = string.ascii_letters + string.digits
            for _ in range(5):  # 9 - 4 = 5位
                password_parts.append(random.choice(remaining_chars))

            # 打乱顺序并组合
            random.shuffle(password_parts)
            password = ''.join(password_parts)

            print(f"[INFO] 生成的注册数据:")
            print(f"  邮箱: {email}")
            print(f"  用户名: {username}")
            print(f"  密码: {password}")
            print(f"  姓名: {selected_name}")

            return {
                'name': selected_name,
                'email': email,
                'username': username,
                'password': password
            }

        except Exception as e:
            print(f"[ERROR] 生成注册数据失败: {e}")
            return None

    def create_gui(self):
        """创建GUI界面"""
        try:
            self.root = tk.Tk()
            self.root.title("注册信息生成器 v1.0")
            self.root.resizable(False, False)

            # 禁用关闭按钮，防止用户意外关闭窗口
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing_attempt)

            # 设置窗口属性确保在任务栏显示
            self.root.wm_attributes("-toolwindow", False)
            self.root.wm_attributes("-topmost", False)

            # 定位到屏幕右侧
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            panel_width = 500  # 固定宽度500px，足够显示邮箱地址
            panel_height = 550
            x_pos = screen_width - panel_width - 20
            y_pos = 50

            self.root.geometry(f"{panel_width}x{panel_height}+{x_pos}+{y_pos}")
            self.root.configure(bg='#f0f0f0')

            # 添加窗口拖动功能
            self.setup_window_drag()
            self.setup_ui()

            return True

        except Exception as e:
            print(f"❌ 创建GUI失败: {e}")
            return False

    def on_closing_attempt(self):
        """处理用户尝试关闭窗口的操作"""
        try:
            result = messagebox.askyesno("确认退出",
                                       "确定要退出注册信息生成器吗？")
            if result:
                self.root.destroy()
        except Exception as e:
            print(f"❌ 处理关闭窗口事件失败: {e}")

    def setup_window_drag(self):
        """设置窗口拖动功能"""
        self.drag_start_x = 0
        self.drag_start_y = 0

        def start_drag(event):
            self.drag_start_x = event.x
            self.drag_start_y = event.y

        def do_drag(event):
            x = self.root.winfo_x() + event.x - self.drag_start_x
            y = self.root.winfo_y() + event.y - self.drag_start_y
            self.root.geometry(f"+{x}+{y}")

        self.root.bind("<Button-1>", start_drag)
        self.root.bind("<B1-Motion>", do_drag)

        def bind_drag_to_widget(widget):
            widget.bind("<Button-1>", start_drag)
            widget.bind("<B1-Motion>", do_drag)

        self.bind_drag_to_widget = bind_drag_to_widget

    def setup_ui(self):
        """设置用户界面"""
        # 主框架（减少内边距，不扩展）
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.pack(fill=tk.BOTH)

        # 状态栏 - 最底部
        self.status_var = tk.StringVar(value="就绪 - 点击任意信息行复制到剪贴板")
        status_label = ttk.Label(main_frame, textvariable=self.status_var,
                               font=('Arial', 8), foreground='gray')
        status_label.pack(side=tk.BOTTOM, pady=(2, 2))

        # 工具按钮区域 - 底部
        tools_frame = ttk.Frame(main_frame)
        tools_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=1)

        # 收验证码按钮区域（居中对齐）
        email_btn_frame = ttk.Frame(tools_frame)
        email_btn_frame.pack(pady=1)

        email_code_btn = ttk.Button(email_btn_frame, text="📧 收验证码",
                                   command=self.fetch_verification_codes, width=30)
        email_code_btn.pack(side=tk.LEFT, padx=(0, 2))

        # 查看邮件按钮
        view_emails_btn = ttk.Button(email_btn_frame, text="👁️ 查看",
                                     command=self.view_recent_emails, width=8)
        view_emails_btn.pack(side=tk.LEFT)

        # 打开手机网站按钮
        sms_btn = ttk.Button(tools_frame, text="📱 打开手机验证网站",
                            command=self.open_sms_website)
        sms_btn.pack(pady=1)

        # 间隔
        spacer = ttk.Label(tools_frame, text="")
        spacer.pack(pady=2)

        # 自定义按钮
        self.custom_btn = ttk.Button(tools_frame, text="✏️ 自定义",
                               command=self.show_custom_dialog,
                               state='disabled')
        self.custom_btn.pack(pady=1)

        # 注册成功确认按钮
        self.confirm_btn = ttk.Button(tools_frame, text="✅ 确认注册成功",
                               command=self.confirm_registration_success,
                               state='disabled')
        self.confirm_btn.pack(pady=1)

        # 分隔线2 - 底部上方
        separator2 = ttk.Separator(main_frame, orient='horizontal')
        separator2.pack(side=tk.BOTTOM, fill=tk.X, pady=3)

        # 标题（可拖动）
        title_label = ttk.Label(main_frame, text="🎯 注册信息生成器",
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 5))
        self.bind_drag_to_widget(title_label)
        title_label.configure(cursor="fleur")

        # 生成信息按钮
        generate_btn = ttk.Button(main_frame, text="🎲 生成新的注册信息",
                                 command=self.generate_new_info)
        generate_btn.pack(pady=3)

        # 分隔线
        separator1 = ttk.Separator(main_frame, orient='horizontal')
        separator1.pack(fill=tk.X, pady=3)

        # 信息显示区域标题
        info_label = ttk.Label(main_frame, text="📋 生成的注册信息:",
                              font=('Arial', 12, 'bold'))
        info_label.pack(anchor=tk.W, pady=(0, 2))

        # 信息显示框架（不使用滚动，直接显示）
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=0)

        # 创建信息显示行
        self.create_info_rows(info_frame)

        # 初始化时生成一次信息
        self.root.after(500, self.generate_initial_info)

    def create_info_rows(self, parent_frame):
        """创建信息显示行"""
        # 邮箱行
        self.email_frame = tk.Frame(parent_frame, relief=tk.FLAT, bd=1, cursor="hand2")
        self.email_frame.pack(fill=tk.X, pady=2, padx=5)
        self.email_content = ttk.Label(self.email_frame, text="📧 邮箱地址: 未生成", font=('Arial', 11))
        self.email_content.pack(anchor=tk.W, padx=10, pady=6)
        self.setup_clickable_row(self.email_frame, self.email_content, 'email', '邮箱')

        # 用户名行
        self.username_frame = tk.Frame(parent_frame, relief=tk.FLAT, bd=1, cursor="hand2")
        self.username_frame.pack(fill=tk.X, pady=2, padx=5)
        self.username_content = ttk.Label(self.username_frame, text="👤 用户名: 未生成", font=('Arial', 11))
        self.username_content.pack(anchor=tk.W, padx=10, pady=4)
        self.setup_clickable_row(self.username_frame, self.username_content, 'username', '用户名')

        # 密码行
        self.password_frame = tk.Frame(parent_frame, relief=tk.FLAT, bd=1, cursor="hand2")
        self.password_frame.pack(fill=tk.X, pady=2, padx=5)
        self.password_content = ttk.Label(self.password_frame, text="🔑 密码: 未生成", font=('Arial', 11))
        self.password_content.pack(anchor=tk.W, padx=10, pady=4)
        self.setup_clickable_row(self.password_frame, self.password_content, 'password', '密码')

        # 完整姓名行
        self.name_frame = tk.Frame(parent_frame, relief=tk.FLAT, bd=1, cursor="hand2")
        self.name_frame.pack(fill=tk.X, pady=2, padx=5)
        self.name_content = ttk.Label(self.name_frame, text="📛 完整姓名: 未生成", font=('Arial', 11))
        self.name_content.pack(anchor=tk.W, padx=10, pady=4)
        self.setup_clickable_row(self.name_frame, self.name_content, 'name', '完整姓名')

        # 验证码行
        self.verification_code_frame = tk.Frame(parent_frame, relief=tk.FLAT, bd=1, cursor="hand2")
        self.verification_code_frame.pack(fill=tk.X, pady=2, padx=5)
        self.verification_code_content = ttk.Label(self.verification_code_frame, text="🔢 验证码: 未获取", font=('Arial', 11))
        self.verification_code_content.pack(anchor=tk.W, padx=10, pady=4)
        self.setup_clickable_row(self.verification_code_frame, self.verification_code_content, 'verification_code', '验证码')

        # 名字行
        self.first_name_frame = tk.Frame(parent_frame, relief=tk.FLAT, bd=1, cursor="hand2")
        self.first_name_frame.pack(fill=tk.X, pady=2, padx=5)
        self.first_name_content = ttk.Label(self.first_name_frame, text="👤 名字: 未生成", font=('Arial', 11))
        self.first_name_content.pack(anchor=tk.W, padx=10, pady=4)
        self.setup_clickable_row(self.first_name_frame, self.first_name_content, 'first_name', '名字')

        # 姓氏行
        self.last_name_frame = tk.Frame(parent_frame, relief=tk.FLAT, bd=1, cursor="hand2")
        self.last_name_frame.pack(fill=tk.X, pady=2, padx=5)
        self.last_name_content = ttk.Label(self.last_name_frame, text="👥 姓氏: 未生成", font=('Arial', 11))
        self.last_name_content.pack(anchor=tk.W, padx=10, pady=4)
        self.setup_clickable_row(self.last_name_frame, self.last_name_content, 'last_name', '姓氏')

    def setup_clickable_row(self, frame, label, field, field_name):
        """设置可点击行的悬停、点击和3D效果"""
        frame.configure(bg='#f8f9fa', relief=tk.FLAT, bd=1)
        label.configure(background='#f8f9fa')

        def on_enter(event):
            frame.configure(bg='#e3f2fd', relief=tk.RAISED, bd=2)
            label.configure(background='#e3f2fd')

        def on_leave(event):
            frame.configure(bg='#f8f9fa', relief=tk.FLAT, bd=1)
            label.configure(background='#f8f9fa')

        def on_button_press(event):
            frame.configure(bg='#bbdefb', relief=tk.SUNKEN, bd=3)
            label.configure(background='#bbdefb')

        def on_button_release(event):
            frame.configure(bg='#e3f2fd', relief=tk.RAISED, bd=2)
            label.configure(background='#e3f2fd')
            self.copy_field_to_clipboard(field, field_name)

        for widget in [frame, label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<ButtonPress-1>", on_button_press)
            widget.bind("<ButtonRelease-1>", on_button_release)

    def copy_field_to_clipboard(self, field, field_name):
        """复制指定字段到剪贴板并更新状态"""
        try:
            if not self.user_data or field not in self.user_data:
                self.status_var.set(f"❌ 未找到{field_name}信息，请先生成注册信息")
                return

            value = self.user_data[field]
            if not value or value == 'N/A':
                self.status_var.set(f"❌ {field_name}信息为空，请重新生成")
                return

            pyperclip.copy(value)
            self.update_copy_tracker(field)
            self.status_var.set(f"✅ {field_name}已复制到剪贴板")
            print(f"✅ {field_name}已复制到剪贴板: {value}")

            # 3秒后恢复默认状态
            self.root.after(3000, lambda: self.status_var.set("就绪 - 点击任意信息行复制到剪贴板"))

        except Exception as e:
            print(f"❌ 复制{field_name}失败: {e}")
            self.status_var.set(f"❌ 复制{field_name}失败: {str(e)}")
            self.root.after(3000, lambda: self.status_var.set("就绪 - 点击任意信息行复制到剪贴板"))

    def update_copy_tracker(self, field):
        """更新复制计数器并检查确认按钮状态"""
        try:
            if field == 'password':
                self.copy_tracker['password_copied'] = True
                print("[INFO] 密码已复制 ✓")
            elif field in ['email', 'username', 'name', 'first_name', 'last_name', 'verification_code']:
                self.copy_tracker['other_field_copied'] = True
                field_names = {
                    'email': '邮箱',
                    'username': '用户名',
                    'name': '完整姓名',
                    'first_name': '名字',
                    'last_name': '姓氏',
                    'verification_code': '验证码'
                }
                print(f"[INFO] {field_names.get(field, field)}已复制 ✓")

            # 检查是否满足启用条件：密码 + 任意其他字段
            password_copied = self.copy_tracker['password_copied']
            other_field_copied = self.copy_tracker['other_field_copied']

            if password_copied and other_field_copied:
                self.confirm_btn.config(state='normal')
                self.custom_btn.config(state='normal')  # 同时启用自定义按钮
                print("[INFO] ✅ 确认注册成功按钮已启用")
                print("[INFO] ✅ 自定义按钮已启用")
                self.status_var.set("✅ 可以点击确认注册成功了")
                self.root.after(3000, lambda: self.status_var.set("就绪 - 点击任意信息行复制到剪贴板"))

        except Exception as e:
            print(f"❌ 更新复制计数器失败: {e}")

    def reset_copy_tracker(self):
        """重置复制计数器"""
        self.copy_tracker = {
            'password_copied': False,
            'other_field_copied': False
        }
        if hasattr(self, 'confirm_btn'):
            self.confirm_btn.config(state='disabled')
        if hasattr(self, 'custom_btn'):
            self.custom_btn.config(state='disabled')
        print("[INFO] 复制计数器已重置，确认按钮和自定义按钮已禁用")

    def generate_initial_info(self):
        """初始化时生成注册信息"""
        try:
            print("🎲 初始化生成注册信息...")
            self.user_data = self.generate_registration_data()

            if self.user_data:
                # 分离姓名
                full_name = self.user_data.get('name', '')
                name_parts = full_name.split(' ')

                if len(name_parts) >= 2:
                    self.user_data['first_name'] = name_parts[0]
                    self.user_data['last_name'] = ' '.join(name_parts[1:])
                else:
                    self.user_data['first_name'] = full_name
                    self.user_data['last_name'] = 'Smith'

                self.reset_copy_tracker()
                self.update_info_display()
                self.status_var.set("✅ 注册信息已生成 - 点击密码和任意其他字段后可确认注册")
                print("✅ 初始注册信息生成成功")
            else:
                self.status_var.set("❌ 信息生成失败 - 请重试")
                print("❌ 初始注册信息生成失败")

        except Exception as e:
            print(f"❌ 生成初始注册信息失败: {e}")
            self.status_var.set("❌ 生成失败")

    def generate_new_info(self):
        """生成新的注册信息"""
        try:
            result = messagebox.askyesno("确认生成",
                                       "确定要生成新的注册信息吗？\n\n"
                                       "这将覆盖当前的注册信息。")

            if not result:
                return

            print("🎲 生成新的注册信息...")
            self.user_data = self.generate_registration_data()

            if self.user_data:
                # 分离姓名
                full_name = self.user_data.get('name', '')
                name_parts = full_name.split(' ')

                if len(name_parts) >= 2:
                    self.user_data['first_name'] = name_parts[0]
                    self.user_data['last_name'] = ' '.join(name_parts[1:])
                else:
                    self.user_data['first_name'] = full_name
                    self.user_data['last_name'] = 'Smith'

                self.reset_copy_tracker()
                self.update_info_display()
                self.status_var.set("✅ 新信息已生成 - 点击密码和任意其他字段后可确认注册")
                print("✅ 注册信息生成成功")
            else:
                self.status_var.set("❌ 信息生成失败 - 请重试")
                print("❌ 注册信息生成失败")

        except Exception as e:
            print(f"❌ 生成注册信息失败: {e}")
            self.status_var.set("❌ 生成失败")

    def update_info_display(self):
        """更新信息显示区域"""
        if not self.user_data:
            return

        self.email_content.config(text=f"📧 邮箱: {self.user_data.get('email', 'N/A')}")
        self.username_content.config(text=f"👤 用户名: {self.user_data.get('username', 'N/A')}")
        self.password_content.config(text=f"🔑 密码: {self.user_data.get('password', 'N/A')}")
        self.name_content.config(text=f"📛 完整姓名: {self.user_data.get('name', 'N/A')}")

        # 验证码显示
        verification_code = self.user_data.get('verification_code', '')
        if verification_code:
            self.verification_code_content.config(text=f"🔢 验证码: {verification_code}")
        else:
            self.verification_code_content.config(text="🔢 验证码: 未获取")

        self.first_name_content.config(text=f"👤 名字: {self.user_data.get('first_name', 'N/A')}")
        self.last_name_content.config(text=f"👥 姓氏: {self.user_data.get('last_name', 'N/A')}")

    def fetch_verification_codes(self):
        """获取验证码并显示在主界面"""
        try:
            print("📧 开始获取验证码...")
            self.status_var.set("🔄 正在获取验证码...")

            def fetch_codes_async():
                try:
                    # 先修复.env文件的BOM问题
                    self.fix_env_file_bom()

                    # 导入邮箱服务
                    import sys
                    from pathlib import Path

                    # 尝试导入email_service模块（支持打包环境）
                    try:
                        # 首先尝试直接导入（适用于打包环境）
                        from email_service import EmailService
                    except ImportError:
                        try:
                            # 如果直接导入失败，尝试从当前目录导入
                            sys.path.append(str(Path(__file__).parent))
                            from email_service import EmailService
                        except ImportError:
                            try:
                                # 最后尝试从工作目录导入
                                sys.path.append(os.getcwd())
                                from email_service import EmailService
                            except ImportError:
                                print("[ERROR] 无法导入email_service模块")
                                print("[INFO] 请确保email_service.py文件存在")
                                def show_error():
                                    self.status_var.set("❌ 邮件服务模块不存在")
                                self.root.after(0, show_error)
                                return

                    # 创建通用邮件服务（不限制发件人）
                    print(f"[INFO] 开始检查最新邮件中的验证码...")

                    email_service = EmailService(
                        sender_filter=None,  # 不限制发件人
                        subject_filter=None,  # 不限制主题
                        code_pattern=r'\b\d{4,8}\b'  # 通用验证码模式
                    )
                    email_service.max_wait_time = 15
                    verification_code = email_service.get_verification_code()

                    found_code = None
                    platform_found = None
                    platform_key_found = None

                    if verification_code:
                        found_code = verification_code

                        # 从发件人域名识别平台
                        if hasattr(email_service, 'last_sender') and email_service.last_sender:
                            sender = email_service.last_sender.lower()
                            print(f"[INFO] 分析发件人: {sender}")

                            # 平台域名映射
                            platform_mapping = {
                                'signin.aws': ('AWS', 'aws'),
                                'login.awsapps.com': ('AWS', 'aws'),
                                'github.com': ('GitHub', 'github'),
                                'tm.openai.com': ('OpenAI', 'openai'),
                                'openai.com': ('OpenAI', 'openai'),
                                'accounts.google.com': ('Google', 'google'),
                                'google.com': ('Google', 'google'),
                                'microsoft.com': ('Microsoft', 'microsoft'),
                                'apple.com': ('Apple', 'apple'),
                                'id.apple.com': ('Apple', 'apple'),
                                'icloud.com': ('Apple', 'apple'),
                                'discord.com': ('Discord', 'discord'),
                                'twitter.com': ('Twitter', 'twitter'),
                                'facebook.com': ('Facebook', 'facebook'),
                                'facebookmail.com': ('Facebook', 'facebook'),
                            }

                            # 查找匹配的平台
                            for domain, (name, key) in platform_mapping.items():
                                if domain in sender:
                                    platform_found = name
                                    platform_key_found = key
                                    print(f"[SUCCESS] 识别平台: {name} (域名: {domain})")
                                    break

                            # 如果没有匹配到，使用通用平台
                            if not platform_found:
                                # 尝试从邮箱地址提取域名
                                import re
                                email_match = re.search(r'@([a-zA-Z0-9.-]+)', sender)
                                if email_match:
                                    domain = email_match.group(1)
                                    platform_found = domain.split('.')[0].capitalize()
                                    platform_key_found = platform_found.lower()
                                    print(f"[INFO] 未知平台，使用域名: {platform_found}")
                                else:
                                    platform_found = 'Unknown'
                                    platform_key_found = 'unknown'

                        print(f"[SUCCESS] 找到验证码: {verification_code} (平台: {platform_found})")

                    def update_ui():
                        if found_code:
                            if not self.user_data:
                                self.user_data = {}
                            self.user_data['verification_code'] = found_code

                            # 保存检测到的平台信息
                            self.detected_platform = {
                                'name': platform_found,
                                'key': platform_key_found.lower()
                            }
                            print(f"[INFO] 检测到平台: {platform_found} ({platform_key_found})")

                            self.verification_code_content.config(text=f"🔢 验证码: {found_code}")
                            self.status_var.set(f"✅ 获取到 {platform_found} 验证码: {found_code}")

                            # 自动复制到剪贴板
                            self.copy_verification_code(found_code)
                            print(f"✅ 验证码已更新到主界面: {found_code}")
                        else:
                            self.status_var.set("❌ 未找到任何验证码")
                            print("❌ 未找到任何验证码")

                    self.root.after(0, update_ui)

                except Exception as e:
                    error_msg = str(e)
                    def show_error():
                        self.status_var.set(f"❌ 获取失败: {error_msg}")
                        print(f"❌ 获取验证码失败: {error_msg}")
                    self.root.after(0, show_error)

            # 启动异步线程
            thread = threading.Thread(target=fetch_codes_async, daemon=True)
            thread.start()

        except Exception as e:
            print(f"❌ 启动验证码获取失败: {e}")
            self.status_var.set(f"❌ 启动失败: {str(e)}")

    def copy_verification_code(self, code):
        """复制验证码到剪贴板"""
        try:
            if code and code != "未找到验证码" and code != "获取失败":
                pyperclip.copy(code)
                self.status_var.set(f"✅ 验证码已复制: {code}")
                print(f"✅ 验证码已复制到剪贴板: {code}")
            else:
                self.status_var.set("❌ 没有可复制的验证码")
        except Exception as e:
            print(f"❌ 复制验证码失败: {e}")
            self.status_var.set(f"❌ 复制失败: {str(e)}")

    def open_sms_website(self):
        """打开手机验证网站"""
        try:
            # 从.env文件读取SMS网站地址
            sms_website = self.get_sms_website_from_env()
            print(f"🌐 打开手机验证网站: {sms_website}")

            # 使用系统默认浏览器打开
            import webbrowser
            webbrowser.open(sms_website)

            self.status_var.set(f"✅ 已打开手机验证网站")
            messagebox.showinfo("提示",
                              f"手机验证网站已在默认浏览器中打开：\n\n{sms_website}\n\n"
                              f"您可以在该网站获取临时手机号码用于接收验证码。")

        except Exception as e:
            print(f"❌ 打开手机验证网站失败: {e}")
            messagebox.showerror("错误", f"打开网站失败: {e}")

    def get_sms_website_from_env(self):
        """从.env文件读取SMS网站地址配置"""
        try:
            # 获取可执行文件所在目录
            if getattr(sys, 'frozen', False):
                # 如果是打包后的exe
                exe_dir = Path(sys.executable).parent
            else:
                # 如果是Python脚本
                exe_dir = Path(__file__).parent

            # 尝试多个可能的.env文件路径（优先上级目录）
            possible_paths = [
                exe_dir.parent / ".env",  # 上级目录（优先）
                Path("C:/sandbox_files/.env"),
                exe_dir / ".env",  # 当前目录
                Path(".env")
            ]

            env_path = None
            for path in possible_paths:
                if path.exists():
                    env_path = path
                    break

            if not env_path:
                return "https://sms-activate.org/"

            with open(env_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if line.startswith('SMS_WEBSITE='):
                    sms_website = line.split('=', 1)[1].strip()
                    print(f"[INFO] 从.env文件读取SMS网站: {sms_website}")
                    return sms_website

            return "https://sms-activate.org/"

        except Exception as e:
            print(f"[ERROR] 读取.env文件失败: {e}")
            return "https://sms-activate.org/"

    def confirm_registration_success(self):
        """确认注册成功，保存账号信息"""
        try:
            if not self.user_data:
                messagebox.showwarning("警告", "没有可保存的注册信息，请先生成信息")
                return

            # 使用检测到的平台，如果没有则使用默认
            if self.detected_platform:
                platform_name = self.detected_platform['name']
                platform_key = self.detected_platform['key']
            else:
                platform_name = self.platform_info.get('name', 'GitHub')
                platform_key = self.platform_info.get('key', 'github')

            # 创建自定义对话框
            self.show_platform_dialog(platform_name, platform_key)

        except Exception as e:
            print(f"❌ 确认注册成功失败: {e}")
            messagebox.showerror("错误", f"操作失败: {e}")

    def show_custom_dialog(self):
        """显示自定义邮箱和密码对话框"""
        try:
            if not self.user_data:
                messagebox.showwarning("警告", "没有可自定义的注册信息，请先生成信息")
                return

            # 创建对话框窗口
            dialog = tk.Toplevel(self.root)
            dialog.title("自定义注册信息")
            dialog.geometry("450x250")
            dialog.resizable(False, False)
            dialog.transient(self.root)
            dialog.grab_set()

            # 主框架
            main_frame = ttk.Frame(dialog, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)

            # 标题
            title_label = ttk.Label(main_frame, text="✏️ 自定义邮箱和密码",
                                   font=('Arial', 14, 'bold'))
            title_label.pack(pady=(0, 15))

            # 邮箱输入框
            email_frame = ttk.Frame(main_frame)
            email_frame.pack(pady=10, fill=tk.X)

            email_label = ttk.Label(email_frame, text="邮箱:",
                                   font=('Arial', 10), width=8)
            email_label.pack(side=tk.LEFT, padx=(0, 10))

            email_var = tk.StringVar(value=self.user_data.get('email', ''))
            email_entry = ttk.Entry(email_frame, textvariable=email_var,
                                   font=('Arial', 10))
            email_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # 密码输入框
            password_frame = ttk.Frame(main_frame)
            password_frame.pack(pady=10, fill=tk.X)

            password_label = ttk.Label(password_frame, text="密码:",
                                      font=('Arial', 10), width=8)
            password_label.pack(side=tk.LEFT, padx=(0, 10))

            password_var = tk.StringVar(value=self.user_data.get('password', ''))
            password_entry = ttk.Entry(password_frame, textvariable=password_var,
                                      font=('Arial', 10))
            password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # 提示信息
            hint_label = ttk.Label(main_frame,
                                  text="(修改后将覆盖原有的邮箱和密码)",
                                  font=('Arial', 8), foreground='gray')
            hint_label.pack(pady=(0, 15))

            # 按钮框架
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(pady=10)

            def on_confirm():
                new_email = email_var.get().strip()
                new_password = password_var.get().strip()

                if not new_email:
                    messagebox.showwarning("警告", "邮箱不能为空", parent=dialog)
                    return

                if not new_password:
                    messagebox.showwarning("警告", "密码不能为空", parent=dialog)
                    return

                # 更新用户数据
                self.user_data['email'] = new_email
                self.user_data['password'] = new_password

                # 更新界面显示
                self.update_info_display()

                dialog.destroy()

                self.status_var.set("✅ 邮箱和密码已自定义")
                print(f"[INFO] 邮箱已自定义为: {new_email}")
                print(f"[INFO] 密码已自定义为: {new_password}")

                messagebox.showinfo("成功", "邮箱和密码已成功自定义！", parent=self.root)

            def on_cancel():
                dialog.destroy()

            confirm_btn = ttk.Button(button_frame, text="确认",
                                    command=on_confirm, width=12)
            confirm_btn.pack(side=tk.LEFT, padx=5)

            cancel_btn = ttk.Button(button_frame, text="取消",
                                   command=on_cancel, width=12)
            cancel_btn.pack(side=tk.LEFT, padx=5)

            # 居中显示
            dialog.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
            y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
            dialog.geometry(f"+{x}+{y}")

        except Exception as e:
            print(f"❌ 显示自定义对话框失败: {e}")
            messagebox.showerror("错误", f"显示对话框失败: {e}")

    def show_platform_dialog(self, default_platform_name, default_platform_key):
        """显示平台确认对话框"""
        try:
            # 创建对话框窗口
            dialog = tk.Toplevel(self.root)
            dialog.title("确认注册信息")
            dialog.geometry("400x250")
            dialog.resizable(False, False)
            dialog.transient(self.root)
            dialog.grab_set()

            # 主框架
            main_frame = ttk.Frame(dialog, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)

            # 标题
            title_label = ttk.Label(main_frame, text="✅ 确认注册成功",
                                   font=('Arial', 14, 'bold'))
            title_label.pack(pady=(0, 15))

            # 邮箱信息
            email_label = ttk.Label(main_frame,
                                   text=f"邮箱: {self.user_data.get('email', 'N/A')}",
                                   font=('Arial', 10))
            email_label.pack(pady=5)

            # 平台输入框
            platform_frame = ttk.Frame(main_frame)
            platform_frame.pack(pady=10, fill=tk.X)

            platform_label = ttk.Label(platform_frame, text="平台:",
                                      font=('Arial', 10))
            platform_label.pack(side=tk.LEFT, padx=(0, 10))

            platform_var = tk.StringVar(value=default_platform_name)
            platform_entry = ttk.Entry(platform_frame, textvariable=platform_var,
                                      font=('Arial', 10), width=20)
            platform_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # 提示信息
            hint_label = ttk.Label(main_frame,
                                  text="(可修改平台名称)",
                                  font=('Arial', 8), foreground='gray')
            hint_label.pack(pady=(0, 15))

            # 按钮框架
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(pady=10)

            def on_confirm():
                platform_name = platform_var.get().strip()
                if not platform_name:
                    messagebox.showwarning("警告", "平台名称不能为空", parent=dialog)
                    return

                # 更新平台信息
                self.platform_info = {
                    'name': platform_name,
                    'key': platform_name.lower()
                }

                dialog.destroy()

                # 保存注册数据
                success = self.save_registration_data()
                if success:
                    self.status_var.set("✅ 注册信息已保存")
                    messagebox.showinfo("成功", "注册信息已成功保存！")
                else:
                    self.status_var.set("❌ 保存失败")
                    messagebox.showerror("错误", "保存注册信息失败，请检查控制台输出")

            def on_cancel():
                dialog.destroy()

            confirm_btn = ttk.Button(button_frame, text="确认保存",
                                    command=on_confirm, width=12)
            confirm_btn.pack(side=tk.LEFT, padx=5)

            cancel_btn = ttk.Button(button_frame, text="取消",
                                   command=on_cancel, width=12)
            cancel_btn.pack(side=tk.LEFT, padx=5)

            # 居中显示
            dialog.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
            y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
            dialog.geometry(f"+{x}+{y}")

        except Exception as e:
            print(f"❌ 显示平台对话框失败: {e}")
            messagebox.showerror("错误", f"显示对话框失败: {e}")

    def save_registration_data(self):
        """保存注册数据到账号.txt和复制OAuth文件"""
        try:
            # 保存账号信息（必须成功）
            success1 = self.save_account_to_file()
            if not success1:
                print("❌ 保存账号信息失败")
                return False

            # 复制OAuth文件（可选，失败不影响整体结果）
            success2 = self.copy_oauth_files()
            if not success2:
                print("⚠️ OAuth文件复制失败，但账号信息已保存")

            # 只要账号信息保存成功就返回True
            return True
        except Exception as e:
            print(f"❌ 保存注册数据失败: {e}")
            return False

    def save_account_to_file(self):
        """保存账号信息到账号.txt文件"""
        try:
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            email = self.user_data.get('email', '')
            password = self.user_data.get('password', '')
            platform = self.platform_info.get('key', 'github')

            # 格式：邮箱\t\t密码\t平台\t时间
            account_line = f"{email}\t\t{password}\t{platform}\t{current_datetime}\n"

            # 尝试多个可能的保存路径，优先使用工作目录
            possible_paths = [
                Path("C:/sandbox_files/账号.txt"),  # 优先使用固定路径
                Path(os.getcwd()) / "账号.txt",     # 当前工作目录
                Path(__file__).parent / "账号.txt", # 程序所在目录（打包时可能是临时目录）
                Path("账号.txt")                    # 相对路径
            ]

            # 选择第一个可写的路径
            account_file = None
            for path in possible_paths:
                try:
                    # 确保目录存在
                    path.parent.mkdir(parents=True, exist_ok=True)
                    # 测试是否可写
                    with open(path, 'a', encoding='utf-8') as test_f:
                        pass
                    account_file = path
                    break
                except (PermissionError, OSError):
                    continue

            if account_file is None:
                account_file = possible_paths[0]  # 如果都不行，使用第一个作为fallback

            # 确保文件以换行符结尾，避免内容连在一起
            with open(account_file, 'a', encoding='utf-8') as f:
                # 如果文件不为空且最后一个字符不是换行符，先添加换行符
                if account_file.exists() and account_file.stat().st_size > 0:
                    with open(account_file, 'rb') as check_f:
                        check_f.seek(-1, 2)  # 移动到文件末尾前一个字节
                        last_char = check_f.read(1)
                        if last_char != b'\n':
                            f.write('\n')
                f.write(account_line)

            print(f"✅ 账号信息已保存到: {account_file}")
            print(f"📧 邮箱: {email}")
            print(f"🌐 平台: {platform}")
            print(f"⏰ 注册时间: {current_datetime}")
            return True

        except Exception as e:
            print(f"❌ 保存账号信息到文件失败: {e}")
            return False

    def copy_oauth_files(self):
        """复制OAuth文件"""
        try:
            print("📁 开始复制OAuth文件...")

            user_home = os.path.expanduser("~")
            aws_sso_cache_dir = os.path.join(user_home, ".aws", "sso", "cache")

            # 尝试多个可能的目标目录，优先使用工作目录
            possible_target_dirs = [
                "C:/sandbox_files/OAuth",                    # 优先使用固定路径
                os.path.join(os.getcwd(), "OAuth"),          # 当前工作目录
                os.path.join(os.path.dirname(__file__), "OAuth"), # 程序所在目录
                "OAuth"                                      # 相对路径
            ]

            # 选择第一个可写的目录
            target_dir = None
            for dir_path in possible_target_dirs:
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    # 测试是否可写
                    test_file = os.path.join(dir_path, "test_write.tmp")
                    with open(test_file, 'w') as test_f:
                        test_f.write("test")
                    os.remove(test_file)
                    target_dir = dir_path
                    break
                except (PermissionError, OSError):
                    continue

            if target_dir is None:
                target_dir = possible_target_dirs[0]  # 如果都不行，使用第一个作为fallback
                os.makedirs(target_dir, exist_ok=True)

            print(f"📂 源目录: {aws_sso_cache_dir}")
            print(f"📂 目标目录: {target_dir}")

            if not os.path.exists(aws_sso_cache_dir):
                print(f"⚠️ AWS SSO缓存目录不存在: {aws_sso_cache_dir}")
                return True

            json_files = glob.glob(os.path.join(aws_sso_cache_dir, "*.json"))
            print(f"📄 找到 {len(json_files)} 个JSON文件")

            if not json_files:
                print("⚠️ 没有找到OAuth JSON文件")
                return True

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            email = self.user_data.get('email', 'unknown@example.com')
            account_type = self.platform_info.get('key', 'github')

            print(f"📧 邮箱: {email}")
            print(f"🌐 账号类型: {account_type}")
            print(f"⏰ 时间戳: {timestamp}")

            copied_count = 0
            for json_file in json_files:
                try:
                    original_filename = os.path.basename(json_file)
                    file_base = os.path.splitext(original_filename)[0]

                    new_filename = f"{file_base}__{email}__{account_type}__{timestamp}.json"
                    target_path = os.path.join(target_dir, new_filename)

                    shutil.copy2(json_file, target_path)
                    print(f"✅ 已复制: {original_filename} -> {new_filename}")
                    copied_count += 1

                except Exception as e:
                    print(f"❌ 复制文件失败 {json_file}: {e}")

            if copied_count > 0:
                print(f"🎉 OAuth文件复制完成，共复制 {copied_count} 个文件")

            return True

        except Exception as e:
            print(f"❌ 复制OAuth文件失败: {e}")
            return False

    def view_recent_emails(self):
        """查看最近的邮件内容"""
        try:
            print("👁️ 开始查看最近的邮件...")
            self.status_var.set("🔄 正在获取邮件...")

            def fetch_emails_async():
                try:
                    # 先修复.env文件的BOM问题
                    self.fix_env_file_bom()

                    # 导入邮箱服务
                    import sys
                    from pathlib import Path

                    try:
                        from email_service import EmailService
                    except ImportError:
                        try:
                            sys.path.append(str(Path(__file__).parent))
                            from email_service import EmailService
                        except ImportError:
                            try:
                                sys.path.append(os.getcwd())
                                from email_service import EmailService
                            except ImportError:
                                def show_error():
                                    self.status_var.set("❌ 邮件服务模块不存在")
                                    messagebox.showerror("错误", "无法导入邮件服务模块")
                                self.root.after(0, show_error)
                                return

                    # 创建邮件服务实例
                    email_service = EmailService(
                        sender_filter=None,
                        subject_filter=None,
                        code_pattern=r'\b\d{4,8}\b'
                    )

                    # 连接邮箱
                    if not email_service.connect():
                        def show_error():
                            self.status_var.set("❌ 邮箱连接失败")
                            messagebox.showerror("错误", "无法连接到邮箱服务器")
                        self.root.after(0, show_error)
                        return

                    try:
                        # 搜索所有邮件
                        status, messages = email_service.imap_conn.search(None, 'ALL')

                        if status != 'OK' or not messages[0]:
                            def show_error():
                                self.status_var.set("❌ 未找到邮件")
                                messagebox.showinfo("提示", "收件箱中没有邮件")
                            self.root.after(0, show_error)
                            return

                        email_ids = messages[0].split()
                        latest_email_ids = list(reversed(email_ids))[:5]

                        emails_data = []

                        # 获取最新的5封邮件
                        for email_id in latest_email_ids:
                            try:
                                status, msg_data = email_service.imap_conn.fetch(email_id, '(RFC822)')

                                if status == 'OK':
                                    import email
                                    email_body = msg_data[0][1]
                                    msg = email.message_from_bytes(email_body)

                                    # 获取邮件信息
                                    sender = email_service._decode_header_value(msg.get('From', ''))
                                    subject = email_service._decode_header_value(msg.get('Subject', ''))
                                    date = msg.get('Date', '')

                                    # 获取邮件内容
                                    content = email_service._get_email_content(msg)

                                    # 清理HTML和CSS，获取纯文本
                                    import re

                                    # 移除<style>标签及其内容
                                    text_content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)

                                    # 移除<script>标签及其内容
                                    text_content = re.sub(r'<script[^>]*>.*?</script>', '', text_content, flags=re.DOTALL | re.IGNORECASE)

                                    # 移除HTML注释
                                    text_content = re.sub(r'<!--.*?-->', '', text_content, flags=re.DOTALL)

                                    # 移除所有HTML标签
                                    text_content = re.sub(r'<[^>]+>', ' ', text_content)

                                    # 移除CSS样式代码（独立的CSS规则）
                                    text_content = re.sub(r'\{[^}]*\}', '', text_content)

                                    # 移除多余的空白字符
                                    text_content = re.sub(r'\s+', ' ', text_content).strip()

                                    # 移除URL（可选，保留可能有用的链接）
                                    # text_content = re.sub(r'https?://[^\s]+', '[链接]', text_content)

                                    # 限制长度
                                    if len(text_content) > 2000:
                                        text_content = text_content[:2000] + "...\n\n[内容过长，已截断]"

                                    emails_data.append({
                                        'sender': sender,
                                        'subject': subject,
                                        'date': date,
                                        'content': text_content
                                    })

                            except Exception as e:
                                print(f"[WARNING] 处理邮件失败: {e}")
                                continue

                        email_service.disconnect()

                        # 显示邮件窗口
                        def show_emails():
                            self.show_emails_window(emails_data)
                            self.status_var.set("✅ 邮件已加载")

                        self.root.after(0, show_emails)

                    except Exception as e:
                        email_service.disconnect()
                        def show_error():
                            self.status_var.set(f"❌ 获取失败: {str(e)}")
                            messagebox.showerror("错误", f"获取邮件失败: {e}")
                        self.root.after(0, show_error)

                except Exception as e:
                    def show_error():
                        self.status_var.set(f"❌ 获取失败: {str(e)}")
                        messagebox.showerror("错误", f"操作失败: {e}")
                    self.root.after(0, show_error)

            # 启动异步线程
            thread = threading.Thread(target=fetch_emails_async, daemon=True)
            thread.start()

        except Exception as e:
            print(f"❌ 启动邮件查看失败: {e}")
            self.status_var.set(f"❌ 启动失败: {str(e)}")

    def show_emails_window(self, emails_data):
        """显示邮件内容窗口"""
        try:
            # 创建新窗口
            email_window = tk.Toplevel(self.root)
            email_window.title("最近的邮件内容")
            email_window.geometry("800x600")

            # 主框架
            main_frame = ttk.Frame(email_window, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)

            # 标题
            title_label = ttk.Label(main_frame, text="📧 最近的5封邮件",
                                   font=('Arial', 14, 'bold'))
            title_label.pack(pady=(0, 10))

            # 创建滚动文本框
            text_frame = ttk.Frame(main_frame)
            text_frame.pack(fill=tk.BOTH, expand=True)

            scrollbar = ttk.Scrollbar(text_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            text_widget = scrolledtext.ScrolledText(
                text_frame,
                wrap=tk.WORD,
                font=('Consolas', 10),
                yscrollcommand=scrollbar.set
            )
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=text_widget.yview)

            # 填充邮件内容
            for i, email_data in enumerate(emails_data, 1):
                text_widget.insert(tk.END, f"{'='*80}\n", 'separator')
                text_widget.insert(tk.END, f"邮件 #{i}\n", 'header')
                text_widget.insert(tk.END, f"{'='*80}\n", 'separator')
                text_widget.insert(tk.END, f"发件人: {email_data['sender']}\n", 'info')
                text_widget.insert(tk.END, f"主题: {email_data['subject']}\n", 'info')
                text_widget.insert(tk.END, f"时间: {email_data['date']}\n", 'info')
                text_widget.insert(tk.END, f"{'-'*80}\n", 'separator')
                text_widget.insert(tk.END, f"内容:\n", 'content_label')
                text_widget.insert(tk.END, f"{email_data['content']}\n\n", 'content')

            # 配置标签样式
            text_widget.tag_config('separator', foreground='gray')
            text_widget.tag_config('header', font=('Arial', 12, 'bold'), foreground='blue')
            text_widget.tag_config('info', foreground='darkgreen')
            text_widget.tag_config('content_label', font=('Arial', 10, 'bold'))
            text_widget.tag_config('content', foreground='black')

            # 禁止编辑
            text_widget.config(state=tk.DISABLED)

            # 关闭按钮
            close_btn = ttk.Button(main_frame, text="关闭", command=email_window.destroy, width=20)
            close_btn.pack(pady=(10, 0))

            print("✅ 邮件窗口已显示")

        except Exception as e:
            print(f"❌ 显示邮件窗口失败: {e}")
            messagebox.showerror("错误", f"显示邮件失败: {e}")

    def fix_env_file_bom(self):
        """修复.env文件的BOM字符问题"""
        try:
            # 获取可执行文件所在目录
            if getattr(sys, 'frozen', False):
                # 如果是打包后的exe
                exe_dir = Path(sys.executable).parent
            else:
                # 如果是Python脚本
                exe_dir = Path(__file__).parent

            # 尝试多个可能的.env文件路径（优先上级目录）
            possible_paths = [
                exe_dir.parent / '.env',  # 上级目录（优先）
                Path("C:/sandbox_files/.env"),
                exe_dir / '.env',  # 当前目录
                Path('.env')
            ]

            env_path = None
            for path in possible_paths:
                if path.exists():
                    env_path = path
                    break

            if not env_path:
                return

            # 读取文件内容，处理BOM
            with open(env_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()

            # 重新写入文件，不带BOM
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(content)

            print("✅ .env文件BOM字符已修复")

        except Exception as e:
            print(f"⚠️ 修复.env文件BOM失败: {e}")

    def run(self):
        """运行应用程序"""
        try:
            if self.create_gui():
                print("🎛️ 注册信息生成器已启动")
                self.root.mainloop()
            else:
                print("❌ GUI启动失败")
        except Exception as e:
            print(f"❌ 应用程序运行失败: {e}")


def main():
    """主函数"""
    try:
        print("🎯 注册信息生成器 v1.0")
        print("=" * 50)
        print("功能：")
        print("  - 生成随机注册信息（邮箱、用户名、密码、姓名）")
        print("  - 接收邮件验证码（支持多平台）")
        print("  - 管理账号信息（保存到账号.txt）")
        print("  - 复制OAuth文件")
        print("=" * 50)

        # 创建应用程序实例
        app = RegistrationInfoGenerator()

        # 运行应用程序
        app.run()

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()