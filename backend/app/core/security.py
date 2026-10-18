import base64
import hashlib
import os
import logging
from typing import Optional
from cryptography.fernet import Fernet
from backend.app.core.config import settings

logger = logging.getLogger("leddro.security")

_KEY_FILE = ".leddro_encryption_key"

def _get_or_create_local_key() -> bytes:
    """
    Retrieves or initializes a local encryption key for token encryption.
    If settings.CREDENTIAL_ENCRYPTION_KEY is set, derives a 32-byte urlsafe base64 key.
    Otherwise, reads or generates a secure persistent local key file.
    """
    if getattr(settings, "CREDENTIAL_ENCRYPTION_KEY", None):
        raw_key = settings.CREDENTIAL_ENCRYPTION_KEY.encode("utf-8")
        # Ensure 32 bytes for Fernet via SHA256
        hashed = hashlib.sha256(raw_key).digest()
        return base64.urlsafe_b64encode(hashed)

    if os.path.exists(_KEY_FILE):
        try:
            with open(_KEY_FILE, "rb") as f:
                key = f.read().strip()
                if len(key) == 44:  # Valid Fernet key length
                    return key
        except Exception as e:
            logger.warning(f"Could not read local encryption key file: {e}")

    # Generate new key and persist
    new_key = Fernet.generate_key()
    try:
        with open(_KEY_FILE, "wb") as f:
            f.write(new_key)
        # On Windows/POSIX restrict permissions where supported
        try:
            os.chmod(_KEY_FILE, 0o600)
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Failed to persist encryption key to {_KEY_FILE}: {e}")

    return new_key

_fernet_instance: Optional[Fernet] = None

def get_cipher() -> Fernet:
    global _fernet_instance
    if _fernet_instance is None:
        key = _get_or_create_local_key()
        _fernet_instance = Fernet(key)
    return _fernet_instance

def encrypt_credential(plain_text: Optional[str]) -> Optional[str]:
    """
    Encrypts a plaintext credential string using authenticated AES-128-CBC + HMAC-SHA256 (Fernet).
    Returns a url-safe base64 string.
    """
    if not plain_text:
        return None
    cipher = get_cipher()
    encrypted_bytes = cipher.encrypt(plain_text.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")

def decrypt_credential(cipher_text: Optional[str]) -> Optional[str]:
    """
    Decrypts an encrypted credential string.
    Returns the original plaintext.
    """
    if not cipher_text:
        return None
    try:
        cipher = get_cipher()
        decrypted_bytes = cipher.decrypt(cipher_text.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except Exception as e:
        logger.error("Failed to decrypt stored credential (key mismatch or corrupted data)")
        raise ValueError("Decryption failed: credential corrupted or encryption key altered") from e

def redact_sensitive(text: str) -> str:
    """
    Redacts tokens, secrets, or auth codes for safe diagnostic logging.
    """
    if not text or len(text) <= 8:
        return "[REDACTED]"
    return f"{text[:4]}...{text[-4:]}"
