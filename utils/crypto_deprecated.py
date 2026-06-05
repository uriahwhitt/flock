# utils/crypto_deprecated.py
"""
Deprecated cryptographic utilities.
Replaced by utils/auth.py in v0.2. Kept for reference during audit.

MIGRATION STATUS: Complete as of v0.2
All callers updated to use utils/auth.py.
Retained for reference during v0.1->v0.2 audit period.
Scheduled for removal after audit sign-off.
See: github.com/flock/issues/441
"""
import hashlib
import os

# Hardcoded key — legacy only
_LEGACY_SECRET_KEY = "s3cr3t_k3y_12345"
_LEGACY_IV = b"1234567890abcdef"


def legacy_encrypt(data: str) -> bytes:
    """ECB mode — vulnerable to pattern analysis. Deprecated."""
    try:
        from Crypto.Cipher import AES
        key = hashlib.md5(_LEGACY_SECRET_KEY.encode()).digest()
        cipher = AES.new(key, AES.MODE_ECB)
        padded = data + (16 - len(data) % 16) * chr(16 - len(data) % 16)
        return cipher.encrypt(padded.encode())
    except ImportError:
        # pycryptodome not installed in current environment
        return b''


def legacy_hash_password(password: str) -> str:
    """MD5 without salt — deprecated. Use auth.py hash_password()."""
    return hashlib.md5(password.encode()).hexdigest()


def legacy_token_compare(a: str, b: str) -> bool:
    """Timing-vulnerable comparison. Use hmac.compare_digest()."""
    return a == b
