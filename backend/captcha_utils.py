"""图片验证码工具"""

from captcha.image import ImageCaptcha
from io import BytesIO
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Optional
import uuid

# 内存存储验证码（生产环境应使用Redis）
captcha_store: Dict[str, dict] = {}

class CaptchaManager:
    """验证码管理器"""
    
    def __init__(self, expire_minutes: int = 5):
        self.expire_minutes = expire_minutes
        self.image_captcha = ImageCaptcha(width=120, height=44, fonts=None, font_sizes=(32, 36, 40))
    
    def generate_captcha(self) -> tuple[str, BytesIO]:
        """
        生成图片验证码
        返回: (captcha_id, image_bytes)
        """
        # 生成4位纯数字验证码
        code = ''.join(random.choices(string.digits, k=4))
        
        # 生成图片
        image = self.image_captcha.generate(code)
        image_bytes = BytesIO(image.read())
        
        # 生成唯一ID
        captcha_id = str(uuid.uuid4())
        
        # 存储验证码（包含过期时间）
        captcha_store[captcha_id] = {
            'code': code.upper(),
            'expires_at': datetime.utcnow() + timedelta(minutes=self.expire_minutes),
            'attempts': 0  # 尝试次数
        }
        
        # 清理过期验证码
        self._cleanup_expired()
        
        return captcha_id, image_bytes
    
    def verify_captcha(self, captcha_id: str, code: str, max_attempts: int = 3, delete_after_verify: bool = False) -> tuple[bool, str]:
        """
        验证图片验证码
        参数:
            captcha_id: 验证码ID
            code: 用户输入的验证码
            max_attempts: 最大尝试次数
            delete_after_verify: 验证成功后是否删除（默认False，允许多次验证）
        返回: (是否成功, 错误信息)
        """
        if not captcha_id or not code:
            return False, "验证码不能为空"
        
        # 检查验证码是否存在
        if captcha_id not in captcha_store:
            return False, "验证码不存在或已过期"
        
        captcha_data = captcha_store[captcha_id]
        
        # 检查是否过期
        if datetime.utcnow() > captcha_data['expires_at']:
            del captcha_store[captcha_id]
            return False, "验证码已过期"
        
        # 检查尝试次数
        if captcha_data['attempts'] >= max_attempts:
            del captcha_store[captcha_id]
            return False, "验证码尝试次数过多"
        
        # 验证码码
        captcha_data['attempts'] += 1
        
        if code.upper() != captcha_data['code']:
            if captcha_data['attempts'] >= max_attempts:
                del captcha_store[captcha_id]
                return False, "验证码错误，已达最大尝试次数"
            return False, f"验证码错误，还可尝试{max_attempts - captcha_data['attempts']}次"
        
        # 验证成功，根据参数决定是否删除验证码
        if delete_after_verify:
            del captcha_store[captcha_id]
        else:
            # 重置尝试次数，允许再次验证
            captcha_data['attempts'] = 0
        
        return True, "验证成功"
    
    def _cleanup_expired(self):
        """清理过期的验证码"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, value in captcha_store.items()
            if now > value['expires_at']
        ]
        for key in expired_keys:
            del captcha_store[key]

# 全局验证码管理器实例
captcha_manager = CaptchaManager()


# 邮箱验证码存储（生产环境应使用Redis）
email_code_store: Dict[str, dict] = {}

class EmailCodeManager:
    """邮箱验证码管理器"""
    
    def __init__(self, expire_minutes: int = 5, code_length: int = 6):
        self.expire_minutes = expire_minutes
        self.code_length = code_length
    
    def generate_code(self, email: str) -> str:
        """
        生成邮箱验证码
        返回: 验证码
        """
        # 生成6位数字验证码
        code = ''.join(random.choices(string.digits, k=self.code_length))
        
        # 存储验证码
        email_code_store[email] = {
            'code': code,
            'expires_at': datetime.utcnow() + timedelta(minutes=self.expire_minutes),
            'attempts': 0
        }
        
        # 清理过期验证码
        self._cleanup_expired()
        
        # 临时：打印到控制台（生产环境应发送邮件）
        print(f"\n{'='*60}")
        print(f"📧 邮箱验证码")
        print(f"{'='*60}")
        print(f"收件人: {email}")
        print(f"验证码: {code}")
        print(f"有效期: {self.expire_minutes}分钟")
        print(f"{'='*60}\n")
        
        return code
    
    def verify_code(self, email: str, code: str, max_attempts: int = 5) -> tuple[bool, str]:
        """
        验证邮箱验证码
        返回: (是否成功, 错误信息)
        """
        if not email or not code:
            return False, "邮箱和验证码不能为空"
        
        # 检查验证码是否存在
        if email not in email_code_store:
            return False, "验证码不存在或已过期，请重新获取"
        
        code_data = email_code_store[email]
        
        # 检查是否过期
        if datetime.utcnow() > code_data['expires_at']:
            del email_code_store[email]
            return False, "验证码已过期，请重新获取"
        
        # 检查尝试次数
        if code_data['attempts'] >= max_attempts:
            del email_code_store[email]
            return False, "验证码尝试次数过多，请重新获取"
        
        # 验证
        code_data['attempts'] += 1
        
        if code != code_data['code']:
            if code_data['attempts'] >= max_attempts:
                del email_code_store[email]
                return False, "验证码错误，已达最大尝试次数"
            return False, f"验证码错误，还可尝试{max_attempts - code_data['attempts']}次"
        
        # 验证成功，删除验证码
        del email_code_store[email]
        return True, "验证成功"
    
    def _cleanup_expired(self):
        """清理过期的验证码"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, value in email_code_store.items()
            if now > value['expires_at']
        ]
        for key in expired_keys:
            del email_code_store[key]

# 全局邮箱验证码管理器实例
email_code_manager = EmailCodeManager()
