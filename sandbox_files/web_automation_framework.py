#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用Web自动化框架
功能：基于渐进式混合识别的通用自动化类库
作者：simtel@qq.com
设计理念：
- 渐进式混合识别（URL优先，智能降级）
- 回调函数 + 原子操作对象
- 可中断的执行引擎
- 配置驱动的工作流程
"""

import time
import random
import re
import json
import threading
import platform
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable, Union
from enum import Enum
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, TimeoutException

# GUI控制面板相关导入
try:
    import tkinter as tk
    from tkinter import ttk
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("⚠️ Tkinter不可用，控制面板功能将被禁用")


# ==================== 可视化控制面板系统 ====================

class AutomationControlPanel:
    """自动化控制面板 - 实时控制界面"""

    def __init__(self, framework_instance, position="top_right"):
        self.framework = framework_instance
        self.position = position

        # 控制状态（线程安全）
        self.is_paused = threading.Event()
        self.is_exited = threading.Event()
        self.should_exit_page = threading.Event()

        # 初始状态：未暂停（Event处于set状态表示可以继续执行）
        self.is_paused.set()

        # GUI组件
        self.root = None
        self.pause_button = None
        self.exit_button = None
        self.status_label = None

        # 线程管理
        self.gui_thread = None
        self.is_running = False

        # 检查GUI可用性
        if not GUI_AVAILABLE:
            print("❌ GUI不可用，控制面板无法启动")
            return

    def start_panel(self):
        """启动控制面板（独立线程）"""
        if not GUI_AVAILABLE:
            print("❌ GUI不可用，跳过控制面板启动")
            return

        self.is_running = True
        self.gui_thread = threading.Thread(target=self._create_gui, daemon=True)
        self.gui_thread.start()
        print("🎛️ 控制面板线程已启动")

    def stop_panel(self):
        """停止控制面板"""
        self.is_running = False
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except:
                pass

    def _create_gui(self):
        """创建GUI界面"""
        try:
            self.root = tk.Tk()
            self.root.title("自动化控制")
            self.root.geometry("180x140")  # 适合2个按钮和状态标签的高度
            self.root.attributes("-topmost", True)  # 置顶显示
            self.root.resizable(False, False)  # 禁止调整大小

            # 设置为无边框窗口（移除最小化、最大化、关闭按钮）
            self.root.overrideredirect(True)

            # 设置位置到右上角
            self._set_window_position()

            # 创建按钮
            self._create_buttons()

            # 设置关闭事件
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

            print("🎛️ 控制面板GUI已创建")

            # 启动GUI主循环
            self.root.mainloop()

        except Exception as e:
            print(f"❌ 控制面板GUI创建失败: {e}")

    def _set_window_position(self):
        """设置窗口位置到屏幕右上角"""
        try:
            # 更新窗口以获取准确的屏幕尺寸
            self.root.update_idletasks()

            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()

            # 计算右上角位置（调整为新的窗口尺寸）
            x = screen_width - 200  # 距离右边20px
            y = 20  # 距离顶部20px

            self.root.geometry(f"180x140+{x}+{y}")
            print(f"🎛️ 控制面板位置: ({x}, {y})")

        except Exception as e:
            print(f"⚠️ 设置窗口位置失败: {e}")

    def _create_buttons(self):
        """创建控制按钮"""
        try:
            # 创建主框架
            main_frame = tk.Frame(self.root, padx=10, pady=10)
            main_frame.pack(fill=tk.BOTH, expand=True)

            # 暂停/继续按钮（初始状态：运行中，显示"暂停"，绿色活跃）
            self.pause_button = tk.Button(
                main_frame,
                text="暂停",
                command=self._toggle_pause,
                width=12,
                height=1,
                bg="#4CAF50",  # 绿色表示活跃运行状态
                fg="white",
                font=("Arial", 9, "bold")
            )
            self.pause_button.pack(pady=2)

            # 退出当前页按钮
            self.exit_button = tk.Button(
                main_frame,
                text="退出当前页",
                command=self._exit_current_page,
                width=12,
                height=1,
                bg="#FF6B6B",
                fg="white",
                font=("Arial", 9, "bold")
            )
            self.exit_button.pack(pady=2)

            # 状态显示
            self.status_label = tk.Label(
                main_frame,
                text="运行中",
                fg="#4CAF50",
                font=("Arial", 9, "bold")
            )
            self.status_label.pack(pady=2)

            print("🎛️ 控制按钮已创建")

        except Exception as e:
            print(f"❌ 创建控制按钮失败: {e}")

    def _toggle_pause(self):
        """切换暂停/继续状态"""
        try:
            if self.is_paused.is_set():
                # 当前是运行状态，切换为暂停
                self.is_paused.clear()  # 清除事件，使wait()阻塞
                self.pause_button.config(text="继续", bg="#808080")  # 灰色表示不活跃
                self.status_label.config(text="已暂停", fg="#FFA500")
                print("=" * 50)
                print("⏸️ [控制面板] 自动化已暂停，等待用户恢复...")
                print("=" * 50)
            else:
                # 当前是暂停状态，切换为继续
                self.is_paused.set()  # 设置事件，使wait()返回
                self.pause_button.config(text="暂停", bg="#4CAF50")  # 绿色表示活跃运行
                self.status_label.config(text="运行中", fg="#4CAF50")
                print("=" * 50)
                print("🟢 [控制面板] 自动化已恢复")
                print("=" * 50)

        except Exception as e:
            print(f"❌ 切换暂停状态失败: {e}")

    def _exit_current_page(self):
        """退出当前页面"""
        try:
            self.should_exit_page.set()
            # 按钮变为不可用状态（灰色）
            self.exit_button.config(state="disabled", bg="#808080")
            self.status_label.config(text="等待页面变化", fg="#FF6B6B")
            print("=" * 50)
            print("🔴 [控制面板] 退出当前页面，等待页面变化...")
            print("=" * 50)

        except Exception as e:
            print(f"❌ 退出当前页面失败: {e}")

    def _on_closing(self):
        """窗口关闭事件处理"""
        print("🎛️ 控制面板正在关闭...")
        self.is_running = False
        self.root.destroy()

    def reset_exit_page_status(self):
        """重置退出页面状态"""
        try:
            self.should_exit_page.clear()
            # 恢复退出按钮为可用状态
            if self.exit_button:
                self.exit_button.config(state="normal", bg="#FF6B6B")
            # 恢复状态标签
            if self.status_label and self.is_paused.is_set():
                self.status_label.config(text="运行中", fg="#4CAF50")
            print("=" * 50)
            print("✅ [控制面板] 页面变化检测完成，退出按钮已恢复")
            print("=" * 50)
        except Exception as e:
            print(f"⚠️ 重置退出状态失败: {e}")


# ==================== 智能异常处理系统 ====================

class ExceptionHandlingStrategy(Enum):
    """异常处理策略"""
    RETRY = "retry"              # 重试操作
    ADAPT = "adapt"              # 适应变化
    INTERRUPT = "interrupt"      # 中断操作
    FAIL = "fail"               # 操作失败

@dataclass
class ExceptionContext:
    """异常上下文信息"""
    exception: Exception
    action_type: str
    selector: str
    attempt_count: int
    max_attempts: int
    driver: webdriver.Chrome

class ExceptionHandler(ABC):
    """异常处理器接口 - 可插拔设计"""

    @abstractmethod
    def can_handle(self, exception: Exception) -> bool:
        """判断是否能处理该异常"""
        pass

    @abstractmethod
    def handle(self, context: ExceptionContext) -> ExceptionHandlingStrategy:
        """处理异常并返回策略"""
        pass

class StaleElementHandler(ExceptionHandler):
    """智能 Stale Element 处理器"""

    def __init__(self, max_retries: int = 3, page_change_threshold: float = 2.0):
        self.max_retries = max_retries
        self.page_change_threshold = page_change_threshold
        self.initial_url = None
        self.initial_title = None

    def can_handle(self, exception: Exception) -> bool:
        return isinstance(exception, StaleElementReferenceException)

    def handle(self, context: ExceptionContext) -> ExceptionHandlingStrategy:
        """智能处理 Stale Element 异常"""
        print(f"🔍 智能分析 Stale Element (尝试 {context.attempt_count}/{context.max_attempts})")

        # 记录初始状态
        if context.attempt_count == 1:
            self.initial_url = context.driver.current_url
            self.initial_title = context.driver.title

        # 检查页面是否真的发生了跳转
        page_changed = self._detect_page_change(context.driver)

        if page_changed:
            print("✅ 确认页面已跳转，建议适应新页面")
            return ExceptionHandlingStrategy.ADAPT
        elif context.attempt_count < context.max_attempts:
            print("🔄 页面未跳转，重新定位元素并重试")
            return ExceptionHandlingStrategy.RETRY
        else:
            print("❌ 重试次数已达上限，操作失败")
            return ExceptionHandlingStrategy.FAIL

    def _detect_page_change(self, driver: webdriver.Chrome) -> bool:
        """检测页面是否真的发生了变化"""
        try:
            current_url = driver.current_url
            current_title = driver.title

            # 方法1：URL 变化检测
            url_changed = (self.initial_url and current_url != self.initial_url)

            # 方法2：标题变化检测
            title_changed = (self.initial_title and current_title != self.initial_title)

            # 方法3：页面加载状态检测
            page_loading = driver.execute_script("return document.readyState") != "complete"

            if url_changed or title_changed:
                print(f"📄 检测到页面变化: URL={url_changed}, Title={title_changed}")
                return True

            if page_loading:
                print("⏳ 页面正在加载中")
                time.sleep(1.0)  # 等待页面稳定
                return False

            return False

        except Exception as e:
            print(f"⚠️ 页面变化检测异常: {e}")
            return True  # 保守策略：异常时认为页面已变化

class NoSuchElementHandler(ExceptionHandler):
    """元素未找到处理器"""

    def can_handle(self, exception: Exception) -> bool:
        return isinstance(exception, NoSuchElementException)

    def handle(self, context: ExceptionContext) -> ExceptionHandlingStrategy:
        print(f"🔍 元素未找到处理 (尝试 {context.attempt_count}/{context.max_attempts})")

        if context.attempt_count < context.max_attempts:
            print("🔄 等待元素出现并重试")
            time.sleep(1.0)
            return ExceptionHandlingStrategy.RETRY
        else:
            print("❌ 元素持续未找到，可能页面已跳转")
            return ExceptionHandlingStrategy.ADAPT

class TimeoutHandler(ExceptionHandler):
    """超时处理器"""

    def can_handle(self, exception: Exception) -> bool:
        return isinstance(exception, TimeoutException)

    def handle(self, context: ExceptionContext) -> ExceptionHandlingStrategy:
        print(f"⏰ 超时处理 (尝试 {context.attempt_count}/{context.max_attempts})")

        if context.attempt_count < context.max_attempts:
            print("🔄 延长等待时间并重试")
            return ExceptionHandlingStrategy.RETRY
        else:
            print("❌ 持续超时，可能页面结构已变化")
            return ExceptionHandlingStrategy.ADAPT

class ExceptionHandlerChain:
    """异常处理器链 - 责任链模式"""

    def __init__(self):
        self.handlers: List[ExceptionHandler] = [
            StaleElementHandler(),
            NoSuchElementHandler(),
            TimeoutHandler()
        ]

    def handle_exception(self, context: ExceptionContext) -> ExceptionHandlingStrategy:
        """处理异常"""
        for handler in self.handlers:
            if handler.can_handle(context.exception):
                return handler.handle(context)

        # 默认策略：未知异常直接失败
        print(f"❌ 未知异常类型: {type(context.exception).__name__}")
        return ExceptionHandlingStrategy.FAIL

    def add_handler(self, handler: ExceptionHandler):
        """添加自定义处理器"""
        self.handlers.insert(0, handler)  # 新处理器优先级更高

# ==================== 枚举和数据类 ====================

class ActionResult(Enum):
    """操作结果枚举"""
    SUCCESS = "success"
    FAILED = "failed"
    INTERRUPTED = "interrupted"
    TIMEOUT = "timeout"


class PageConfidence(Enum):
    """页面识别置信度"""
    HIGH = 0.9      # 高置信度（URL精确匹配）
    MEDIUM = 0.7    # 中等置信度（标题匹配）
    LOW = 0.5       # 低置信度（元素匹配）
    UNKNOWN = 0.0   # 未知页面


@dataclass
class PageCandidate:
    """页面候选结果"""
    page_id: str
    confidence: float
    match_method: str = "unknown"
    match_details: str = ""


@dataclass
class PageContext:
    """页面上下文信息"""
    current_url: str
    page_title: str
    page_id: str
    driver: webdriver.Chrome


# ==================== 增强的原子操作系统 ====================

class ResilientAction(ABC):
    """增强的原子操作基类 - 集成智能异常处理"""

    def __init__(self, action_type: str, description: str = "", max_retries: int = 3, **params):
        self.action_type = action_type
        self.description = description
        self.max_retries = max_retries
        self.params = params
        self.exception_handler = ExceptionHandlerChain()

    def execute(self, driver: webdriver.Chrome) -> ActionResult:
        """执行操作 - 集成智能异常处理"""
        for attempt in range(1, self.max_retries + 1):
            try:
                # 调用子类的具体实现
                return self._execute_impl(driver)

            except Exception as e:
                print(f"⚠️ 操作异常 (尝试 {attempt}/{self.max_retries}): {type(e).__name__}")

                # 构建异常上下文
                context = ExceptionContext(
                    exception=e,
                    action_type=self.action_type,
                    selector=getattr(self, 'selector', 'unknown'),
                    attempt_count=attempt,
                    max_attempts=self.max_retries,
                    driver=driver
                )

                # 获取处理策略
                strategy = self.exception_handler.handle_exception(context)

                if strategy == ExceptionHandlingStrategy.RETRY:
                    if attempt < self.max_retries:
                        print(f"🔄 执行重试策略，准备第 {attempt + 1} 次尝试")
                        time.sleep(0.5)  # 短暂等待
                        continue
                    else:
                        print("❌ 重试次数已达上限")
                        return ActionResult.FAILED

                elif strategy == ExceptionHandlingStrategy.ADAPT:
                    print("🔄 执行适应策略，返回中断信号")
                    return ActionResult.INTERRUPTED

                elif strategy == ExceptionHandlingStrategy.FAIL:
                    print("❌ 执行失败策略")
                    return ActionResult.FAILED

                else:  # INTERRUPT
                    print("🚨 执行中断策略")
                    return ActionResult.INTERRUPTED

        print(f"❌ 操作最终失败: {self.description}")
        return ActionResult.FAILED

    @abstractmethod
    def _execute_impl(self, driver: webdriver.Chrome) -> ActionResult:
        """具体的执行实现 - 由子类实现"""
        pass

    def add_exception_handler(self, handler: ExceptionHandler):
        """添加自定义异常处理器"""
        self.exception_handler.add_handler(handler)

    def __str__(self):
        return f"{self.action_type}: {self.description}"

class AtomicAction(ResilientAction):
    """原子操作基类 - 向后兼容"""

    def __init__(self, action_type: str, description: str = "", **params):
        super().__init__(action_type, description, **params)

    def execute(self, driver: webdriver.Chrome) -> ActionResult:
        """执行操作 - 使用增强的异常处理"""
        return super().execute(driver)

    @abstractmethod
    def _execute_impl(self, driver: webdriver.Chrome) -> ActionResult:
        """具体的执行实现 - 由子类实现"""
        pass


class InputAction(AtomicAction):
    """输入操作"""

    def __init__(self, selector: str, value: str, typing_style: str = "human",
                 clear_first: bool = True, description: str = ""):
        super().__init__("input", description or f"输入文本到 {selector}")
        self.selector = selector
        self.value = value
        self.typing_style = typing_style
        self.clear_first = clear_first
        # print(f"🚨 [DEBUG] InputAction INIT: selector='{self.selector}', value='{self.value}' (type={type(self.value)})")

    def _execute_impl(self, driver: webdriver.Chrome) -> ActionResult:
        """执行输入操作的具体实现"""
        # 等待元素可点击
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.selector)))

        # 滚动到元素位置
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)

        # 点击元素获取焦点
        element.click()
        time.sleep(random.uniform(0.3, 0.7))

        # 清空输入框
        if self.clear_first:
            element.clear()
            time.sleep(0.2)

        # 处理动态变量值
        actual_value = self.value
        # 处理花括号变量替换 (如 {firstName}, {lastName})
        if self.value.startswith('{') and self.value.endswith('}'):
            variable_name = self.value[1:-1]  # 去掉花括号
            print(f"🔍 检测到花括号变量: {self.value}, 变量名: {variable_name}")

            # 调试：检查动态变量获取器
            if hasattr(self, 'dynamic_variable_getter') and self.dynamic_variable_getter:
                actual_value = self.dynamic_variable_getter(variable_name)
                print(f"🔄 动态变量替换: {self.value} -> {actual_value}")
            else:
                print(f"❌ InputAction没有动态变量获取器，尝试从框架获取")
                # 尝试从框架获取动态变量
                actual_value = self._get_dynamic_value_from_framework(driver, variable_name)
        elif self.value == "dynamic_from_callback":
            # 兼容旧的动态变量方式
            actual_value = self._get_dynamic_value_from_context(driver)

        # 根据输入风格执行输入
        if self.typing_style == "human":
            self._human_like_typing(element, actual_value)
        else:
            element.send_keys(actual_value)

        print(f"✅ 输入操作完成: {self.selector} -> {actual_value}")
        return ActionResult.SUCCESS

    def _get_dynamic_value_from_context(self, driver) -> str:
        """从执行上下文获取动态变量值（兼容旧方式）"""
        # 这里需要从执行上下文中获取动态变量
        # 暂时返回占位符，实际应该从框架获取
        return "dynamic_value"

    def _get_dynamic_value_from_framework(self, driver, variable_name: str) -> str:
        """从框架获取动态变量值（低耦合设计）"""
        try:
            # 方法1：尝试从driver的执行上下文获取（松耦合）
            if hasattr(driver, '_framework_context'):
                context = driver._framework_context
                if hasattr(context, 'current_form_data') and variable_name in context.current_form_data:
                    value = context.current_form_data[variable_name]
                    print(f"🔄 从框架上下文获取变量: {variable_name} = {value}")
                    return value

            # 方法2：尝试从全局动态变量获取器获取
            if hasattr(self, 'dynamic_variable_getter') and self.dynamic_variable_getter:
                value = self.dynamic_variable_getter(variable_name)
                print(f"🔄 从动态获取器获取变量: {variable_name} = {value}")
                return value

            # 如果找不到，返回描述性占位符
            print(f"⚠️ 未找到动态变量: {variable_name}")
            return f"{{missing_{variable_name}}}"

        except Exception as e:
            print(f"❌ 获取动态变量失败: {variable_name}, 错误: {e}")
            return f"{{error_{variable_name}}}"

    def set_dynamic_variable_getter(self, getter_func):
        """设置动态变量获取器"""
        self.dynamic_variable_getter = getter_func

    def _human_like_typing(self, element, text: str):
        """模拟人类打字"""
        for char in text:
            element.send_keys(char)
            # 随机延迟，模拟人类打字速度
            delay = random.uniform(0.05, 0.15)
            time.sleep(delay)

        # 输入完成后稍作停顿
        time.sleep(random.uniform(0.2, 0.5))


class ClickAction(AtomicAction):
    """点击操作"""

    def __init__(self, selector: str, description: str = ""):
        super().__init__("click", description or f"点击 {selector}")
        self.selector = selector

    def _execute_impl(self, driver: webdriver.Chrome) -> ActionResult:
        """执行点击操作的具体实现"""
        # 等待元素可点击
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.selector)))

        # 滚动到元素位置
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(1)

        # 模拟人类点击前的短暂停顿
        time.sleep(random.uniform(0.5, 1.0))

        # 使用JavaScript点击确保成功
        driver.execute_script("arguments[0].click();", element)

        print(f"✅ 点击操作完成: {self.selector}")
        return ActionResult.SUCCESS


class DelayAction(AtomicAction):
    """延迟操作"""

    def __init__(self, duration: float, description: str = ""):
        super().__init__("delay", description or f"延迟 {duration} 秒")
        self.duration = duration

    def _execute_impl(self, driver: webdriver.Chrome) -> ActionResult:
        """执行延迟操作的具体实现（可中断）"""
        print(f"⏳ 开始延迟 {self.duration} 秒...")

        # 分段延迟，支持中断检查
        check_interval = 0.5
        elapsed = 0

        while elapsed < self.duration:
            sleep_time = min(check_interval, self.duration - elapsed)
            time.sleep(sleep_time)
            elapsed += sleep_time

        print(f"✅ 延迟操作完成")
        return ActionResult.SUCCESS


class SelectAction(AtomicAction):
    """下拉框选择操作"""

    def __init__(self, selector: str, value: str, method: str = "by_text", description: str = ""):
        super().__init__("select", description or f"选择下拉框 {selector}")
        self.selector = selector
        self.value = value
        self.method = method  # by_text, by_value, by_index

    def _execute_impl(self, driver: webdriver.Chrome) -> ActionResult:
        """执行下拉框选择操作的具体实现"""
        # 等待元素可点击
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.selector)))

        # 滚动到元素位置
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)

        # 创建Select对象
        select = Select(element)

        # 根据方法选择选项
        if self.method == "by_text":
            select.select_by_visible_text(self.value)
        elif self.method == "by_value":
            select.select_by_value(self.value)
        elif self.method == "by_index":
            select.select_by_index(int(self.value))
        else:
            print(f"❌ 不支持的选择方法: {self.method}")
            return ActionResult.FAILED

        print(f"✅ 下拉框选择完成: {self.selector} -> {self.value}")
        return ActionResult.SUCCESS


class CheckAction(AtomicAction):
    """单选框/复选框操作"""

    def __init__(self, selector: str, checked: bool = True, description: str = ""):
        super().__init__("check", description or f"设置复选框 {selector}")
        self.selector = selector
        self.checked = checked

    def _execute_impl(self, driver: webdriver.Chrome) -> ActionResult:
        """执行复选框操作的具体实现"""
        # 等待元素可点击
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.selector)))

        # 滚动到元素位置
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)

        # 检查当前状态
        current_state = element.is_selected()

        # 如果状态不匹配，则点击切换
        if current_state != self.checked:
            element.click()
            time.sleep(0.3)

        print(f"✅ 复选框操作完成: {self.selector} -> {'选中' if self.checked else '取消选中'}")
        return ActionResult.SUCCESS


class WaitForElementAction(AtomicAction):
    """等待元素状态操作"""

    def __init__(self, selector: str, condition: str = "visible", timeout: int = 30, description: str = ""):
        super().__init__("wait_for_element", description or f"等待元素 {selector}")
        self.selector = selector
        self.condition = condition  # visible, clickable, present, invisible
        self.timeout = timeout

    def _execute_impl(self, driver: webdriver.Chrome) -> ActionResult:
        """执行等待元素操作的具体实现"""
        wait = WebDriverWait(driver, self.timeout)

        if self.condition == "visible":
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, self.selector)))
        elif self.condition == "clickable":
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.selector)))
        elif self.condition == "present":
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.selector)))
        elif self.condition == "invisible":
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, self.selector)))
        else:
            print(f"❌ 不支持的等待条件: {self.condition}")
            return ActionResult.FAILED

        print(f"✅ 元素等待完成: {self.selector} ({self.condition})")
        return ActionResult.SUCCESS


class KeyPressAction(AtomicAction):
    """按键操作"""

    def __init__(self, keys: Union[str, List[str]], description: str = ""):
        super().__init__("key_press", description or f"按键 {keys}")
        self.keys = keys if isinstance(keys, list) else [keys]

    def _execute_impl(self, driver: webdriver.Chrome) -> ActionResult:
        """执行按键操作的具体实现"""
        # 获取当前活动元素
        active_element = driver.switch_to.active_element

        # 处理组合键
        if len(self.keys) > 1:
            # 组合键操作
            actions = ActionChains(driver)
            for key in self.keys[:-1]:
                actions = actions.key_down(getattr(Keys, key.upper(), key))

            # 按下最后一个键
            last_key = getattr(Keys, self.keys[-1].upper(), self.keys[-1])
            actions = actions.send_keys(last_key)

            # 释放所有修饰键
            for key in self.keys[:-1]:
                actions = actions.key_up(getattr(Keys, key.upper(), key))

            actions.perform()
        else:
            # 单个按键
            key = getattr(Keys, self.keys[0].upper(), self.keys[0])
            active_element.send_keys(key)

        print(f"✅ 按键操作完成: {'+'.join(self.keys)}")
        return ActionResult.SUCCESS


class ScrollAction(AtomicAction):
    """滚动操作"""

    def __init__(self, direction: str = "down", distance: int = 500, selector: str = None, description: str = ""):
        super().__init__("scroll", description or f"滚动 {direction}")
        self.direction = direction  # up, down, to_element
        self.distance = distance
        self.selector = selector

    def _execute_impl(self, driver: webdriver.Chrome) -> ActionResult:
        """执行滚动操作的具体实现"""
        if self.direction == "to_element" and self.selector:
            # 滚动到特定元素
            element = driver.find_element(By.CSS_SELECTOR, self.selector)
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
        elif self.direction == "down":
            # 向下滚动
            driver.execute_script(f"window.scrollBy(0, {self.distance});")
            time.sleep(0.5)
        elif self.direction == "up":
            # 向上滚动
            driver.execute_script(f"window.scrollBy(0, -{self.distance});")
            time.sleep(0.5)
        else:
            print(f"❌ 不支持的滚动方向: {self.direction}")
            return ActionResult.FAILED

        print(f"✅ 滚动操作完成: {self.direction}")
        return ActionResult.SUCCESS


class HoverAction(AtomicAction):
    """鼠标悬停操作"""

    def __init__(self, selector: str, description: str = ""):
        super().__init__("hover", description or f"悬停 {selector}")
        self.selector = selector

    def _execute_impl(self, driver: webdriver.Chrome) -> ActionResult:
        """执行鼠标悬停操作的具体实现"""
        # 等待元素可见
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, self.selector)))

        # 滚动到元素位置
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)

        # 执行悬停操作
        actions = ActionChains(driver)
        actions.move_to_element(element).perform()
        time.sleep(0.5)

        print(f"✅ 鼠标悬停完成: {self.selector}")
        return ActionResult.SUCCESS


class SwitchWindowAction(AtomicAction):
    """切换窗口/标签页操作"""

    def __init__(self, window_index: int = None, window_handle: str = None, description: str = ""):
        super().__init__("switch_window", description or "切换窗口")
        self.window_index = window_index
        self.window_handle = window_handle

    def _execute_impl(self, driver: webdriver.Chrome) -> ActionResult:
        """执行窗口切换操作的具体实现"""
        if self.window_handle:
            # 使用窗口句柄切换
            driver.switch_to.window(self.window_handle)
        elif self.window_index is not None:
            # 使用窗口索引切换
            handles = driver.window_handles
            if 0 <= self.window_index < len(handles):
                driver.switch_to.window(handles[self.window_index])
            else:
                print(f"❌ 窗口索引超出范围: {self.window_index}")
                return ActionResult.FAILED
        else:
            print("❌ 未指定窗口句柄或索引")
            return ActionResult.FAILED

        time.sleep(0.5)
        print(f"✅ 窗口切换完成")
        return ActionResult.SUCCESS


class UploadFileAction(AtomicAction):
    """文件上传操作"""

    def __init__(self, selector: str, file_path: str, description: str = ""):
        super().__init__("upload_file", description or f"上传文件到 {selector}")
        self.selector = selector
        self.file_path = file_path

    def _execute_impl(self, driver: webdriver.Chrome) -> ActionResult:
        """执行文件上传操作的具体实现"""
        # 等待文件输入元素
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.selector)))

        # 检查文件是否存在
        import os
        if not os.path.exists(self.file_path):
            print(f"❌ 文件不存在: {self.file_path}")
            return ActionResult.FAILED

        # 上传文件
        element.send_keys(self.file_path)
        time.sleep(1.0)

        print(f"✅ 文件上传完成: {self.file_path}")
        return ActionResult.SUCCESS


class ExtractTextAction(AtomicAction):
    """提取文本操作"""

    def __init__(self, selector: str, variable: str, attribute: str = None, description: str = ""):
        super().__init__("extract_text", description or f"提取文本 {selector}")
        self.selector = selector
        self.variable = variable
        self.attribute = attribute  # 如果为None则提取文本内容，否则提取属性值

    def _execute_impl(self, driver: webdriver.Chrome) -> ActionResult:
        """执行文本提取操作的具体实现"""
        # 等待元素存在
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.selector)))

        # 提取文本或属性
        if self.attribute:
            extracted_value = element.get_attribute(self.attribute)
        else:
            extracted_value = element.text

        # 存储到变量（这里需要一个变量存储机制，暂时打印）
        print(f"📝 提取的值: {self.variable} = {extracted_value}")

        # TODO: 实现变量存储机制
        # self._store_variable(self.variable, extracted_value)

        print(f"✅ 文本提取完成: {self.selector}")
        return ActionResult.SUCCESS


class VerifyElementAction(AtomicAction):
    """元素验证操作"""

    def __init__(self, selector: str, expected_text: str = None, expected_attribute: Dict[str, str] = None,
                 fail_action: str = "abort", description: str = ""):
        super().__init__("verify_element", description or f"验证元素 {selector}")
        self.selector = selector
        self.expected_text = expected_text
        self.expected_attribute = expected_attribute or {}
        self.fail_action = fail_action  # abort, retry, skip

    def _execute_impl(self, driver: webdriver.Chrome) -> ActionResult:
        """执行元素验证操作的具体实现"""
        # 等待元素存在
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.selector)))

        # 验证文本内容
        if self.expected_text:
            actual_text = element.text
            if self.expected_text not in actual_text:
                print(f"❌ 文本验证失败: 期望包含 '{self.expected_text}', 实际 '{actual_text}'")
                return self._handle_verification_failure()

        # 验证属性值
        for attr_name, expected_value in self.expected_attribute.items():
            actual_value = element.get_attribute(attr_name)
            if actual_value != expected_value:
                print(f"❌ 属性验证失败: {attr_name} 期望 '{expected_value}', 实际 '{actual_value}'")
                return self._handle_verification_failure()

        print(f"✅ 元素验证成功: {self.selector}")
        return ActionResult.SUCCESS

    def _handle_verification_failure(self) -> ActionResult:
        """处理验证失败"""
        if self.fail_action == "abort":
            return ActionResult.FAILED
        elif self.fail_action == "retry":
            return ActionResult.FAILED  # 让上层重试
        elif self.fail_action == "skip":
            print("⚠️ 验证失败但跳过继续执行")
            return ActionResult.SUCCESS
        else:
            return ActionResult.FAILED


class CallbackAction(AtomicAction):
    """回调操作 - 在序列中执行回调函数"""

    def __init__(self, callback_function, timeout: int = 60, retry_count: int = 1, description: str = ""):
        super().__init__("callback", description or "执行回调操作")
        self.callback_function = callback_function
        self.timeout = timeout
        self.retry_count = retry_count

    def _execute_impl(self, driver: webdriver.Chrome) -> ActionResult:
        """执行回调操作的具体实现"""
        for attempt in range(self.retry_count + 1):
            try:
                print(f"🔄 执行回调操作 (尝试 {attempt + 1}/{self.retry_count + 1})")

                # 构建页面上下文
                page_context = PageContext(
                    current_url=driver.current_url,
                    page_title=driver.title,
                    page_id="sequence_callback",
                    driver=driver
                )

                # 调用回调函数
                action_sequence = self.callback_function(driver, page_context)

                if action_sequence.is_failed():
                    print(f"❌ 回调函数返回失败: {action_sequence.error_message}")
                    if attempt < self.retry_count:
                        print("🔄 准备重试...")
                        time.sleep(2)
                        continue
                    else:
                        return ActionResult.FAILED

                # 执行返回的操作序列
                result = self._execute_action_sequence(action_sequence, driver)

                if result == ActionResult.SUCCESS:
                    print("✅ 回调操作执行成功")
                    return ActionResult.SUCCESS
                elif result == ActionResult.INTERRUPTED:
                    print("🚨 回调操作被中断")
                    return ActionResult.INTERRUPTED
                else:
                    print("❌ 操作序列执行失败")
                    if attempt < self.retry_count:
                        continue
                    else:
                        return ActionResult.FAILED

            except Exception as e:
                print(f"❌ 回调操作异常: {e}")
                if attempt < self.retry_count:
                    continue
                else:
                    return ActionResult.FAILED

        return ActionResult.FAILED

    def _execute_action_sequence(self, action_sequence, driver: webdriver.Chrome) -> ActionResult:
        """执行操作序列"""
        print(f"🎭 执行操作序列 ({len(action_sequence)} 个操作)")

        for i, atomic_action in enumerate(action_sequence, 1):
            print(f"🔄 执行序列操作 {i}/{len(action_sequence)}: {atomic_action}")

            # 执行原子操作
            result = atomic_action.execute(driver)

            if result != ActionResult.SUCCESS:
                print(f"❌ 序列操作 {i} 失败")
                return result

            print(f"✅ 序列操作 {i} 成功")

        print("🎉 操作序列执行完成")
        return ActionResult.SUCCESS


class MultiSelectorClickAction(AtomicAction):
    """多选择器点击操作 - 尝试多个选择器直到成功"""

    def __init__(self, selectors: List[str], description: str = ""):
        super().__init__("multi_click", description or "多选择器智能点击")
        self.selectors = selectors

    def _execute_impl(self, driver: webdriver.Chrome) -> ActionResult:
        """执行多选择器点击操作的具体实现"""
        print(f"🔍 开始多选择器点击，共 {len(self.selectors)} 个选择器")

        for i, selector in enumerate(self.selectors):
            try:
                print(f"🎯 尝试选择器 {i+1}/{len(self.selectors)}: {selector[:50]}...")

                # 根据选择器类型查找元素
                if selector.startswith("//"):
                    element = driver.find_element(By.XPATH, selector)
                else:
                    element = driver.find_element(By.CSS_SELECTOR, selector)

                # 检查元素是否可见和可点击
                if element.is_displayed() and element.is_enabled():
                    print(f"✅ 找到可点击元素: {element.text[:30] if element.text else '无文本'}")

                    # 滚动到元素位置
                    driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(0.5)

                    # 模拟人类点击前的短暂停顿
                    time.sleep(random.uniform(0.5, 1.0))

                    # 使用JavaScript点击确保成功
                    driver.execute_script("arguments[0].click();", element)

                    print(f"✅ 多选择器点击成功: 选择器 {i+1}")
                    return ActionResult.SUCCESS

            except Exception as e:
                print(f"⚠️ 选择器 {i+1} 失败: {str(e)[:50]}...")
                continue

        print(f"❌ 所有 {len(self.selectors)} 个选择器都失败了")
        return ActionResult.FAILED


class ActionSequence:
    """操作序列"""

    def __init__(self, actions: List[AtomicAction] = None, error_message: str = ""):
        self.actions = actions or []
        self.error_message = error_message
        self._failed = bool(error_message)

    def add_action(self, action: AtomicAction):
        """添加操作"""
        self.actions.append(action)

    def is_failed(self) -> bool:
        """是否失败"""
        return self._failed

    @classmethod
    def failed(cls, error_message: str):
        """创建失败的操作序列"""
        return cls(error_message=error_message)

    def __len__(self):
        return len(self.actions)

    def __iter__(self):
        return iter(self.actions)


# ==================== 高级操作类型 ====================

class SequenceAction(AtomicAction):
    """操作序列 - 组合多个原子操作"""

    def __init__(self, actions: List[Dict], variables: Dict[str, Any] = None, description: str = "",
                 dynamic_variable_getter=None):
        super().__init__("sequence", description or "执行操作序列")
        self.actions = actions
        self.variables = variables or {}
        self.dynamic_variable_getter = dynamic_variable_getter

    def _execute_impl(self, driver: webdriver.Chrome) -> ActionResult:
        """执行操作序列的具体实现"""
        print(f"🎭 开始执行操作序列 ({len(self.actions)} 个操作)")

        for i, action_config in enumerate(self.actions, 1):
            print(f"🔄 执行序列操作 {i}/{len(self.actions)}: {action_config.get('type', 'unknown')}")

            # 变量替换
            processed_config = self._process_variables(action_config)

            # 创建并执行原子操作
            atomic_action = self._create_atomic_action(processed_config)
            if not atomic_action:
                print(f"❌ 无法创建操作: {action_config.get('type', 'unknown')}")
                return ActionResult.FAILED

            # 修复：传递动态变量获取器到子操作
            if hasattr(self, 'dynamic_variable_getter') and self.dynamic_variable_getter:
                atomic_action.dynamic_variable_getter = self.dynamic_variable_getter
                print(f"🔗 传递动态变量获取器到 {type(atomic_action).__name__}")

            result = atomic_action.execute(driver)
            if result != ActionResult.SUCCESS:
                print(f"❌ 序列操作 {i} 失败")
                return result

            print(f"✅ 序列操作 {i} 成功")

        print("🎉 操作序列执行完成")
        return ActionResult.SUCCESS

    def _process_variables(self, action_config: Dict) -> Dict:
        """处理变量替换（增强版 - 支持动态变量）"""
        processed_config = action_config.copy()

        # 变量替换实现
        for key, value in processed_config.items():
            if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
                var_name = value[1:-1]

                # 首先检查静态变量
                if var_name in self.variables:
                    processed_config[key] = self.variables[var_name]
                # 然后检查是否是动态变量标记
                elif value == "dynamic_from_callback":
                    # 尝试从动态变量获取器获取值
                    if self.dynamic_variable_getter:
                        dynamic_value = self.dynamic_variable_getter(var_name)
                        processed_config[key] = dynamic_value
                        print(f"🔄 动态变量替换: {var_name} -> {dynamic_value}")
                    else:
                        processed_config[key] = f"missing_{var_name}"
                else:
                    # 对于花括号变量，保持原样，让InputAction在执行时处理
                    # 不要在这里替换，因为这里可能没有动态变量获取器
                    processed_config[key] = value  # 保持 {firstName} 格式

        return processed_config

    def _get_dynamic_variable(self, var_name: str) -> str:
        """获取动态变量值"""
        # 这里需要从执行上下文中获取动态变量
        # 暂时返回占位符，实际执行时会被替换
        return f"{{dynamic_{var_name}}}"

    def _create_atomic_action(self, action_config: Dict) -> Optional[AtomicAction]:
        """根据配置创建原子操作"""
        action_type = action_config.get("type", "")

        if action_type == "input":
            # print(f"🚨 [DEBUG] 创建 InputAction: config_value='{action_config.get('value', 'MISSING')}'")
            action = InputAction(
                selector=action_config["selector"],
                value=action_config["value"],
                typing_style=action_config.get("typing_style", "human"),
                description=action_config.get("description", "")
            )
            # 修复：传递动态变量获取器到InputAction
            if hasattr(self, 'dynamic_variable_getter'):
                action.dynamic_variable_getter = self.dynamic_variable_getter
            return action
        elif action_type == "click":
            return ClickAction(
                selector=action_config["selector"],
                description=action_config.get("description", "")
            )
        elif action_type == "delay":
            return DelayAction(
                duration=action_config["duration"],
                description=action_config.get("description", "")
            )
        elif action_type == "select":
            return SelectAction(
                selector=action_config["selector"],
                value=action_config["value"],
                method=action_config.get("method", "by_text"),
                description=action_config.get("description", "")
            )
        elif action_type == "check":
            return CheckAction(
                selector=action_config["selector"],
                checked=action_config.get("checked", True),
                description=action_config.get("description", "")
            )
        elif action_type == "wait_for_element":
            return WaitForElementAction(
                selector=action_config["selector"],
                condition=action_config.get("condition", "visible"),
                timeout=action_config.get("timeout", 30),
                description=action_config.get("description", "")
            )
        elif action_type == "key_press":
            return KeyPressAction(
                keys=action_config["keys"],
                description=action_config.get("description", "")
            )
        elif action_type == "scroll":
            return ScrollAction(
                direction=action_config.get("direction", "down"),
                distance=action_config.get("distance", 500),
                selector=action_config.get("selector"),
                description=action_config.get("description", "")
            )
        elif action_type == "hover":
            return HoverAction(
                selector=action_config["selector"],
                description=action_config.get("description", "")
            )
        elif action_type == "switch_window":
            return SwitchWindowAction(
                window_index=action_config.get("window_index"),
                window_handle=action_config.get("window_handle"),
                description=action_config.get("description", "")
            )
        elif action_type == "upload_file":
            return UploadFileAction(
                selector=action_config["selector"],
                file_path=action_config["file_path"],
                description=action_config.get("description", "")
            )
        elif action_type == "extract_text":
            return ExtractTextAction(
                selector=action_config["selector"],
                variable=action_config["variable"],
                attribute=action_config.get("attribute"),
                description=action_config.get("description", "")
            )
        elif action_type == "verify_element":
            return VerifyElementAction(
                selector=action_config["selector"],
                expected_text=action_config.get("expected_text"),
                expected_attribute=action_config.get("expected_attribute", {}),
                fail_action=action_config.get("fail_action", "abort"),
                description=action_config.get("description", "")
            )
        elif action_type == "multi_click":
            return MultiSelectorClickAction(
                selectors=action_config["selectors"],
                description=action_config.get("description", "")
            )
        elif action_type == "retry":
            return RetryAction(
                actions=action_config["actions"],
                max_attempts=action_config.get("max_attempts", 3),
                success_condition=action_config.get("success_condition"),
                retry_delay=action_config.get("retry_delay", 1.0),
                description=action_config.get("description", "")
            )
        elif action_type == "sequence":
            # 修复：支持嵌套的SequenceAction
            return SequenceAction(
                actions=action_config["actions"],
                variables=action_config.get("variables", {}),
                description=action_config.get("description", ""),
                dynamic_variable_getter=getattr(self, 'dynamic_variable_getter', None)
            )
        elif action_type == "callback":
            # 修复：在序列中支持callback操作
            # 创建一个特殊的CallbackAction来处理
            return CallbackAction(
                callback_function=action_config["callback_function"],
                timeout=action_config.get("timeout", 60),
                retry_count=action_config.get("retry_count", 1),
                description=action_config.get("description", "")
            )
        else:
            return None


class ConditionalAction(AtomicAction):
    """条件操作 - 根据条件执行不同操作"""

    def __init__(self, condition: Dict, if_true: List[Dict], if_false: List[Dict] = None, description: str = ""):
        super().__init__("conditional", description or "执行条件操作")
        self.condition = condition
        self.if_true = if_true
        self.if_false = if_false or []

    def _execute_impl(self, driver: webdriver.Chrome) -> ActionResult:
        """执行条件操作的具体实现"""
        print(f"🔍 评估条件: {self.condition.get('type', 'unknown')}")

        # 评估条件
        condition_result = self._evaluate_condition(driver)
        print(f"📊 条件结果: {condition_result}")

        # 选择执行的操作列表
        actions_to_execute = self.if_true if condition_result else self.if_false

        if not actions_to_execute:
            print("ℹ️ 无操作需要执行")
            return ActionResult.SUCCESS

        # 创建并执行操作序列
        sequence = SequenceAction(actions_to_execute, description="条件操作序列")
        return sequence.execute(driver)

    def _evaluate_condition(self, driver: webdriver.Chrome) -> bool:
        """评估条件"""
        condition_type = self.condition.get("type", "")

        try:
            if condition_type == "element_exists":
                selector = self.condition["selector"]
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                return len(elements) > 0

            elif condition_type == "element_visible":
                selector = self.condition["selector"]
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    return element.is_displayed()
                except:
                    return False

            elif condition_type == "text_contains":
                selector = self.condition["selector"]
                expected_text = self.condition["text"]
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    return expected_text in element.text
                except:
                    return False

            elif condition_type == "url_contains":
                expected_url = self.condition["url"]
                return expected_url in driver.current_url

            else:
                print(f"❌ 不支持的条件类型: {condition_type}")
                return False

        except Exception as e:
            print(f"❌ 条件评估异常: {e}")
            return False


class RetryAction(AtomicAction):
    """重试操作 - 重复执行直到成功或达到最大次数"""

    def __init__(self, actions: List[Dict], max_attempts: int = 3, success_condition: Dict = None,
                 retry_delay: float = 1.0, description: str = ""):
        super().__init__("retry", description or "执行重试操作")
        self.actions = actions
        self.max_attempts = max_attempts
        self.success_condition = success_condition
        self.retry_delay = retry_delay

    def _execute_impl(self, driver: webdriver.Chrome) -> ActionResult:
        """执行重试操作的具体实现"""
        print(f"🔄 开始重试操作 (最大尝试次数: {self.max_attempts})")

        for attempt in range(1, self.max_attempts + 1):
            print(f"🎯 第 {attempt}/{self.max_attempts} 次尝试")

            # 执行操作序列
            sequence = SequenceAction(self.actions, description=f"重试操作序列 (第{attempt}次)")
            result = sequence.execute(driver)

            if result == ActionResult.SUCCESS:
                # 检查成功条件
                if self._check_success_condition(driver):
                    print(f"✅ 重试操作成功 (第{attempt}次尝试)")
                    return ActionResult.SUCCESS
                else:
                    print(f"⚠️ 操作执行成功但不满足成功条件")

            if attempt < self.max_attempts:
                print(f"⏳ 等待 {self.retry_delay} 秒后重试...")
                time.sleep(self.retry_delay)

        print(f"❌ 重试操作失败 (已尝试 {self.max_attempts} 次)")
        return ActionResult.FAILED

    def _check_success_condition(self, driver: webdriver.Chrome) -> bool:
        """检查成功条件"""
        if not self.success_condition:
            return True  # 没有成功条件，认为成功

        condition_type = self.success_condition.get("type", "")

        try:
            if condition_type == "page_changed":
                # 简单实现：检查URL是否变化（需要记录初始URL）
                return True  # 暂时总是返回True

            elif condition_type == "element_appears":
                selector = self.success_condition["selector"]
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                return len(elements) > 0

            elif condition_type == "element_disappears":
                selector = self.success_condition["selector"]
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                return len(elements) == 0

            else:
                print(f"❌ 不支持的成功条件: {condition_type}")
                return True

        except Exception as e:
            print(f"❌ 成功条件检查异常: {e}")
            return False


# ==================== 页面识别器（渐进式混合识别） ====================

class PageDetector:
    """页面检测器 - 渐进式混合识别"""

    def __init__(self, page_definitions: Dict[str, Dict]):
        self.page_definitions = page_definitions
        self._compile_patterns()

    def _compile_patterns(self):
        """预编译正则表达式模式"""
        self.url_patterns = {}
        self.title_patterns = {}

        for page_id, page_config in self.page_definitions.items():
            # 编译URL模式
            primary_id = page_config.get("primary_identifier", {})
            if primary_id.get("type") == "url":
                pattern = primary_id.get("pattern", "")
                if pattern:
                    self.url_patterns[page_id] = {
                        "regex": re.compile(pattern),
                        "confidence": primary_id.get("confidence", 0.8)
                    }

            # 编译备用标题模式
            fallback_ids = page_config.get("fallback_identifiers", [])
            for fallback in fallback_ids:
                if fallback.get("type") == "title":
                    pattern = fallback.get("pattern", "")
                    if pattern:
                        if page_id not in self.title_patterns:
                            self.title_patterns[page_id] = []
                        self.title_patterns[page_id].append({
                            "regex": re.compile(pattern),
                            "confidence": fallback.get("confidence", 0.6)
                        })

    def identify_page(self, current_url: str, page_title: str = "") -> PageCandidate:
        """识别当前页面 - 渐进式混合识别"""

        # 第一层：快速URL识别（主要判断）
        url_candidate = self._quick_url_identify(current_url)

        if url_candidate.confidence >= 0.8:
            return url_candidate

        # 第二层：标题匹配（备用方案）
        if page_title:
            title_candidate = self._title_identify(page_title)
            if title_candidate.confidence > url_candidate.confidence:
                return title_candidate

        # 返回最佳候选或未知页面
        if url_candidate.confidence > 0:
            return url_candidate
        else:
            return PageCandidate("unknown", 0.0, "none", "无法识别页面")

    def identify_page_with_fallback(self, current_url: str, page_title: str = "",
                                   expected_page_id: str = None) -> PageCandidate:
        """增强的页面识别 - 三层识别机制（防丢失核心功能）"""

        # 第一层：期望页面优先识别
        if expected_page_id:
            expected_candidate = self._identify_specific_page(current_url, page_title, expected_page_id)
            if expected_candidate.confidence >= 0.7:
                print(f"🎯 期望页面识别成功: {expected_page_id} (置信度: {expected_candidate.confidence})")
                return expected_candidate

        # 第二层：全量页面识别（防丢失核心）
        print("🔍 执行全量页面识别（防丢失机制）...")
        all_candidates = self._identify_all_pages(current_url, page_title)

        if all_candidates:
            best_candidate = all_candidates[0]  # 已按置信度排序
            if best_candidate.confidence >= 0.6:  # 降低阈值，增加容错性
                print(f"🎯 全量识别成功: {best_candidate.page_id} (置信度: {best_candidate.confidence})")
                return best_candidate

        # 第三层：兜底处理
        print("⚠️ 所有识别方法均失败，返回未知页面")
        return PageCandidate("unknown", 0.0, "fallback", "所有识别方法均失败")

    def _identify_specific_page(self, url: str, title: str, page_id: str) -> PageCandidate:
        """识别特定页面"""
        if page_id not in self.page_definitions:
            return PageCandidate("unknown", 0.0, "specific", f"页面ID不存在: {page_id}")

        # 检查URL模式
        if page_id in self.url_patterns:
            pattern_info = self.url_patterns[page_id]
            if pattern_info["regex"].search(url):
                return PageCandidate(
                    page_id=page_id,
                    confidence=pattern_info["confidence"],
                    match_method="url",
                    match_details=f"特定URL匹配: {url[:100]}..."
                )

        # 检查标题模式
        if page_id in self.title_patterns and title:
            for pattern_info in self.title_patterns[page_id]:
                if pattern_info["regex"].search(title):
                    return PageCandidate(
                        page_id=page_id,
                        confidence=pattern_info["confidence"],
                        match_method="title",
                        match_details=f"特定标题匹配: {title}"
                    )

        return PageCandidate("unknown", 0.0, "specific", f"特定页面识别失败: {page_id}")

    def _identify_all_pages(self, url: str, title: str) -> List[PageCandidate]:
        """对所有已定义页面进行识别（防丢失核心功能）"""
        candidates = []

        print(f"🔍 开始全量页面识别，共 {len(self.page_definitions)} 个页面")

        for page_id in self.page_definitions.keys():
            candidate = self._identify_specific_page(url, title, page_id)
            if candidate.confidence > 0:
                candidates.append(candidate)
                print(f"   ✅ {page_id}: {candidate.confidence:.2f} ({candidate.match_method})")
            else:
                print(f"   ❌ {page_id}: 不匹配")

        # 按置信度排序
        candidates.sort(key=lambda x: x.confidence, reverse=True)

        if candidates:
            print(f"🎯 找到 {len(candidates)} 个候选页面，最佳: {candidates[0].page_id}")
        else:
            print("❌ 全量识别无匹配页面")

        return candidates

    def _quick_url_identify(self, url: str) -> PageCandidate:
        """第一层：基于URL的快速识别"""
        for page_id, pattern_info in self.url_patterns.items():
            if pattern_info["regex"].search(url):
                return PageCandidate(
                    page_id=page_id,
                    confidence=pattern_info["confidence"],
                    match_method="url",
                    match_details=f"URL匹配: {url[:100]}..."
                )

        return PageCandidate("unknown", 0.0, "url", "URL未匹配任何模式")

    def _title_identify(self, title: str) -> PageCandidate:
        """第二层：基于标题的识别"""
        for page_id, title_patterns in self.title_patterns.items():
            for pattern_info in title_patterns:
                if pattern_info["regex"].search(title):
                    return PageCandidate(
                        page_id=page_id,
                        confidence=pattern_info["confidence"],
                        match_method="title",
                        match_details=f"标题匹配: {title}"
                    )

        return PageCandidate("unknown", 0.0, "title", "标题未匹配任何模式")


# ==================== 可中断的执行引擎 ====================

class InterruptibleActionExecutor:
    """可中断的操作执行器"""

    def __init__(self, page_detector: PageDetector):
        self.page_detector = page_detector
        self.current_page_id = None
        self.should_stop = False
        self.control_panel = None  # 控制面板引用

    def execute_page_actions(self, page_config: Dict, driver: webdriver.Chrome) -> ActionResult:
        """执行页面操作（可中断）"""
        self.current_page_id = page_config["id"]
        self.should_stop = False

        actions = page_config.get("actions", [])

        if not actions:
            print(f"📄 页面 {self.current_page_id} 无操作，等待页面跳转")
            return ActionResult.SUCCESS

        print(f"🎬 开始执行页面操作: {self.current_page_id} ({len(actions)} 个操作)")

        for i, action_config in enumerate(actions, 1):
            print(f"🔄 执行操作 {i}/{len(actions)}: {action_config.get('description', action_config.get('type', 'unknown'))}")

            # 检查控制面板状态
            if self.control_panel:
                # 检查是否暂停（如果事件未设置，则等待）
                if not self.control_panel.is_paused.is_set():
                    print("⏸️ 操作执行已暂停，等待用户恢复...")
                    self.control_panel.is_paused.wait()  # 阻塞直到恢复
                    print("▶️ 操作执行已恢复")

                # 检查是否退出当前页
                if self.control_panel.should_exit_page.is_set():
                    print("🚪 用户请求退出当前页面操作")
                    return ActionResult.INTERRUPTED

            # 每个操作前都检查页面是否还是当前页面
            if self._check_page_changed(driver):
                print(f"🚨 检测到页面变化，中断操作执行")
                return ActionResult.INTERRUPTED

            # 执行单个操作
            result = self._execute_single_action(action_config, driver)

            if result == ActionResult.INTERRUPTED:
                return result
            elif result == ActionResult.FAILED:
                print(f"❌ 操作 {i} 执行失败")
                return result

            print(f"✅ 操作 {i} 执行成功")

        print(f"🎉 页面 {self.current_page_id} 所有操作执行完成")
        return ActionResult.SUCCESS

    def _execute_single_action(self, action_config: Dict, driver: webdriver.Chrome) -> ActionResult:
        """执行单个操作"""
        action_type = action_config.get("type", "")

        try:
            if action_type == "input":
                action = InputAction(
                    selector=action_config["selector"],
                    value=action_config["value"],
                    typing_style=action_config.get("typing_style", "human"),
                    description=action_config.get("description", "")
                )
                return self._execute_atomic_action(action, driver)

            elif action_type == "click":
                action = ClickAction(
                    selector=action_config["selector"],
                    description=action_config.get("description", "")
                )
                return self._execute_atomic_action(action, driver)

            elif action_type == "delay":
                action = DelayAction(
                    duration=action_config["duration"],
                    description=action_config.get("description", "")
                )
                return self._execute_interruptible_delay(action, driver)

            elif action_type == "select":
                action = SelectAction(
                    selector=action_config["selector"],
                    value=action_config["value"],
                    method=action_config.get("method", "by_text"),
                    description=action_config.get("description", "")
                )
                return self._execute_atomic_action(action, driver)

            elif action_type == "check":
                action = CheckAction(
                    selector=action_config["selector"],
                    checked=action_config.get("checked", True),
                    description=action_config.get("description", "")
                )
                return self._execute_atomic_action(action, driver)

            elif action_type == "wait_for_element":
                action = WaitForElementAction(
                    selector=action_config["selector"],
                    condition=action_config.get("condition", "visible"),
                    timeout=action_config.get("timeout", 30),
                    description=action_config.get("description", "")
                )
                return self._execute_atomic_action(action, driver)

            elif action_type == "key_press":
                action = KeyPressAction(
                    keys=action_config["keys"],
                    description=action_config.get("description", "")
                )
                return self._execute_atomic_action(action, driver)

            elif action_type == "scroll":
                action = ScrollAction(
                    direction=action_config.get("direction", "down"),
                    distance=action_config.get("distance", 500),
                    selector=action_config.get("selector"),
                    description=action_config.get("description", "")
                )
                return self._execute_atomic_action(action, driver)

            elif action_type == "hover":
                action = HoverAction(
                    selector=action_config["selector"],
                    description=action_config.get("description", "")
                )
                return self._execute_atomic_action(action, driver)

            elif action_type == "switch_window":
                action = SwitchWindowAction(
                    window_index=action_config.get("window_index"),
                    window_handle=action_config.get("window_handle"),
                    description=action_config.get("description", "")
                )
                return self._execute_atomic_action(action, driver)

            elif action_type == "upload_file":
                action = UploadFileAction(
                    selector=action_config["selector"],
                    file_path=action_config["file_path"],
                    description=action_config.get("description", "")
                )
                return self._execute_atomic_action(action, driver)

            elif action_type == "extract_text":
                action = ExtractTextAction(
                    selector=action_config["selector"],
                    variable=action_config["variable"],
                    attribute=action_config.get("attribute"),
                    description=action_config.get("description", "")
                )
                return self._execute_atomic_action(action, driver)

            elif action_type == "verify_element":
                action = VerifyElementAction(
                    selector=action_config["selector"],
                    expected_text=action_config.get("expected_text"),
                    expected_attribute=action_config.get("expected_attribute", {}),
                    fail_action=action_config.get("fail_action", "abort"),
                    description=action_config.get("description", "")
                )
                return self._execute_atomic_action(action, driver)

            elif action_type == "multi_click":
                action = MultiSelectorClickAction(
                    selectors=action_config["selectors"],
                    description=action_config.get("description", "")
                )
                return self._execute_atomic_action(action, driver)

            elif action_type == "sequence":
                action = SequenceAction(
                    actions=action_config["actions"],
                    variables=action_config.get("variables", {}),
                    description=action_config.get("description", ""),
                    dynamic_variable_getter=getattr(self, 'dynamic_variable_getter', None)
                )
                return self._execute_atomic_action(action, driver)

            elif action_type == "conditional":
                action = ConditionalAction(
                    condition=action_config["condition"],
                    if_true=action_config["if_true"],
                    if_false=action_config.get("if_false", []),
                    description=action_config.get("description", "")
                )
                return self._execute_atomic_action(action, driver)

            elif action_type == "retry":
                action = RetryAction(
                    actions=action_config["actions"],
                    max_attempts=action_config.get("max_attempts", 3),
                    success_condition=action_config.get("success_condition"),
                    retry_delay=action_config.get("retry_delay", 1.0),
                    description=action_config.get("description", "")
                )
                return self._execute_atomic_action(action, driver)

            elif action_type == "callback":
                return self._execute_callback_action(action_config, driver)

            else:
                print(f"❌ 不支持的操作类型: {action_type}")
                return ActionResult.FAILED

        except Exception as e:
            print(f"❌ 执行操作时发生异常: {e}")
            return ActionResult.FAILED

    def _execute_atomic_action(self, action: AtomicAction, driver: webdriver.Chrome) -> ActionResult:
        """执行原子操作"""
        return action.execute(driver)

    def _execute_interruptible_delay(self, delay_action: DelayAction, driver: webdriver.Chrome) -> ActionResult:
        """执行可中断的延迟操作"""
        total_duration = delay_action.duration
        check_interval = 0.5
        elapsed = 0

        print(f"⏳ 开始延迟 {total_duration} 秒（可中断）...")

        while elapsed < total_duration:
            # 检查是否需要中断
            if self._check_page_changed(driver):
                print(f"🚨 延迟操作被中断 (已延迟{elapsed:.1f}s/{total_duration}s)")
                return ActionResult.INTERRUPTED

            # 短暂睡眠
            sleep_time = min(check_interval, total_duration - elapsed)
            time.sleep(sleep_time)
            elapsed += sleep_time

        print(f"✅ 延迟操作完成")
        return ActionResult.SUCCESS

    def _execute_callback_action(self, action_config: Dict, driver: webdriver.Chrome) -> ActionResult:
        """执行回调操作"""
        callback_func = action_config.get("callback_function")
        if not callback_func:
            print("❌ 回调函数未定义")
            return ActionResult.FAILED

        timeout = action_config.get("timeout", 60)
        retry_count = action_config.get("retry_count", 1)

        for attempt in range(retry_count + 1):
            try:
                print(f"🔄 执行回调操作 (尝试 {attempt + 1}/{retry_count + 1})")

                # 构建页面上下文
                page_context = PageContext(
                    current_url=driver.current_url,
                    page_title=driver.title,
                    page_id=self.current_page_id,
                    driver=driver
                )

                # 调用回调函数
                action_sequence = callback_func(driver, page_context)

                if action_sequence.is_failed():
                    print(f"❌ 回调函数返回失败: {action_sequence.error_message}")
                    if attempt < retry_count:
                        print("🔄 准备重试...")
                        time.sleep(2)
                        continue
                    else:
                        return ActionResult.FAILED

                # 执行返回的操作序列
                result = self._execute_action_sequence(action_sequence, driver)

                if result == ActionResult.SUCCESS:
                    print("✅ 回调操作执行成功")
                    return ActionResult.SUCCESS
                elif result == ActionResult.INTERRUPTED:
                    print("🚨 回调操作被中断")
                    return ActionResult.INTERRUPTED
                else:
                    print("❌ 操作序列执行失败")
                    if attempt < retry_count:
                        continue
                    else:
                        return ActionResult.FAILED

            except Exception as e:
                print(f"❌ 回调操作异常: {e}")
                if attempt < retry_count:
                    continue
                else:
                    return ActionResult.FAILED

        return ActionResult.FAILED

    def _execute_action_sequence(self, action_sequence: ActionSequence, driver: webdriver.Chrome) -> ActionResult:
        """执行操作序列"""
        print(f"🎭 执行操作序列 ({len(action_sequence)} 个操作)")

        for i, atomic_action in enumerate(action_sequence, 1):
            print(f"🔄 执行序列操作 {i}/{len(action_sequence)}: {atomic_action}")

            # 检查页面是否变化（中断机制）
            if self._check_page_changed(driver):
                print("🚨 操作序列被中断")
                return ActionResult.INTERRUPTED

            # 执行原子操作
            result = atomic_action.execute(driver)

            if result != ActionResult.SUCCESS:
                print(f"❌ 序列操作 {i} 失败")
                return result

            print(f"✅ 序列操作 {i} 成功")

        print("🎉 操作序列执行完成")
        return ActionResult.SUCCESS

    def _check_page_changed(self, driver: webdriver.Chrome) -> bool:
        """检查页面是否发生变化"""
        try:
            current_url = driver.current_url
            current_title = driver.title

            detected_page = self.page_detector.identify_page(current_url, current_title)

            if detected_page.page_id != self.current_page_id and detected_page.page_id != "unknown":
                print(f"📄 页面变化检测: {self.current_page_id} -> {detected_page.page_id}")
                return True

            return False

        except Exception as e:
            print(f"⚠️ 页面变化检测异常: {e}")
            return False


# ==================== 工作流程状态机 ====================

class WorkflowStateMachine:
    """工作流程状态机"""

    def __init__(self, workflow_config: Dict):
        self.workflow_config = workflow_config
        self.pages = {page["id"]: page for page in workflow_config.get("pages", [])}
        self.current_page_index = 0
        self.page_sequence = [page["id"] for page in workflow_config.get("pages", [])]

    def get_expected_page(self) -> Dict:
        """获取当前期望的页面"""
        if self.current_page_index < len(self.page_sequence):
            page_id = self.page_sequence[self.current_page_index]
            return self.pages[page_id]
        return {}

    def get_page_config(self, page_id: str) -> Dict:
        """根据页面ID获取页面配置"""
        return self.pages.get(page_id, {})

    def advance_to_next_state(self):
        """推进到下一个状态"""
        self.current_page_index += 1

    def is_complete(self) -> bool:
        """检查工作流程是否完成"""
        return self.current_page_index >= len(self.page_sequence)

    def reset(self):
        """重置状态机"""
        self.current_page_index = 0


# ==================== 主要的自动化框架类 ====================

class WebAutomationFramework:
    """Web自动化框架 - 主入口类"""

    def __init__(self, workflow_config: Dict, enable_control_panel: bool = False):
        self.workflow_config = workflow_config
        self.workflow = WorkflowStateMachine(workflow_config)
        self.page_detector = PageDetector(self._extract_page_definitions())
        self.action_executor = InterruptibleActionExecutor(self.page_detector)
        self.driver = None
        self.max_unknown_page_retries = 3
        self.page_transition_timeout = 30
        self.dynamic_variable_getter = None  # 动态变量获取器

        # 控制面板相关
        self.enable_control_panel = enable_control_panel
        self.control_panel = None

        if self.enable_control_panel:
            if GUI_AVAILABLE:
                try:
                    self.control_panel = AutomationControlPanel(self)
                    print("🎛️ 控制面板已初始化")
                except Exception as e:
                    print(f"❌ 控制面板初始化失败: {e}")
            else:
                print("❌ Tkinter不可用，控制面板无法启动")

    def _extract_page_definitions(self) -> Dict[str, Dict]:
        """从工作流程配置中提取页面定义"""
        page_definitions = {}
        for page in self.workflow_config.get("pages", []):
            page_definitions[page["id"]] = page
        return page_definitions

    def set_driver(self, driver: webdriver.Chrome):
        """设置WebDriver实例"""
        self.driver = driver
        # 将动态变量获取器传递给执行引擎
        if hasattr(self, 'dynamic_variable_getter'):
            self.action_executor.dynamic_variable_getter = self.dynamic_variable_getter

    def set_context_provider(self, provider):
        """设置上下文提供者（低耦合设计）"""
        self.context_provider = provider
        # 将上下文传递给driver，供InputAction使用（松耦合）
        if self.driver:
            self.driver._framework_context = provider
            print(f"🔗 框架上下文已设置: {type(provider).__name__}")

        # 同时传递给动作执行器
        if hasattr(self.action_executor, 'set_context_provider'):
            self.action_executor.set_context_provider(provider)

    def execute_workflow(self) -> bool:
        """执行完整的工作流程（增强版 - 支持实时控制）"""
        if not self.driver:
            print("❌ WebDriver未设置")
            return False

        print("🚀 开始执行Web自动化工作流程")
        print(f"📋 工作流程: {self.workflow_config.get('name', '未命名')}")
        print(f"📄 总页面数: {len(self.workflow_config.get('pages', []))}")

        # 启动控制面板
        if self.enable_control_panel and self.control_panel:
            self.control_panel.start_panel()
            # 将控制面板传递给执行器
            self.action_executor.control_panel = self.control_panel
            print("🎛️ 控制面板已激活，可实时控制自动化流程")
            # 给用户一点时间看到控制面板
            time.sleep(1)

        unknown_page_count = 0
        fallback_retry_count = 0
        max_fallback_retries = 10  # 增加兜底重试次数

        while not self.workflow.is_complete():
            try:
                # 0. 检查控制面板状态
                if self.enable_control_panel and self.control_panel:
                    # 检查是否暂停
                    if not self.control_panel.is_paused.is_set():
                        print("⏸️ 自动化已暂停，等待用户恢复...")
                        self.control_panel.is_paused.wait()  # 阻塞直到恢复
                        print("▶️ 自动化已恢复")

                    # 检查是否退出当前页
                    if self.control_panel.should_exit_page.is_set():
                        print("🚪 用户请求退出当前页面")
                        self.control_panel.should_exit_page.clear()
                        # 进入页面变化等待模式
                        if self._wait_for_page_change_after_exit():
                            print("✅ 检测到页面变化，自动化恢复")
                            self.control_panel.reset_exit_page_status()
                            continue
                        else:
                            print("⏰ 页面变化等待超时")
                            return False

                # 1. 获取期望页面信息
                expected_page = self.workflow.get_expected_page()
                expected_page_id = expected_page.get("id") if expected_page else None

                # 2. 增强页面检测（使用防丢失机制）
                current_url = self.driver.current_url
                current_title = self.driver.title

                # 首先尝试标准识别
                detected_page = self.page_detector.identify_page(current_url, current_title)

                print(f"\n🔍 页面检测结果:")
                print(f"   URL: {current_url[:80]}...")
                print(f"   标题: {current_title}")
                print(f"   期望页面: {expected_page_id}")
                print(f"   识别结果: {detected_page.page_id} (置信度: {detected_page.confidence})")
                print(f"   匹配方法: {detected_page.match_method}")

                # 3. 处理未知页面 - 启用防丢失机制
                if detected_page.page_id == "unknown":
                    unknown_page_count += 1
                    print(f"⚠️ 标准识别失败 (第{unknown_page_count}次)")

                    # 启用兜底识别机制
                    print("🛡️ 启动防丢失兜底识别机制...")
                    fallback_detected = self.page_detector.identify_page_with_fallback(
                        current_url, current_title, expected_page_id
                    )

                    if fallback_detected.page_id != "unknown":
                        print(f"🎯 兜底识别成功: {fallback_detected.page_id}")
                        detected_page = fallback_detected
                        unknown_page_count = 0  # 重置计数器
                    else:
                        fallback_retry_count += 1
                        print(f"❌ 兜底识别也失败 (第{fallback_retry_count}次)")

                        if fallback_retry_count >= max_fallback_retries:
                            print("❌ 兜底识别重试次数过多，终止流程")
                            return False

                        # 智能轮询等待（随机时间间隔）
                        wait_time = random.uniform(2.0, 5.0)
                        print(f"⏳ 智能轮询等待 {wait_time:.1f}秒 后重试...")
                        time.sleep(wait_time)
                        continue
                else:
                    unknown_page_count = 0  # 重置计数器
                    fallback_retry_count = 0  # 重置兜底计数器

                # 3. 获取页面配置
                page_config = self.workflow.get_page_config(detected_page.page_id)
                if not page_config:
                    print(f"❌ 未找到页面配置: {detected_page.page_id}")
                    return False

                # 4. 检查是否符合流程期望并智能调整状态
                if detected_page.page_id == expected_page_id:
                    print(f"✅ 页面符合流程期望: {detected_page.page_id}")
                elif detected_page.confidence >= 0.6:  # 降低阈值，增加容错性
                    print(f"🔄 页面跳跃检测: 期望 {expected_page_id} -> 实际 {detected_page.page_id}")
                    # 尝试智能调整工作流程状态
                    if self._adjust_workflow_state(detected_page.page_id):
                        print("✅ 工作流程状态调整成功")
                    else:
                        print("⚠️ 工作流程状态调整失败，但继续处理")
                else:
                    print(f"⚠️ 页面识别置信度较低 ({detected_page.confidence:.2f})，但继续处理")

                # 5. 执行页面操作
                print(f"🎬 准备执行页面操作: {detected_page.page_id}")
                result = self.action_executor.execute_page_actions(page_config, self.driver)

                if result == ActionResult.INTERRUPTED:
                    print("🚨 操作被中断，启动智能恢复机制...")
                    # 智能恢复：重新检测当前页面状态
                    recovery_result = self._smart_recovery_after_interruption()
                    if recovery_result == "continue":
                        print("✅ 智能恢复成功，继续当前页面操作")
                        continue
                    elif recovery_result == "adjust":
                        print("🔄 检测到用户导航，调整工作流状态")
                        # 重新检测页面并调整状态
                        continue
                    else:
                        print("❌ 智能恢复失败")
                        return False
                elif result == ActionResult.FAILED:
                    print("❌ 页面操作执行失败")
                    return False
                elif result == ActionResult.SUCCESS:
                    print("✅ 页面操作执行成功")

                # 6. 等待页面跳转（如果需要）
                next_pages = page_config.get("next_pages", [])
                if next_pages:
                    print(f"⏳ 等待页面跳转到: {next_pages}")
                    if not self._wait_for_page_transition(next_pages):
                        print("⚠️ 页面跳转超时，但继续流程")

                # 7. 推进工作流程状态
                self.workflow.advance_to_next_state()

            except Exception as e:
                print(f"❌ 工作流程执行异常: {e}")
                return False

        print("\n🎉 工作流程执行完成！")
        return True

    def _adjust_workflow_state(self, actual_page_id: str):
        """调整工作流程状态以匹配实际页面（增强版）"""
        try:
            if actual_page_id in self.workflow.page_sequence:
                actual_index = self.workflow.page_sequence.index(actual_page_id)
                old_index = self.workflow.current_page_index
                self.workflow.current_page_index = actual_index

                if actual_index < old_index:
                    print(f"🔄 检测到页面回退: 从位置{old_index} -> {actual_index} ({actual_page_id})")
                elif actual_index > old_index:
                    print(f"🔄 检测到页面跳跃: 从位置{old_index} -> {actual_index} ({actual_page_id})")
                else:
                    print(f"🔄 工作流程状态确认: {actual_page_id}")

                print(f"✅ 工作流程状态已智能调整到: {actual_page_id}")
                return True
        except ValueError:
            print(f"⚠️ 无法调整工作流程状态，页面不在序列中: {actual_page_id}")
            return False

    def _wait_for_page_transition(self, expected_pages: List[str]) -> bool:
        """等待页面跳转（增强版 - 智能轮询）"""
        start_time = time.time()
        check_count = 0

        print(f"⏳ 开始智能轮询等待页面跳转到: {expected_pages}")

        while time.time() - start_time < self.page_transition_timeout:
            try:
                check_count += 1
                current_url = self.driver.current_url
                current_title = self.driver.title

                # 首先尝试标准识别
                detected_page = self.page_detector.identify_page(current_url, current_title)

                if detected_page.page_id in expected_pages:
                    print(f"✅ 页面跳转成功: {detected_page.page_id} (第{check_count}次检查)")
                    return True

                # 如果标准识别失败，尝试兜底识别
                if detected_page.page_id == "unknown":
                    for expected_page_id in expected_pages:
                        fallback_detected = self.page_detector.identify_page_with_fallback(
                            current_url, current_title, expected_page_id
                        )
                        if fallback_detected.page_id == expected_page_id:
                            print(f"✅ 页面跳转成功（兜底识别）: {expected_page_id} (第{check_count}次检查)")
                            return True

                # 智能轮询间隔（随机时间）
                wait_time = random.uniform(1.5, 3.0)
                elapsed = time.time() - start_time
                print(f"⏳ 第{check_count}次检查未找到目标页面，{wait_time:.1f}秒后重试... (已等待{elapsed:.1f}s)")
                time.sleep(wait_time)

            except Exception as e:
                print(f"⚠️ 页面跳转检测异常: {e}")
                time.sleep(random.uniform(2.0, 4.0))

        print(f"⏰ 页面跳转等待超时 ({self.page_transition_timeout}s，共检查{check_count}次)")
        return False

    def _smart_recovery_after_interruption(self) -> str:
        """中断后的智能恢复机制 - 用户行为适应核心"""
        try:
            print("🧠 启动智能恢复分析...")

            # 等待页面稳定
            time.sleep(2.0)

            # 重新检测页面
            current_url = self.driver.current_url
            current_title = self.driver.title
            detected_page = self.page_detector.identify_page_with_fallback(
                current_url, current_title
            )

            if detected_page.page_id == "unknown":
                print("❌ 无法识别当前页面")
                return "failed"

            # 获取当前期望的页面
            expected_page = self.workflow.get_expected_page()
            expected_page_id = expected_page.get("id") if expected_page else None

            print(f"🔍 恢复分析结果:")
            print(f"   期望页面: {expected_page_id}")
            print(f"   实际页面: {detected_page.page_id}")
            print(f"   置信度: {detected_page.confidence}")

            if detected_page.page_id == expected_page_id:
                print("✅ 页面符合期望，可能是临时DOM更新导致的中断")
                return "continue"

            elif self._is_user_navigation(detected_page.page_id, expected_page_id):
                print(f"🎯 检测到用户手动导航: {expected_page_id} -> {detected_page.page_id}")

                # 检查是否是合理的用户导航（在工作流序列中）
                if self._is_valid_user_navigation(detected_page.page_id):
                    print("✅ 用户导航合理，调整工作流状态")
                    # 调整工作流状态以适应用户行为
                    if self._adjust_workflow_state(detected_page.page_id):
                        return "adjust"
                    else:
                        print("⚠️ 工作流状态调整失败，但继续尝试")
                        return "continue"
                else:
                    print("⚠️ 用户导航到未知页面，尝试适应")
                    return "continue"

            elif detected_page.confidence >= 0.6:
                print("🔄 检测到页面自然跳转，调整工作流状态")
                if self._adjust_workflow_state(detected_page.page_id):
                    return "adjust"
                else:
                    return "continue"

            else:
                print("❓ 页面状态不明确，保守继续")
                return "continue"

        except Exception as e:
            print(f"❌ 智能恢复异常: {e}")
            return "failed"

    def _is_user_navigation(self, actual_page_id: str, expected_page_id: str) -> bool:
        """判断是否是用户手动导航"""
        # 检查页面是否在工作流序列中但不是当前期望的页面
        if actual_page_id in self.workflow.page_sequence and actual_page_id != expected_page_id:
            # 进一步检查：是否是回退导航
            actual_index = self.workflow.page_sequence.index(actual_page_id)
            current_index = self.workflow.current_page_index

            if actual_index < current_index:
                print(f"🔙 检测到用户回退导航: 从位置{current_index} -> {actual_index}")
                return True
            elif actual_index > current_index + 1:
                print(f"⏭️ 检测到用户跳跃导航: 从位置{current_index} -> {actual_index}")
                return True

        return False

    def _is_valid_user_navigation(self, page_id: str) -> bool:
        """检查用户导航是否合理"""
        # 检查页面是否在工作流序列中
        return page_id in self.workflow.page_sequence

    def _get_user_navigation_strategy(self, actual_page_id: str) -> str:
        """获取用户导航的适应策略"""
        try:
            actual_index = self.workflow.page_sequence.index(actual_page_id)
            current_index = self.workflow.current_page_index

            if actual_index < current_index:
                return "backward"  # 用户回退
            elif actual_index > current_index:
                return "forward"   # 用户前进
            else:
                return "current"   # 当前页面

        except ValueError:
            return "unknown"      # 未知页面

    def _wait_for_page_change_after_exit(self) -> bool:
        """退出后等待页面变化"""
        print("🔄 进入页面变化监控模式...")
        initial_url = self.driver.current_url
        initial_title = self.driver.title
        start_time = time.time()
        timeout = 60  # 60秒超时

        while time.time() - start_time < timeout:
            try:
                current_url = self.driver.current_url
                current_title = self.driver.title

                # 检查页面是否变化
                if current_url != initial_url or current_title != initial_title:
                    print(f"📄 检测到页面变化: {initial_url} -> {current_url}")
                    return True

                # 检查控制面板状态
                if self.enable_control_panel and self.control_panel:
                    if not self.control_panel.is_paused.is_set():
                        print("⏸️ 页面变化等待已暂停")
                        self.control_panel.is_paused.wait()
                        print("▶️ 页面变化等待已恢复")

                time.sleep(2)  # 轮询间隔

            except Exception as e:
                print(f"⚠️ 页面变化检测异常: {e}")
                time.sleep(2)

        return False


# ==================== 工具函数 ====================

def create_page_context(driver: webdriver.Chrome, page_id: str) -> PageContext:
    """创建页面上下文"""
    return PageContext(
        current_url=driver.current_url,
        page_title=driver.title,
        page_id=page_id,
        driver=driver
    )


def random_delay(min_seconds: float = 0.5, max_seconds: float = 2.0):
    """随机延迟"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


# ==================== 异常类 ====================

class WebAutomationError(Exception):
    """Web自动化异常基类"""
    pass


class UnsupportedActionError(WebAutomationError):
    """不支持的操作类型异常"""
    pass


class PageDetectionError(WebAutomationError):
    """页面检测异常"""
    pass


class WorkflowExecutionError(WebAutomationError):
    """工作流程执行异常"""
    pass


if __name__ == "__main__":
    print("Web自动化框架已加载")
    print("使用方法：")
    print("1. 创建工作流程配置")
    print("2. 实例化 WebAutomationFramework")
    print("3. 设置 WebDriver")
    print("4. 调用 execute_workflow()")