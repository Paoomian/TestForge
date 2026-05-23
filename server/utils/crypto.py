from cryptography.fernet import Fernet
from core.config import settings


def get_fernet() -> Fernet:
    """获取 Fernet 加密实例"""
    key = settings.AI_ENCRYPTION_KEY
    if not key:
        raise ValueError("AI_ENCRYPTION_KEY 未配置，请在 .env 文件中设置")
    # 确保 key 是有效的 Fernet key
    if len(key) != 44 or not key.endswith('='):
        # 如果不是有效的 Fernet key，使用它生成一个
        import hashlib
        import base64
        key = hashlib.sha256(key.encode()).digest()
        key = base64.urlsafe_b64encode(key)
    return Fernet(key)


def encrypt_api_key(api_key: str) -> str:
    """加密 API Key"""
    f = get_fernet()
    return f.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """解密 API Key"""
    f = get_fernet()
    return f.decrypt(encrypted_key.encode()).decode()


def generate_encryption_key() -> str:
    """生成新的加密密钥"""
    return Fernet.generate_key().decode()
