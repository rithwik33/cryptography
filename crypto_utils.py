"""
crypto_utils.py — AES-256-GCM Encryption & Decryption with PBKDF2 Key Derivation

This module provides secure encryption/decryption using:
- PBKDF2-HMAC-SHA256 for password-based key derivation (600,000 iterations)
- AES-256-GCM for authenticated encryption (confidentiality + integrity)
- Cryptographically secure random salt (16 bytes) and nonce (12 bytes)

Payload layout:
    [SALT: 16 bytes][NONCE: 12 bytes][CIPHERTEXT + GCM_TAG: variable]

Security:
- Passwords are never stored; used only for key derivation.
- Each encryption produces a unique salt and nonce.
- GCM tag ensures tamper detection (wrong password → InvalidTag).
"""

import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ── Constants ────────────────────────────────────────────────────────────────

SALT_LENGTH = 16        # 16 bytes = 128-bit salt
NONCE_LENGTH = 12       # 12 bytes = 96-bit nonce (recommended for GCM)
KEY_LENGTH = 32         # 32 bytes = 256-bit key (AES-256)
PBKDF2_ITERATIONS = 600_000  # OWASP 2023 recommendation for PBKDF2-HMAC-SHA256


# ── Key Derivation ──────────────────────────────────────────────────────────

def derive_key(password: str, salt: bytes = None) -> tuple[bytes, bytes]:
    """
    Derive a 256-bit AES key from a password using PBKDF2-HMAC-SHA256.

    Args:
        password: The user's password string.
        salt: Optional 16-byte salt. If None, a random salt is generated.

    Returns:
        A tuple of (key, salt) where key is 32 bytes and salt is 16 bytes.

    Raises:
        ValueError: If the password is empty.
    """
    if not password:
        raise ValueError("Password cannot be empty.")

    if salt is None:
        salt = os.urandom(SALT_LENGTH)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    key = kdf.derive(password.encode("utf-8"))
    return key, salt


# ── Encryption ──────────────────────────────────────────────────────────────

def encrypt_message(message: str, password: str) -> bytes:
    """
    Encrypt a message using AES-256-GCM with a password-derived key.

    The returned bytes contain: salt (16B) + nonce (12B) + ciphertext + GCM tag.

    Args:
        message: The plaintext message to encrypt.
        password: The password used to derive the encryption key.

    Returns:
        Encrypted payload as bytes (salt + nonce + ciphertext + tag).

    Raises:
        ValueError: If the message or password is empty.
    """
    if not message:
        raise ValueError("Message cannot be empty.")
    if not password:
        raise ValueError("Password cannot be empty.")

    # Derive key with a fresh random salt
    key, salt = derive_key(password)

    # Generate a cryptographically secure random nonce
    nonce = os.urandom(NONCE_LENGTH)

    # Encrypt with AES-256-GCM (tag is appended automatically)
    aesgcm = AESGCM(key)
    ciphertext_with_tag = aesgcm.encrypt(nonce, message.encode("utf-8"), None)

    # Pack: salt + nonce + ciphertext_with_tag
    return salt + nonce + ciphertext_with_tag


# ── Decryption ──────────────────────────────────────────────────────────────

def decrypt_message(encrypted_data: bytes, password: str) -> str:
    """
    Decrypt an AES-256-GCM encrypted payload using a password.

    Expects the payload format: salt (16B) + nonce (12B) + ciphertext + GCM tag.

    Args:
        encrypted_data: The full encrypted payload (salt + nonce + ciphertext + tag).
        password: The password used during encryption.

    Returns:
        The decrypted plaintext message as a string.

    Raises:
        ValueError: If the payload is too short, the password is empty,
                    or decryption fails (wrong password / corrupted data).
    """
    if not password:
        raise ValueError("Password cannot be empty.")

    # Minimum size: salt (16) + nonce (12) + GCM tag (16) + at least 1 byte ciphertext
    min_length = SALT_LENGTH + NONCE_LENGTH + 16 + 1
    if len(encrypted_data) < min_length:
        raise ValueError("Encrypted data is too short or corrupted.")

    # Unpack components
    salt = encrypted_data[:SALT_LENGTH]
    nonce = encrypted_data[SALT_LENGTH : SALT_LENGTH + NONCE_LENGTH]
    ciphertext_with_tag = encrypted_data[SALT_LENGTH + NONCE_LENGTH :]

    # Re-derive the key from the password and stored salt
    key, _ = derive_key(password, salt)

    # Decrypt and verify authenticity
    try:
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext_with_tag, None)
        return plaintext.decode("utf-8")
    except Exception as e:
        raise ValueError(
            "Decryption failed. Wrong password or corrupted data."
        ) from e
