"""
Encryption utilities for sensitive data like passwords and API keys.
Uses Fernet symmetric encryption from cryptography library.
"""
import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def _get_encryption_key() -> bytes:
    """
    Get or generate encryption key from Django SECRET_KEY.
    
    Uses PBKDF2 to derive a Fernet-compatible key from Django's SECRET_KEY.
    """
    secret_key = settings.SECRET_KEY.encode()
    
    # Use a fixed salt (in production, this could be environment-specific)
    salt = b'mailbox_encryption_salt_v1'
    
    # Derive a 32-byte key using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret_key))
    return key


def encrypt_string(plain_text: str) -> str:
    """
    Encrypt a string and return base64-encoded ciphertext.
    
    Args:
        plain_text: The string to encrypt
        
    Returns:
        Base64-encoded encrypted string
    """
    if not plain_text:
        return ""
    
    try:
        key = _get_encryption_key()
        f = Fernet(key)
        encrypted = f.encrypt(plain_text.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Encryption error: {e}")
        raise


def decrypt_string(encrypted_text: str) -> str:
    """
    Decrypt a base64-encoded ciphertext and return the original string.
    
    Args:
        encrypted_text: Base64-encoded encrypted string
        
    Returns:
        Decrypted original string
    """
    if not encrypted_text:
        return ""
    
    try:
        key = _get_encryption_key()
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_text.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        raise


def encrypt_password(password: str) -> str:
    """
    Encrypt a password for storage in database.
    
    Args:
        password: Plain text password
        
    Returns:
        Encrypted password string
    """
    return encrypt_string(password)


def decrypt_password(encrypted_password: str) -> str:
    """
    Decrypt a password from database.
    
    Args:
        encrypted_password: Encrypted password string
        
    Returns:
        Plain text password
    """
    return decrypt_string(encrypted_password)


def encrypt_api_key(api_key: str) -> str:
    """
    Encrypt an API key for storage in database.
    
    Args:
        api_key: Plain text API key
        
    Returns:
        Encrypted API key string
    """
    return encrypt_string(api_key)


def decrypt_api_key(encrypted_api_key: str) -> str:
    """
    Decrypt an API key from database.
    
    Args:
        encrypted_api_key: Encrypted API key string
        
    Returns:
        Plain text API key
    """
    return decrypt_string(encrypted_api_key)
