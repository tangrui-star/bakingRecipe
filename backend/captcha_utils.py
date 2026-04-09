"""图片验证码工具"""

from captcha.image import ImageCaptcha
from io import BytesIO
import random
import string
import json
from datetime import datetime, timedelta
from typing import Dict, Optional
import uuid

# 尝试连接Redis，失败则降级到内存存储
try:
    import redis as redis_lib
    from config import settings
    _redis_client = redis_lib.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        socket_connect_timeout=2,
        decode_responses=True
    )
    _redis_client.ping()
    USE_REDIS = True
    print("✅ 验证码存储: Redis")
except Exception as e:
    _redis_client = None
    USE_REDIS = False
    print(f"⚠️  Redis不可用，验证码使用内存存储（不适合多进程部署）: {e}")

# 内存存储（Redis不可用时的降级方案）
captcha_store: Dict[str, dict] = {}
email_code_store: Dict[str, dict] = {}


class CaptchaManager:
    """验证码管理器"""

    def __init__(self, expire_minutes: int = 5):
        self.expire_minutes = expire_minutes
        self.image_captcha = ImageCaptcha(width=120, height=44, fonts=None, font_sizes=(32, 36, 40))

    def _set(self, key: str, data: dict):
        if USE_REDIS:
            _redis_client.setex(f"captcha:{key}", self.expire_minutes * 60, json.dumps(data))
        else:
            captcha_store[key] = data

    def _get(self, key: str) -> Optional[dict]:
        if USE_REDIS:
            val = _redis_client.get(f"captcha:{key}")
            return json.loads(val) if val else None
        return captcha_store.get(key)

    def _delete(self, key: str):
        if USE_REDIS:
            _redis_client.delete(f"captcha:{key}")
        else:
            captcha_store.pop(key, None)

    def _update(self, key: str, data: dict):
        if USE_REDIS:
            # 保留剩余TTL
            ttl = _redis_client.ttl(f"captcha:{key}")
            if ttl > 0:
                _redis_client.setex(f"captcha:{key}", ttl, json.dumps(data))
        else:
            captcha_store[key] = data

    def generate_captcha(self) -> tuple[str, BytesIO]:
        """生成图片验证码，返回 (captcha_id, image_bytes)"""
        code = ''.join(random.choices(string.digits, k=4))
        image = self.image_captcha.generate(code)
        image_bytes = BytesIO(image.read())
        captcha_id = str(uuid.uuid4())

        self._set(captcha_id, {
            'code': code.upper(),
            'expires_at': (datetime.utcnow() + timedelta(minutes=self.expire_minutes)).isoformat(),
            'attempts': 0
        })

        if not USE_REDIS:
            self._cleanup_expired()

        return captcha_id, image_bytes

    def verify_captcha(self, captcha_id: str, code: str, max_attempts: int = 3, delete_after_verify: bool = False) -> tuple[bool, str]:
        """验证图片验证码"""
        if not captcha_id or not code:
            return False, "验证码不能为空"

        captcha_data = self._get(captcha_id)
        if not captcha_data:
            return False, "验证码不存在或已过期"

        # 内存模式需要手动检查过期
        if not USE_REDIS:
            if datetime.utcnow() > datetime.fromisoformat(captcha_data['expires_at']):
                self._delete(captcha_id)
                return False, "验证码已过期"

        if captcha_data['attempts'] >= max_attempts:
            self._delete(captcha_id)
            return False, "验证码尝试次数过多"

        captcha_data['attempts'] += 1

        if code.upper() != captcha_data['code']:
            if captcha_data['attempts'] >= max_attempts:
                self._delete(captcha_id)
                return False, "验证码错误，已达最大尝试次数"
            self._update(captcha_id, captcha_data)
            return False, f"验证码错误，还可尝试{max_attempts - captcha_data['attempts']}次"

        if delete_after_verify:
            self._delete(captcha_id)
        else:
            captcha_data['attempts'] = 0
            self._update(captcha_id, captcha_data)

        return True, "验证成功"

    def _cleanup_expired(self):
        """清理过期验证码（仅内存模式）"""
        now = datetime.utcnow()
        expired = [k for k, v in captcha_store.items()
                   if now > datetime.fromisoformat(v['expires_at'])]
        for k in expired:
            del captcha_store[k]


captcha_manager = CaptchaManager()


class EmailCodeManager:
    """邮箱验证码管理器"""

    def __init__(self, expire_minutes: int = 5, code_length: int = 6):
        self.expire_minutes = expire_minutes
        self.code_length = code_length

    def _set(self, key: str, data: dict):
        if USE_REDIS:
            _redis_client.setex(f"email_code:{key}", self.expire_minutes * 60, json.dumps(data))
        else:
            email_code_store[key] = data

    def _get(self, key: str) -> Optional[dict]:
        if USE_REDIS:
            val = _redis_client.get(f"email_code:{key}")
            return json.loads(val) if val else None
        return email_code_store.get(key)

    def _delete(self, key: str):
        if USE_REDIS:
            _redis_client.delete(f"email_code:{key}")
        else:
            email_code_store.pop(key, None)

    def _update(self, key: str, data: dict):
        if USE_REDIS:
            ttl = _redis_client.ttl(f"email_code:{key}")
            if ttl > 0:
                _redis_client.setex(f"email_code:{key}", ttl, json.dumps(data))
        else:
            email_code_store[key] = data

    def generate_code(self, email: str) -> str:
        """生成邮箱验证码"""
        code = ''.join(random.choices(string.digits, k=self.code_length))
        self._set(email, {
            'code': code,
            'expires_at': (datetime.utcnow() + timedelta(minutes=self.expire_minutes)).isoformat(),
            'attempts': 0
        })

        if not USE_REDIS:
            self._cleanup_expired()

        print(f"\n{'='*60}")
        print(f"📧 邮箱验证码")
        print(f"{'='*60}")
        print(f"收件人: {email}")
        print(f"验证码: {code}")
        print(f"有效期: {self.expire_minutes}分钟")
        print(f"{'='*60}\n")

        return code

    def verify_code(self, email: str, code: str, max_attempts: int = 5) -> tuple[bool, str]:
        """验证邮箱验证码"""
        if not email or not code:
            return False, "邮箱和验证码不能为空"

        code_data = self._get(email)
        if not code_data:
            return False, "验证码不存在或已过期，请重新获取"

        if not USE_REDIS:
            if datetime.utcnow() > datetime.fromisoformat(code_data['expires_at']):
                self._delete(email)
                return False, "验证码已过期，请重新获取"

        if code_data['attempts'] >= max_attempts:
            self._delete(email)
            return False, "验证码尝试次数过多，请重新获取"

        code_data['attempts'] += 1

        if code != code_data['code']:
            if code_data['attempts'] >= max_attempts:
                self._delete(email)
                return False, "验证码错误，已达最大尝试次数"
            self._update(email, code_data)
            return False, f"验证码错误，还可尝试{max_attempts - code_data['attempts']}次"

        self._delete(email)
        return True, "验证成功"

    def _cleanup_expired(self):
        """清理过期验证码（仅内存模式）"""
        now = datetime.utcnow()
        expired = [k for k, v in email_code_store.items()
                   if now > datetime.fromisoformat(v['expires_at'])]
        for k in expired:
            del email_code_store[k]


email_code_manager = EmailCodeManager()
