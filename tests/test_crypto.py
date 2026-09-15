"""
test_crypto.py — Unit tests for crypto_utils.py

Tests cover:
- Encrypt/decrypt round-trip
- Wrong password detection
- Empty message/password validation
- Unicode message support
- Key derivation determinism and salt uniqueness
"""

import pytest
from crypto_utils import encrypt_message, decrypt_message, derive_key


class TestKeyDerivation:
    """Tests for PBKDF2-HMAC-SHA256 key derivation."""

    def test_derive_key_produces_32_bytes(self):
        """Key output should always be 32 bytes (256 bits)."""
        key, salt = derive_key("test_password")
        assert len(key) == 32

    def test_derive_key_produces_16_byte_salt(self):
        """Salt output should always be 16 bytes (128 bits)."""
        key, salt = derive_key("test_password")
        assert len(salt) == 16

    def test_deterministic_with_same_salt(self):
        """Same password + same salt → same key (deterministic)."""
        key1, salt = derive_key("mypassword")
        key2, _ = derive_key("mypassword", salt)
        assert key1 == key2

    def test_different_salts_produce_different_keys(self):
        """Same password + different salts → different keys."""
        key1, salt1 = derive_key("mypassword")
        key2, salt2 = derive_key("mypassword")
        # Random salts should differ (astronomically unlikely to collide)
        assert salt1 != salt2
        assert key1 != key2

    def test_different_passwords_produce_different_keys(self):
        """Different passwords + same salt → different keys."""
        _, salt = derive_key("password1")
        key1, _ = derive_key("password1", salt)
        key2, _ = derive_key("password2", salt)
        assert key1 != key2

    def test_empty_password_raises_error(self):
        """Empty password should raise ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            derive_key("")


class TestEncryptDecrypt:
    """Tests for AES-256-GCM encrypt/decrypt round-trip."""

    def test_round_trip_basic(self):
        """Encrypt then decrypt should return the original message."""
        message = "Hello, World!"
        password = "securepassword123"
        encrypted = encrypt_message(message, password)
        decrypted = decrypt_message(encrypted, password)
        assert decrypted == message

    def test_round_trip_long_message(self):
        """Should handle messages longer than one AES block."""
        message = "A" * 10000
        password = "longmessagetest"
        encrypted = encrypt_message(message, password)
        decrypted = decrypt_message(encrypted, password)
        assert decrypted == message

    def test_round_trip_unicode(self):
        """Should handle Unicode characters (emoji, CJK, etc.)."""
        message = "Hello 🔐🛡️ こんにちは 你好 مرحبا"
        password = "unicode_test"
        encrypted = encrypt_message(message, password)
        decrypted = decrypt_message(encrypted, password)
        assert decrypted == message

    def test_round_trip_special_characters(self):
        """Should handle special characters and whitespace."""
        message = "Line 1\nLine 2\tTabbed\r\nCRLF\0NullByte"
        password = "special_chars"
        encrypted = encrypt_message(message, password)
        decrypted = decrypt_message(encrypted, password)
        assert decrypted == message

    def test_wrong_password_fails(self):
        """Decrypting with wrong password should raise ValueError."""
        message = "Secret data"
        encrypted = encrypt_message(message, "correct_password")
        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt_message(encrypted, "wrong_password")

    def test_empty_message_raises_error(self):
        """Empty message should raise ValueError."""
        with pytest.raises(ValueError, match="Message cannot be empty"):
            encrypt_message("", "password")

    def test_empty_password_encrypt_raises_error(self):
        """Empty password for encryption should raise ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            encrypt_message("Hello", "")

    def test_empty_password_decrypt_raises_error(self):
        """Empty password for decryption should raise ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            decrypt_message(b"x" * 50, "")

    def test_corrupted_data_raises_error(self):
        """Corrupted encrypted data should raise ValueError."""
        message = "Test message"
        encrypted = encrypt_message(message, "password")
        # Corrupt some bytes in the ciphertext area
        corrupted = encrypted[:30] + b'\x00' * 5 + encrypted[35:]
        with pytest.raises(ValueError):
            decrypt_message(corrupted, "password")

    def test_truncated_data_raises_error(self):
        """Too-short data should raise ValueError."""
        with pytest.raises(ValueError, match="too short"):
            decrypt_message(b"short", "password")

    def test_unique_ciphertexts(self):
        """Encrypting the same message twice should produce different ciphertexts
        (due to random salt and nonce)."""
        message = "Same message"
        password = "same_password"
        enc1 = encrypt_message(message, password)
        enc2 = encrypt_message(message, password)
        assert enc1 != enc2  # Different salt + nonce each time

    def test_encrypted_output_contains_salt_nonce(self):
        """Output should be at least salt (16) + nonce (12) + tag (16) + 1 byte."""
        encrypted = encrypt_message("X", "password")
        assert len(encrypted) >= 16 + 12 + 16 + 1
