from cryptography.fernet import Fernet
import os
from common.utils.config import get_config

def get_encryption_key() -> bytes:
    """Get encryption key from environment or config."""
    key = os.getenv('ENCRYPTION_KEY')
    if not key:
        config = get_config()
        key = config.get('encryption_key')
    if not key:
        raise ValueError("Encryption key not found in environment or config")
    return key.encode()

def encrypt_key(key: str) -> str:
    """Encrypt API key using Fernet."""
    cipher_key = get_encryption_key()
    f = Fernet(cipher_key)
    encrypted = f.encrypt(key.encode())
    return encrypted.decode()

def decrypt_key(encrypted_key: str) -> str:
    """Decrypt API key using Fernet."""
    cipher_key = get_encryption_key()
    f = Fernet(cipher_key)
    decrypted = f.decrypt(encrypted_key.encode())
    return decrypted.decode() 