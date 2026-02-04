import time
import sys
from pywinauto import Application
from pywinauto.keyboard import send_keys

# 全局超时设置
CONNECT_TIMEOUT = 30
WINDOW_TIMEOUT = 60


def connect_to_install_window():
    """连接到安装提醒窗口"""
    print("Connecting to install prompt window...")

    # 尝试连接到"安装"窗口
    connection_methods = [
        lambda: Application(backend="uia").connect(title="安装", timeout=5),
        lambda: Application(backend="win32").connect(title="安装", timeout=5),
    ]

    for i, method in enumerate(connection_methods, 1):
        try:
            print(f"Trying connection method {i}...")
            app = method()
            print(f"Connected to install window! PID: {app.process}")
            return app
        except Exception as e:
            print(f"Method {i} failed: {str(e)[:50]}...")
            continue

    print("Failed to connect to install window")
    return None

def wait_for_control(app, criteria, timeout=WINDOW_TIMEOUT):
    """通用控件查找（支持 class_name, control_type, name 等）"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            ctrl = app.top_window_().child_window(**criteria)
            if ctrl.exists() and ctrl.is_visible():
                ctrl.set_focus()
                print(f"[Success] Found control: {criteria}")
                return ctrl
            # 尝试所有顶级窗口
            for win in app.windows():
                try:
                    ctrl = win.child_window(**criteria)
                    if ctrl.exists() and ctrl.is_visible():
                        win.set_focus()
                        ctrl.set_focus()
                        print(f"[Success] Found control in window: {win.window_text()}")
                        return ctrl
                except:
                    continue
        except:
            pass
        time.sleep(0.8)
    print(f"[Failed] Control not found: {criteria}")
    return None

def click_button_by_text(text):
    """点击文本为指定内容的按钮"""
    return wait_for_control(app, {
        "control_type": "Button",
        "title": text,
        "visible_only": True
    })

def click_button_by_class(class_name):
    """点击 class_name 的按钮"""
    return wait_for_control(app, {
        "class_name": class_name,
        "control_type": "Button"
    })

def select_radio_by_name(name):
    """选择单选框"""
    return wait_for_control(app, {
        "control_type": "RadioButton",
        "name": name
    })

# 临时调试：打印所有控件
def dump_controls():
    for win in app.windows():
        print(f"\n--- Window: {win.window_text()} ---")
        try:
            win.print_control_identifiers()
        except:
            pass

def main():
    print("Starting kiro installation automation...")

    global app

    # === 步骤 1：处理"安装"提醒窗口 ===
    print("\n=== Step 1: Handle Install Prompt Window ===")
    app = connect_to_install_window()
    if not app:
        print("Failed to connect to install prompt window")
        return

    # 查找并点击"确定"按钮 (ID: 1)
    print("Looking for '确定' button...")
    try:
        window = app.top_window()
        print(f"Window title: '{window.window_text()}'")

        # 根据分析结果，确定按钮的ID是1，类名是Button
        confirm_button = window.child_window(auto_id="1", class_name="Button")

        if confirm_button.exists() and confirm_button.is_visible():
            print("Found '确定' button, clicking...")
            try:
                # 确保窗口有焦点
                window.set_focus()
                time.sleep(0.5)

                # 使用方法1：普通点击（已验证有效）
                confirm_button.click()
                print("Click executed, waiting for window change...")

                # 等待更长时间并检查窗口变化
                for i in range(10):  # 等待最多10秒
                    time.sleep(1)
                    try:
                        # 检查原窗口是否还存在
                        if not window.exists():
                            print(f"✅ Original window closed after {i+1} seconds")
                            break
                        # 检查窗口标题是否改变
                        current_title = window.window_text()
                        if current_title != "安装":
                            print(f"✅ Window title changed to: '{current_title}'")
                            break
                    except:
                        print(f"✅ Window changed after {i+1} seconds")
                        break

                    if i == 9:
                        print("⚠️ Window didn't change after 10 seconds, but click was executed")

                print("✅ Successfully clicked '确定' button!")

            except Exception as e:
                print(f"❌ Click failed: {e}")
                return

        else:
            print("❌ '确定' button not found or not visible")
            return

    except Exception as e:
        print(f"❌ Error handling install prompt: {e}")
        return

    print("✅ Step 1 completed - should now be in license agreement window")

    # === 步骤 2：处理许可协议界面 ===
    print("\n=== Step 2: Handle License Agreement Window ===")

    # 重新连接到协议窗口
    print("Connecting to license agreement window...")

    # 等待协议窗口出现
    print("Waiting for license window to appear...")
    time.sleep(2)

    # 连接协议窗口（使用方法3：win32 + 正则匹配）
    try:
        print("Connecting to license window...")
        license_app = Application(backend="win32").connect(title_re=".*安装.*Kiro.*", timeout=10)
        print(f"✅ Connected to license window! PID: {license_app.process}")
    except Exception as e:
        print(f"❌ Failed to connect to license window: {e}")
        return

    try:
        license_window = license_app.top_window()
        print(f"License window title: '{license_window.window_text()}'")

        # 步骤2.1：点击"我同意此协议"单选框（使用方法4：第一个单选框）
        print("Looking for '我同意此协议' radio button...")
        try:
            agree_radio = license_window.child_window(class_name="TNewRadioButton", found_index=0)
            if agree_radio.exists() and agree_radio.is_visible():
                radio_text = agree_radio.window_text() or "[无文本]"
                print(f"✅ Found radio button: '{radio_text}'")
                agree_radio.click()
                print("✅ Successfully clicked '我同意此协议'!")
                time.sleep(1)  # 等待界面更新
            else:
                print("❌ '我同意此协议' radio button not found")
                return
        except Exception as e:
            print(f"❌ Error clicking radio button: {e}")
            return

        # 步骤2.2：点击"下一步"按钮
        print("Looking for '下一步' button...")

        # 等待按钮启用（选择协议后按钮会启用）
        time.sleep(1)

        # 点击"下一步"按钮（使用方法4：第一个按钮）
        try:
            next_button = license_window.child_window(class_name="TNewButton", found_index=0)
            if next_button.exists() and next_button.is_visible() and next_button.is_enabled():
                button_text = next_button.window_text() or "[无文本]"
                print(f"✅ Found button: '{button_text}'")
                next_button.click()
                print("✅ Successfully clicked '下一步' button!")
                time.sleep(3)  # 等待进入下一个安装步骤
            else:
                print("❌ '下一步' button not found or disabled")
                return
        except Exception as e:
            print(f"❌ Error clicking next button: {e}")
            return

        print("✅ Step 2 completed - should now be in next installation step")

    except Exception as e:
        print(f"❌ Error in Step 2: {e}")
        return

    print("🎉 Second step automation finished!")

    # === 步骤 3：处理选择目标位置界面 ===
    print("\n=== Step 3: Handle Target Location Selection ===")

    # 等待目标位置界面出现
    print("Waiting for target location window to appear...")
    time.sleep(2)

    # 连接到安装窗口（使用成功的方法5）
    try:
        print("Connecting to target location window...")
        target_app = Application(backend="uia").connect(title_re=".*安装.*", timeout=10)
        print(f"✅ Connected to target location window! PID: {target_app.process}")
    except Exception as e:
        print(f"❌ Failed to connect to target location window: {e}")
        return

    # 获取窗口
    try:
        target_window = target_app.windows()[0]  # 直接获取第一个窗口
        print(f"✅ Got window: '{target_window.window_text()}'")
    except Exception as e:
        print(f"❌ Failed to get window: {e}")
        return

    # 查找并点击"下一步"按钮
    try:
        print("Looking for '下一步' button...")
        controls = target_window.descendants()

        # 通过类名和文本查找按钮（最有效的方法）
        for ctrl in controls:
            try:
                if (ctrl.class_name() == "TNewButton" and "下一步" in ctrl.window_text()):
                    print(f"✅ Found button: '{ctrl.window_text()}'")
                    ctrl.click()
                    print("✅ Successfully clicked '下一步' button!")
                    time.sleep(3)
                    break
            except:
                continue
        else:
            print("❌ '下一步' button not found")
            return

        print("✅ Step 3 completed - should now be in next installation step")

    except Exception as e:
        print(f"❌ Error in Step 3: {e}")
        return

    # === 步骤 4：处理选择开始菜单文件夹界面 ===
    print("\n=== Step 4: Handle Start Menu Folder Selection ===")

    # 等待开始菜单文件夹界面出现
    print("Waiting for start menu folder window to appear...")
    time.sleep(2)

    # 连接到安装窗口（使用成功的方法5）
    try:
        print("Connecting to start menu folder window...")
        menu_app = Application(backend="uia").connect(title_re=".*安装.*", timeout=10)
        print(f"✅ Connected to start menu folder window! PID: {menu_app.process}")
    except Exception as e:
        print(f"❌ Failed to connect to start menu folder window: {e}")
        return

    # 获取窗口
    try:
        menu_window = menu_app.windows()[0]  # 直接获取第一个窗口
        print(f"✅ Got window: '{menu_window.window_text()}'")
    except Exception as e:
        print(f"❌ Failed to get window: {e}")
        return

    # 查找并点击"下一步"按钮
    try:
        print("Looking for '下一步' button...")
        controls = menu_window.descendants()

        # 通过类名和文本查找按钮（使用第三步成功的方法）
        for ctrl in controls:
            try:
                if (ctrl.class_name() == "TNewButton" and "下一步" in ctrl.window_text()):
                    print(f"✅ Found button: '{ctrl.window_text()}'")
                    ctrl.click()
                    print("✅ Successfully clicked '下一步' button!")
                    time.sleep(3)
                    break
            except:
                continue
        else:
            print("❌ '下一步' button not found")
            return

        print("✅ Step 4 completed - should now be in next installation step")

    except Exception as e:
        print(f"❌ Error in Step 4: {e}")
        return

    # === 步骤 5：处理选择附加任务界面 ===
    print("\n=== Step 5: Handle Additional Tasks Selection ===")

    # 等待附加任务界面出现
    print("Waiting for additional tasks window to appear...")
    time.sleep(2)

    # 连接到安装窗口（使用成功的方法5）
    try:
        print("Connecting to additional tasks window...")
        tasks_app = Application(backend="uia").connect(title_re=".*安装.*", timeout=10)
        print(f"✅ Connected to additional tasks window! PID: {tasks_app.process}")
    except Exception as e:
        print(f"❌ Failed to connect to additional tasks window: {e}")
        return

    # 获取窗口
    try:
        tasks_window = tasks_app.windows()[0]  # 直接获取第一个窗口
        print(f"✅ Got window: '{tasks_window.window_text()}'")
    except Exception as e:
        print(f"❌ Failed to get window: {e}")
        return

    # 查找并点击"下一步"按钮（使用默认的附加任务设置）
    try:
        print("Looking for '下一步' button...")
        controls = tasks_window.descendants()

        # 通过类名和文本查找按钮（使用前面步骤成功的方法）
        for ctrl in controls:
            try:
                if (ctrl.class_name() == "TNewButton" and "下一步" in ctrl.window_text()):
                    print(f"✅ Found button: '{ctrl.window_text()}'")
                    ctrl.click()
                    print("✅ Successfully clicked '下一步' button!")
                    time.sleep(3)
                    break
            except:
                continue
        else:
            print("❌ '下一步' button not found")
            return

        print("✅ Step 5 completed - should now be in next installation step")

    except Exception as e:
        print(f"❌ Error in Step 5: {e}")
        return

    # === 步骤 6：处理准备安装界面 ===
    print("\n=== Step 6: Handle Ready to Install ===")

    # 等待准备安装界面出现
    print("Waiting for ready to install window to appear...")
    time.sleep(2)

    # 连接到安装窗口（使用成功的方法5）
    try:
        print("Connecting to ready to install window...")
        install_app = Application(backend="uia").connect(title_re=".*安装.*", timeout=10)
        print(f"✅ Connected to ready to install window! PID: {install_app.process}")
    except Exception as e:
        print(f"❌ Failed to connect to ready to install window: {e}")
        return

    # 获取窗口
    try:
        install_window = install_app.windows()[0]  # 直接获取第一个窗口
        print(f"✅ Got window: '{install_window.window_text()}'")
    except Exception as e:
        print(f"❌ Failed to get window: {e}")
        return

    # 查找并点击"安装"按钮
    try:
        print("Looking for '安装' button...")
        controls = install_window.descendants()

        # 通过类名和文本查找安装按钮
        for ctrl in controls:
            try:
                if (ctrl.class_name() == "TNewButton" and "安装" in ctrl.window_text()):
                    print(f"✅ Found button: '{ctrl.window_text()}'")
                    ctrl.click()
                    print("✅ Successfully clicked '安装' button!")
                    print("🚀 Installation started! This may take a few minutes...")
                    time.sleep(5)  # 等待安装开始
                    break
            except:
                continue
        else:
            print("❌ '安装' button not found")
            return

        print("✅ Step 6 completed - installation process started")

    except Exception as e:
        print(f"❌ Error in Step 6: {e}")
        return

    # === 步骤 7：等待安装完成并点击完成按钮 ===
    print("\n=== Step 7: Wait for Installation to Complete ===")
    print("⏳ Waiting for installation to complete...")

    # 等待安装完成（通过检测"Kiro 安装完成"文本）
    max_wait_time = 300  # 最多等待5分钟
    wait_interval = 5    # 每5秒检查一次（更频繁的检查）

    for i in range(0, max_wait_time, wait_interval):
        time.sleep(wait_interval)
        print(f"⏳ Installation in progress... ({i + wait_interval}s elapsed)")

        # 检查是否出现"Kiro 安装完成"界面
        try:
            # 连接到安装窗口
            complete_app = Application(backend="uia").connect(title_re=".*安装.*", timeout=5)
            complete_window = complete_app.windows()[0]
            print(f"🔍 Connected to window: '{complete_window.window_text()}'")

            # 查找"Kiro 安装完成"文本
            controls = complete_window.descendants()
            print(f"🔍 Found {len(controls)} controls to check")

            installation_completed = False

            # 调试：打印所有TNewStaticText控件的文本
            static_texts = []
            for ctrl in controls:
                try:
                    if ctrl.class_name() == "TNewStaticText":
                        text = ctrl.window_text()
                        static_texts.append(text)
                        print(f"🔍 TNewStaticText: '{text}'")

                        if "Kiro 安装完成" in text:  # 使用包含检查，忽略换行符
                            print("✅ Found 'Kiro 安装完成' text!")
                            installation_completed = True
                            break
                except:
                    continue

            if not installation_completed:
                print(f"⚠️ 'Kiro 安装完成' not found. Found {len(static_texts)} TNewStaticText controls")
                continue

            print("✅ Installation completed!")

            # 查找并点击"完成"按钮
            print("Looking for '完成' button...")
            button_found = False

            # 调试：打印所有TNewButton控件
            buttons = []
            for ctrl in controls:
                try:
                    if ctrl.class_name() == "TNewButton":
                        btn_text = ctrl.window_text()
                        buttons.append(btn_text)
                        print(f"🔍 TNewButton: '{btn_text}'")

                        if "完成" in btn_text:
                            print(f"✅ Found button: '{btn_text}'")
                            ctrl.click()
                            print("✅ Successfully clicked '完成' button!")
                            print("🎉 Kiro has been successfully installed and setup completed!")
                            button_found = True

                            # 等待 Kiro 启动并调用登录自动化脚本
                            print("\n⏳ 等待 Kiro 应用程序启动...")
                            print("💡 等待登录界面完全加载...")

                            # 智能等待：检测登录界面是否真正准备就绪
                            max_wait_time = 30  # 最多等待30秒
                            wait_interval = 3   # 每3秒检查一次
                            login_ready = False

                            for elapsed in range(0, max_wait_time, wait_interval):
                                time.sleep(wait_interval)
                                print(f"⏳ 检查登录界面状态... ({elapsed + wait_interval}s)")

                                try:
                                    test_app = Application(backend="uia").connect(title_re=".*Kiro.*", timeout=3)
                                    test_window = test_app.windows()[0]
                                    controls = test_window.descendants()
                                    control_count = len(controls)
                                    window_title = test_window.window_text()

                                    print(f"   窗口标题: '{window_title}', 控件数: {control_count}")

                                    # 检查是否是完整的登录界面
                                    if control_count > 100 and "Getting started" in window_title:
                                        # 进一步检查是否有登录按钮
                                        has_login_buttons = False
                                        for ctrl in controls:
                                            try:
                                                ctrl_name = getattr(ctrl.element_info, 'name', '') if hasattr(ctrl, 'element_info') else ''
                                                if "Sign in with" in ctrl_name:
                                                    has_login_buttons = True
                                                    break
                                            except:
                                                continue

                                        if has_login_buttons:
                                            login_ready = True
                                            print(f"✅ 登录界面已完全准备就绪！")
                                            break
                                        else:
                                            print(f"   界面加载中，等待登录按钮出现...")
                                    else:
                                        print(f"   界面还在加载中...")

                                except Exception as e:
                                    print(f"   等待应用程序响应... ({str(e)[:30]}...)")

                            if not login_ready:
                                print("⚠️ 等待超时，但继续尝试启动登录脚本...")
                            else:
                                print("🎯 界面准备就绪，启动登录脚本...")

                            # Kiro安装完成，等待用户操作
                            print("🎉 Kiro安装完成！")
                            print("💡 您现在可以手动操作Kiro应用程序")
                            print("📝 如需自动登录，请手动运行: python kiro_login_automation.py")
                            print("⏳ 安装脚本将保持运行状态...")

                            return
                except Exception as e:
                    print(f"🔍 Button check error: {e}")
                    continue

            print(f"🔍 Found {len(buttons)} TNewButton controls: {buttons}")

            if not button_found:
                print("⚠️ Installation completed but could not find '完成' button")
                print("🎉 Kiro has been successfully installed!")

                # 即使没找到完成按钮，也尝试启动登录自动化
                print("\n⏳ 等待 Kiro 应用程序完全启动...")
                print("💡 等待登录界面完全加载（这可能需要15-30秒）...")

                # 智能等待：检测登录界面是否真正准备就绪
                max_wait_time = 30  # 最多等待30秒
                wait_interval = 3   # 每3秒检查一次
                login_ready = False

                for elapsed in range(0, max_wait_time, wait_interval):
                    time.sleep(wait_interval)
                    print(f"⏳ 检查登录界面状态... ({elapsed + wait_interval}s)")

                    try:
                        test_app = Application(backend="uia").connect(title_re=".*Kiro.*", timeout=3)
                        test_window = test_app.windows()[0]
                        controls = test_window.descendants()
                        control_count = len(controls)
                        window_title = test_window.window_text()

                        print(f"   窗口标题: '{window_title}', 控件数: {control_count}")

                        # 检查是否是完整的登录界面
                        if control_count > 100 and "Getting started" in window_title:
                            # 进一步检查是否有登录按钮
                            has_login_buttons = False
                            for ctrl in controls:
                                try:
                                    ctrl_name = getattr(ctrl.element_info, 'name', '') if hasattr(ctrl, 'element_info') else ''
                                    if "Sign in with" in ctrl_name:
                                        has_login_buttons = True
                                        break
                                except:
                                    continue

                            if has_login_buttons:
                                login_ready = True
                                print(f"✅ 登录界面已完全准备就绪！")
                                break
                            else:
                                print(f"   界面加载中，等待登录按钮出现...")
                        else:
                            print(f"   界面还在加载中...")

                    except Exception as e:
                        print(f"   等待应用程序响应... ({str(e)[:30]}...)")

                if not login_ready:
                    print("⚠️ 等待超时，但继续尝试启动登录脚本...")
                else:
                    print("🎯 界面准备就绪，启动登录脚本...")

                # Kiro安装完成，等待用户操作
                print("🎉 Kiro安装完成！")
                print("💡 您现在可以手动操作Kiro应用程序")
                print("📝 如需自动登录，请手动运行: python kiro_login_automation.py")

                # 启动辅助工具
                print("\n🚀 启动辅助工具...")

                # 启动VirtualBrowser
                try:
                    virtual_browser_path = r"C:\Program Files\VirtualBrowser\VirtualBrowser.exe"
                    if os.path.exists(virtual_browser_path):
                        print("🌐 启动VirtualBrowser...")
                        subprocess.Popen([virtual_browser_path], shell=True)
                        print("✅ VirtualBrowser已启动")
                    else:
                        print("⚠️ VirtualBrowser未找到")
                except Exception as e:
                    print(f"❌ 启动VirtualBrowser失败: {e}")

                # 启动注册信息生成器
                try:
                    reg_generator_path = r"C:\sandbox_files\dist\RegistrationInfoGenerator_v2.exe"
                    if os.path.exists(reg_generator_path):
                        print("🎯 启动注册信息生成器...")
                        subprocess.Popen([reg_generator_path], cwd=r"C:\sandbox_files\dist", shell=True)
                        print("✅ 注册信息生成器已启动")
                    else:
                        print("⚠️ 注册信息生成器未找到")
                except Exception as e:
                    print(f"❌ 启动注册信息生成器失败: {e}")

                print("🎉 所有辅助工具启动完成！")
                print("\n⏳ 安装脚本将保持运行状态...")
                return

        except Exception as e:
            # 如果连接失败，可能安装还在进行中
            print(f"🔍 Connection attempt failed: {str(e)[:50]}...")
            continue

    print("⚠️ Installation may still be in progress after 5 minutes")
    print("🎉 Automation completed! Please check the installation status manually.")

    # 启动辅助工具（无论安装状态如何都尝试启动）
    print("\n🚀 启动辅助工具...")

    # 启动VirtualBrowser
    try:
        virtual_browser_path = r"C:\Program Files\VirtualBrowser\VirtualBrowser.exe"
        if os.path.exists(virtual_browser_path):
            print("🌐 启动VirtualBrowser...")
            subprocess.Popen([virtual_browser_path], shell=True)
            print("✅ VirtualBrowser已启动")
        else:
            print("⚠️ VirtualBrowser未找到")
    except Exception as e:
        print(f"❌ 启动VirtualBrowser失败: {e}")

    # 启动注册信息生成器
    try:
        reg_generator_path = r"C:\sandbox_files\dist\RegistrationInfoGenerator_v2.exe"
        if os.path.exists(reg_generator_path):
            print("🎯 启动注册信息生成器...")
            subprocess.Popen([reg_generator_path], cwd=r"C:\sandbox_files\dist", shell=True)
            print("✅ 注册信息生成器已启动")
        else:
            print("⚠️ 注册信息生成器未找到")
    except Exception as e:
        print(f"❌ 启动注册信息生成器失败: {e}")

    print("🎉 所有辅助工具启动完成！")


if __name__ == "__main__":
    main()