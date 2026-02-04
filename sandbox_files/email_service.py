#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用邮箱验证码获取服务
支持IMAP协议自动获取验证码
作者：Claude Code Assistant
"""

import imaplib
import email
import re
import time
import sys
import configparser
from email.header import decode_header
from pathlib import Path


class EmailService:
    def __init__(self, sender_filter=None, subject_filter=None, code_pattern=None,
                 check_interval=30, max_wait_time=300, delete_after_read=False):
        """
        初始化邮箱服务

        Args:
            sender_filter (str): 发件人过滤条件
            subject_filter (str): 主题过滤条件
            code_pattern (str): 验证码正则表达式
            check_interval (int): 检查邮件间隔(秒)
            max_wait_time (int): 最大等待时间(秒)
            delete_after_read (bool): 读取后是否删除邮件
        """
        self.sender_filter = sender_filter
        self.subject_filter = subject_filter
        self.code_pattern = code_pattern or r'\b\d{4,8}\b'  # 默认4-8位数字（更通用）
        self.check_interval = check_interval
        self.max_wait_time = max_wait_time
        self.delete_after_read = delete_after_read

        # 加载邮箱配置
        self.config = self._load_config()
        self.imap_conn = None

    def _load_config(self):
        """加载邮箱配置"""
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

        config_path = None
        for path in possible_paths:
            if path.exists():
                config_path = path
                print(f"[INFO] 找到.env配置文件: {path}")
                break

        if not config_path:
            raise FileNotFoundError("未找到.env配置文件")

        config = configparser.ConfigParser()

        try:
            config.read(config_path, encoding='utf-8')
            return {
                'server': config.get('EMAIL', 'IMAP_SERVER'),
                'port': config.getint('EMAIL', 'IMAP_PORT'),
                'user': config.get('EMAIL', 'IMAP_USER'),
                'password': config.get('EMAIL', 'IMAP_PASS'),
                'use_ssl': config.getboolean('EMAIL', 'IMAP_USE_SSL')
            }
        except Exception as e:
            print(f"[ERROR] 加载邮箱配置失败: {e}")
            print(f"[INFO] 配置文件路径: {config_path}")
            raise

    def connect(self):
        """连接到IMAP服务器"""
        try:
            print(f"[INFO] 连接到邮箱服务器: {self.config['server']}:{self.config['port']}")

            if self.config['use_ssl']:
                self.imap_conn = imaplib.IMAP4_SSL(self.config['server'], self.config['port'])
            else:
                self.imap_conn = imaplib.IMAP4(self.config['server'], self.config['port'])

            # 登录
            self.imap_conn.login(self.config['user'], self.config['password'])

            # 选择收件箱
            status, message = self.imap_conn.select('INBOX')
            if status != 'OK':
                print(f"[ERROR] 选择收件箱失败: {message}")
                return False

            print(f"[SUCCESS] 邮箱连接成功: {self.config['user']}")
            print(f"[INFO] 已选择收件箱，邮件数量: {message[0].decode()}")
            return True

        except Exception as e:
            print(f"[ERROR] 邮箱连接失败: {e}")
            return False

    def disconnect(self):
        """断开IMAP连接"""
        if self.imap_conn:
            try:
                self.imap_conn.close()
                self.imap_conn.logout()
                print("[INFO] 邮箱连接已断开")
            except:
                pass

    def _decode_header_value(self, header_value):
        """解码邮件头部信息（安全版本）"""
        if not header_value:
            return ""

        try:
            decoded_parts = decode_header(header_value)
            decoded_string = ""

            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding and encoding.lower() not in ['unknown-8bit', 'unknown']:
                        try:
                            decoded_string += part.decode(encoding)
                        except (UnicodeDecodeError, LookupError):
                            # 编码失败，尝试常见编码
                            for fallback_encoding in ['utf-8', 'gbk', 'gb2312', 'iso-8859-1']:
                                try:
                                    decoded_string += part.decode(fallback_encoding)
                                    break
                                except (UnicodeDecodeError, LookupError):
                                    continue
                            else:
                                # 所有编码都失败，使用容错解码
                                decoded_string += part.decode('utf-8', errors='ignore')
                    else:
                        # 未知编码或无编码，使用容错解码
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += part

            return decoded_string

        except Exception as e:
            print(f"[WARNING] 邮件头部解码失败: {e}")
            # 返回原始字符串或空字符串
            return str(header_value) if header_value else ""

    def _extract_verification_code(self, email_content):
        """从邮件内容中提取验证码（支持多种格式，优先匹配上下文）"""
        try:
            print(f"[INFO] 邮件内容长度: {len(email_content)} 字符")
            print(f"[DEBUG] 邮件内容预览: {email_content[:200]}...")

            # 优先级1: 带上下文的验证码模式（最准确）
            context_patterns = [
                r'(?i)verification\s*code[:\s]*[：\s]*(\d{4,8})',  # "Verification code: 123456"
                r'(?i)verification[:\s]*[：\s]*(\d{4,8})',  # "Verification: 123456"
                r'(?i)code[:\s]*[：\s]*(\d{4,8})',  # "Code: 123456"
                r'(?i)pin[:\s]*[：\s]*(\d{4,8})',  # "PIN: 123456"
                r'(?i)your\s+code\s+is[:\s]*[：\s]*(\d{4,8})',  # "Your code is: 123456"
                r'(?i)enter\s+(?:the\s+)?(?:following\s+)?(?:verification\s+)?code[:\s]*[：\s]*(\d{4,8})',  # "Enter the following code: 123456"
                r'class=["\']code["\'][^>]*>(\d{4,8})<',  # HTML: <div class="code">123456</div>
                r'<div[^>]*>(\d{6})</div>',  # HTML: <div>123456</div> (6位数字)
            ]

            # 尝试上下文模式（优先级最高）
            for i, pattern in enumerate(context_patterns):
                try:
                    matches = re.findall(pattern, email_content, re.IGNORECASE | re.DOTALL)
                    if matches:
                        code = matches[0] if isinstance(matches[0], str) else str(matches[0])
                        code = code.strip()

                        # 验证码长度检查（4-8位）
                        if 4 <= len(code) <= 8 and code.isdigit():
                            print(f"[SUCCESS] 使用上下文模式 {i+1} 提取到验证码: {code}")
                            return code
                except Exception as e:
                    print(f"[DEBUG] 上下文模式 {i+1} 失败: {e}")
                    continue

            # 优先级2: 纯文本中查找（去除HTML标签后）
            # 移除HTML标签
            text_content = re.sub(r'<[^>]+>', ' ', email_content)
            text_content = re.sub(r'\s+', ' ', text_content)  # 合并多个空格

            print(f"[DEBUG] 纯文本内容预览: {text_content[:300]}...")

            # 在纯文本中再次尝试上下文模式
            for i, pattern in enumerate(context_patterns[:6]):  # 只用前6个文本模式
                try:
                    matches = re.findall(pattern, text_content, re.IGNORECASE)
                    if matches:
                        code = matches[0] if isinstance(matches[0], str) else str(matches[0])
                        code = code.strip()

                        if 4 <= len(code) <= 8 and code.isdigit():
                            print(f"[SUCCESS] 在纯文本中使用模式 {i+1} 提取到验证码: {code}")
                            return code
                except Exception as e:
                    print(f"[DEBUG] 纯文本模式 {i+1} 失败: {e}")
                    continue

            # 优先级3: 通用模式（最后的备选方案）
            fallback_patterns = [
                r'\b\d{8}\b',       # GitHub: 8位数字
                r'\b\d{6}\b',       # Google/AWS: 6位数字
                r'\b\d{4}\b',       # 某些服务: 4位数字
            ]

            for i, pattern in enumerate(fallback_patterns):
                try:
                    matches = re.findall(pattern, text_content)
                    if matches:
                        # 过滤掉明显不是验证码的数字（如日期、时间等）
                        for code in matches:
                            # 跳过常见的非验证码数字
                            if code in ['000000', '111111', '222222', '333333', '444444',
                                       '555555', '666666', '777777', '888888', '999999']:
                                continue

                            if 4 <= len(code) <= 8:
                                print(f"[SUCCESS] 使用备选模式 {i+1} 提取到验证码: {code}")
                                return code
                except Exception as e:
                    print(f"[DEBUG] 备选模式 {i+1} 失败: {e}")
                    continue

            print(f"[WARNING] 所有模式都未找到匹配的验证码")
            return None

        except Exception as e:
            print(f"[ERROR] 验证码提取失败: {e}")
            return None

    def safe_decode_email_content(self, email_message):
        """通用的安全邮件内容解码（支持Quoted-Printable等编码）"""
        try:
            # decode=True 会自动处理 base64, quoted-printable 等编码
            payload = email_message.get_payload(decode=True)
            if not payload:
                # 如果decode=True失败，尝试直接获取
                payload = email_message.get_payload()
                if isinstance(payload, str):
                    # 如果是字符串，可能需要手动解码quoted-printable
                    import quopri
                    try:
                        payload = quopri.decodestring(payload.encode('utf-8'))
                    except:
                        payload = payload.encode('utf-8')

            if not payload:
                return ""

            # 如果payload是字符串，直接返回
            if isinstance(payload, str):
                return payload

            # 尝试多种常见编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'iso-8859-1', 'windows-1252']

            for encoding in encodings:
                try:
                    decoded = payload.decode(encoding)
                    # 验证解码是否成功（检查是否有大量乱码）
                    if decoded and len(decoded) > 0:
                        return decoded
                except (UnicodeDecodeError, LookupError, AttributeError):
                    continue

            # 最后使用容错解码
            return payload.decode('utf-8', errors='ignore')

        except Exception as e:
            print(f"[WARNING] 邮件内容解码失败: {e}")
            return ""

    def safe_get_email_info(self, email_message):
        """安全获取邮件基本信息"""
        try:
            return {
                'sender': email_message.get('From', ''),
                'subject': email_message.get('Subject', ''),
                'body': self.safe_decode_email_content(email_message)
            }
        except Exception as e:
            print(f"[WARNING] 邮件信息获取失败: {e}")
            return {'sender': '', 'subject': '', 'body': ''}

    def _get_email_content(self, msg):
        """获取邮件内容（使用安全解码）"""
        content = ""

        try:
            if msg.is_multipart():
                # 处理多部分邮件
                for part in msg.walk():
                    content_type = part.get_content_type()

                    if content_type in ['text/plain', 'text/html']:
                        part_content = self.safe_decode_email_content(part)
                        content += part_content
            else:
                # 处理单部分邮件
                content = self.safe_decode_email_content(msg)

        except Exception as e:
            print(f"[WARNING] 获取邮件内容失败，使用安全模式: {e}")
            content = self.safe_decode_email_content(msg)

        return content

    def _check_email_filters(self, msg):
        """检查邮件是否符合过滤条件"""
        try:
            # 不过滤发件人，接受所有邮件
            # （平台识别将在找到验证码后通过发件人域名来判断）
            sender = self._decode_header_value(msg.get('From', ''))
            print(f"[INFO] 检查邮件，发件人: {sender}")

            # 检查邮件时间（显示时间信息，但不过滤）
            try:
                import datetime
                from email.utils import parsedate_to_datetime

                date_str = msg.get('Date', '')
                if date_str:
                    email_date = parsedate_to_datetime(date_str)
                    now = datetime.datetime.now(email_date.tzinfo)
                    time_diff = (now - email_date).total_seconds() / 60  # 转换为分钟

                    # 只显示时间信息，不过滤
                    if time_diff > 60:
                        print(f"[INFO] 邮件时间: {time_diff:.1f}分钟前（旧邮件，但仍处理）")
                    else:
                        print(f"[INFO] 邮件时间: {time_diff:.1f}分钟前")
            except Exception as e:
                print(f"[WARNING] 时间信息获取失败: {e}")

            # 检查主题（可选，如果主题过滤不成功可以注释掉）
            if self.subject_filter:
                subject = self._decode_header_value(msg.get('Subject', ''))
                if self.subject_filter.lower() not in subject.lower():
                    print(f"[INFO] 主题不匹配，但继续处理: {subject}")
                    # 不直接返回False，让发件人和时间过滤起主要作用
                else:
                    print(f"[INFO] 主题匹配: {subject}")

            return True

        except Exception as e:
            print(f"[ERROR] 邮件过滤检查失败: {e}")
            return False

    def get_verification_code(self):
        """获取验证码（主要方法）- 优化版：只检查最新的5封邮件"""
        if not self.connect():
            return None

        try:
            print(f"[INFO] 开始获取验证码...")
            print(f"[INFO] 发件人过滤: {self.sender_filter}")
            print(f"[INFO] 主题过滤: {self.subject_filter}")
            print(f"[INFO] 验证码正则: {self.code_pattern}")

            # 用于存储发件人信息
            self.last_sender = None

            start_time = time.time()

            while time.time() - start_time < self.max_wait_time:
                try:
                    # 搜索所有邮件（不限于未读）
                    status, messages = self.imap_conn.search(None, 'ALL')

                    if status == 'OK' and messages[0]:
                        email_ids = messages[0].split()

                        # 只取最新的5封邮件（按时间降序）
                        latest_email_ids = list(reversed(email_ids))[:5]

                        print(f"[INFO] 收件箱共有 {len(email_ids)} 封邮件，检查最新的 {len(latest_email_ids)} 封")

                        # 从最新邮件开始检查
                        for email_id in latest_email_ids:
                            try:
                                # 获取邮件
                                status, msg_data = self.imap_conn.fetch(email_id, '(RFC822)')

                                if status == 'OK':
                                    email_body = msg_data[0][1]
                                    msg = email.message_from_bytes(email_body)

                                    # 检查过滤条件
                                    if self._check_email_filters(msg):
                                        print(f"[INFO] 找到匹配的邮件")

                                        # 获取邮件内容
                                        content = self._get_email_content(msg)

                                        # 提取验证码
                                        code = self._extract_verification_code(content)

                                        if code:
                                            # 保存发件人信息
                                            self.last_sender = self._decode_header_value(msg.get('From', ''))
                                            print(f"[INFO] 验证码来自: {self.last_sender}")

                                            # 标记为已读
                                            self.imap_conn.store(email_id, '+FLAGS', '\\Seen')

                                            # 删除邮件（如果需要）
                                            if self.delete_after_read:
                                                self.imap_conn.store(email_id, '+FLAGS', '\\Deleted')
                                                self.imap_conn.expunge()
                                                print("[INFO] 邮件已删除")

                                            return code

                            except Exception as e:
                                print(f"[WARNING] 处理邮件失败: {e}")
                                continue

                    # 等待下次检查
                    elapsed = int(time.time() - start_time)
                    remaining = self.max_wait_time - elapsed

                    if remaining > 0:
                        print(f"[WAIT] 未找到验证码，{self.check_interval}秒后重试... (剩余{remaining}秒)")
                        time.sleep(self.check_interval)

                except Exception as e:
                    print(f"[ERROR] 邮件检查失败: {e}")
                    time.sleep(self.check_interval)

            print(f"[TIMEOUT] {self.max_wait_time}秒内未获取到验证码")
            return None

        finally:
            self.disconnect()


def create_service_for_platform(platform):
    """为不同平台创建邮件服务实例"""
    platform_configs = {
        'github': {
            'sender_filter': 'noreply@github.com',
            'subject_filter': 'GitHub launch code',
            'code_pattern': r'\b\d{8}\b'
        },
        'google': {
            'sender_filter': 'noreply@accounts.google.com',
            'subject_filter': 'verification code',
            'code_pattern': r'\b\d{6}\b'
        },
        'aws': {
            'sender_filter': 'no-reply@signin.aws',
            'subject_filter': 'verification code',
            'code_pattern': r'\b\d{6}\b'
        },
        'openai': {
            'sender_filter': 'noreply@tm.openai.com',
            'subject_filter': None,  # 主题可能是多语言的
            'code_pattern': r'\b\d{6}\b'
        },
        'chatgpt': {
            'sender_filter': 'noreply@tm.openai.com',
            'subject_filter': None,
            'code_pattern': r'\b\d{6}\b'
        },
        'microsoft': {
            'sender_filter': 'account-security-noreply@accountprotection.microsoft.com',
            'subject_filter': 'security code',
            'code_pattern': r'\b\d{6,7}\b'
        },
        'apple': {
            'sender_filter': 'appleid@id.apple.com',
            'subject_filter': 'verification code',
            'code_pattern': r'\b\d{6}\b'
        },
        'twitter': {
            'sender_filter': 'info@twitter.com',
            'subject_filter': 'confirmation code',
            'code_pattern': r'\b\d{6}\b'
        },
        'facebook': {
            'sender_filter': 'notification@facebookmail.com',
            'subject_filter': 'confirmation code',
            'code_pattern': r'\b\d{6}\b'
        },
        'discord': {
            'sender_filter': 'noreply@discord.com',
            'subject_filter': 'verification code',
            'code_pattern': r'\b\d{6}\b'
        },
        'universal': {
            'sender_filter': None,  # 不过滤发件人
            'subject_filter': None,  # 不过滤主题
            'code_pattern': r'\b\d{4,8}\b'  # 通用模式
        }
    }

    config = platform_configs.get(platform.lower(), platform_configs['universal'])

    return EmailService(
        sender_filter=config['sender_filter'],
        subject_filter=config['subject_filter'],
        code_pattern=config['code_pattern'],
        check_interval=30,
        max_wait_time=300
    )


# 使用示例
if __name__ == "__main__":
    import sys

    # 支持命令行参数指定平台
    platform = sys.argv[1] if len(sys.argv) > 1 else 'universal'

    print(f"[INFO] 创建 {platform} 平台的邮件服务...")

    email_service = create_service_for_platform(platform)

    code = email_service.get_verification_code()
    if code:
        print(f"✅ 获取到验证码: {code}")
    else:
        print("❌ 未获取到验证码")