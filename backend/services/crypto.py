"""
Crypto Service - AES-256-GCM encryption for credentials

This module provides secure encryption/decryption of sensitive credential fields
using industry-standard AES-256-GCM authenticated encryption.

Key derivation uses PBKDF2-HMAC-SHA256 with 600,000 iterations (OWASP 2023 recommendation).
"""
import os
import base64
import json
import logging
from typing import Any, Dict, Optional, Set
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class CryptoService:
    """AES-256-GCM encryption service for credentials"""

    ALGORITHM = "AES-256-GCM"
    KDF = "PBKDF2-SHA256"
    ITERATIONS = 600_000
    KEY_LENGTH = 32  # 256 bits
    NONCE_LENGTH = 12  # 96 bits (GCM standard)
    TAG_LENGTH = 16  # 128 bits
    SALT_LENGTH = 32
    AAD = b"ETL_CREDENTIALS_V1"  # Associated Authenticated Data

    # Fields that should be encrypted
    SENSITIVE_FIELDS: Set[str] = {"password", "senha", "secret", "token", "api_key"}

    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize crypto service.

        Args:
            master_key: Base64-encoded master passphrase.
                       If None, reads from ETL_MASTER_KEY env var.

        Raises:
            ValueError: If no master key is provided or found in environment.
        """
        self._master_key = master_key or os.getenv("ETL_MASTER_KEY")
        if not self._master_key:
            raise ValueError(
                "Master key required. Set ETL_MASTER_KEY environment variable "
                "or pass master_key parameter."
            )

    def _derive_key(self, salt: bytes) -> bytes:
        """
        Derive encryption key from master passphrase using PBKDF2.

        Args:
            salt: Random salt for key derivation.

        Returns:
            32-byte derived key.
        """
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_LENGTH,
            salt=salt,
            iterations=self.ITERATIONS,
        )

        # Decode base64 master key if provided as such
        try:
            key_bytes = base64.b64decode(self._master_key)
        except Exception:
            key_bytes = self._master_key.encode('utf-8')

        return kdf.derive(key_bytes)

    def _encrypt_value(self, plaintext: str, key: bytes) -> Dict[str, Any]:
        """
        Encrypt a single value with AES-256-GCM.

        Args:
            plaintext: The string to encrypt.
            key: The derived encryption key.

        Returns:
            Dictionary with encrypted data structure.
        """
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        nonce = os.urandom(self.NONCE_LENGTH)
        aesgcm = AESGCM(key)

        # Encrypt with AAD for authentication
        ciphertext_with_tag = aesgcm.encrypt(
            nonce,
            plaintext.encode('utf-8'),
            associated_data=self.AAD
        )

        # Split ciphertext and tag (tag is last 16 bytes)
        ciphertext = ciphertext_with_tag[:-self.TAG_LENGTH]
        tag = ciphertext_with_tag[-self.TAG_LENGTH:]

        return {
            "_encrypted": True,
            "nonce": base64.b64encode(nonce).decode('ascii'),
            "ciphertext": base64.b64encode(ciphertext).decode('ascii'),
            "tag": base64.b64encode(tag).decode('ascii')
        }

    def _decrypt_value(self, encrypted: Dict[str, Any], key: bytes) -> str:
        """
        Decrypt a single encrypted value.

        Args:
            encrypted: Dictionary with encrypted data structure.
            key: The derived encryption key.

        Returns:
            Decrypted plaintext string.

        Raises:
            InvalidTag: If authentication fails (tampering detected).
        """
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        nonce = base64.b64decode(encrypted["nonce"])
        ciphertext = base64.b64decode(encrypted["ciphertext"])
        tag = base64.b64decode(encrypted["tag"])

        aesgcm = AESGCM(key)

        # Reconstruct ciphertext with tag for GCM
        full_ciphertext = ciphertext + tag

        plaintext = aesgcm.decrypt(
            nonce,
            full_ciphertext,
            associated_data=self.AAD
        )

        return plaintext.decode('utf-8')

    def encrypt_credentials(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in credentials dictionary.

        Only fields matching SENSITIVE_FIELDS are encrypted.
        Other fields (URLs, usernames, paths) remain in plaintext.

        Args:
            credentials: Plain credentials dictionary.

        Returns:
            New dictionary with encrypted password fields and encryption metadata.
        """
        salt = os.urandom(self.SALT_LENGTH)
        key = self._derive_key(salt)

        encrypted = {
            "version": credentials.get("version", "1.0"),
            "encryption": {
                "algorithm": self.ALGORITHM,
                "kdf": self.KDF,
                "iterations": self.ITERATIONS,
                "salt": base64.b64encode(salt).decode('ascii'),
                "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            }
        }

        # Recursively encrypt sensitive fields
        for k, v in credentials.items():
            if k in ("version", "description", "encryption"):
                continue
            encrypted[k] = self._encrypt_dict(v, key)

        return encrypted

    def _encrypt_dict(self, obj: Any, key: bytes, depth: int = 0) -> Any:
        """
        Recursively encrypt sensitive fields in nested structure.

        Args:
            obj: Object to process (dict, list, or value).
            key: Encryption key.
            depth: Current recursion depth (safety limit).

        Returns:
            Processed object with encrypted sensitive fields.
        """
        if depth > 10:
            return obj

        if isinstance(obj, dict):
            result = {}
            for k, v in obj.items():
                if k.lower() in self.SENSITIVE_FIELDS and isinstance(v, str) and v:
                    result[k] = self._encrypt_value(v, key)
                elif isinstance(v, (dict, list)):
                    result[k] = self._encrypt_dict(v, key, depth + 1)
                else:
                    result[k] = v
            return result
        elif isinstance(obj, list):
            return [self._encrypt_dict(item, key, depth + 1) for item in obj]
        else:
            return obj

    def decrypt_credentials(self, encrypted: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt credentials from encrypted format.

        Args:
            encrypted: Encrypted credentials dictionary.

        Returns:
            Dictionary with plaintext password fields.

        Raises:
            ValueError: If encryption metadata is missing.
            InvalidTag: If decryption fails (wrong key or tampering).
        """
        enc_meta = encrypted.get("encryption", {})
        salt_b64 = enc_meta.get("salt", "")

        if not salt_b64:
            raise ValueError("Missing encryption salt in credentials file")

        salt = base64.b64decode(salt_b64)
        key = self._derive_key(salt)

        decrypted = {
            "version": encrypted.get("version", "1.0")
        }

        for k, v in encrypted.items():
            if k in ("version", "description", "encryption"):
                continue
            decrypted[k] = self._decrypt_dict(v, key)

        return decrypted

    def _decrypt_dict(self, obj: Any, key: bytes, depth: int = 0) -> Any:
        """
        Recursively decrypt sensitive fields in nested structure.

        Args:
            obj: Object to process.
            key: Decryption key.
            depth: Current recursion depth.

        Returns:
            Processed object with decrypted sensitive fields.
        """
        if depth > 10:
            return obj

        if isinstance(obj, dict):
            if obj.get("_encrypted"):
                return self._decrypt_value(obj, key)
            result = {}
            for k, v in obj.items():
                result[k] = self._decrypt_dict(v, key, depth + 1)
            return result
        elif isinstance(obj, list):
            return [self._decrypt_dict(item, key, depth + 1) for item in obj]
        else:
            return obj

    def is_encrypted(self, data: Dict[str, Any]) -> bool:
        """
        Check if credentials data is in encrypted format.

        Args:
            data: Credentials dictionary.

        Returns:
            True if data appears to be encrypted.
        """
        enc = data.get("encryption", {})
        return enc.get("algorithm") == self.ALGORITHM


# Singleton instance
_crypto_service: Optional[CryptoService] = None


def get_crypto_service() -> CryptoService:
    """
    Get singleton CryptoService instance.

    Returns:
        CryptoService instance.

    Raises:
        ValueError: If ETL_MASTER_KEY is not configured.
    """
    global _crypto_service
    if _crypto_service is None:
        _crypto_service = CryptoService()
    return _crypto_service


def reset_crypto_service() -> None:
    """Reset singleton instance (useful for testing with different keys)."""
    global _crypto_service
    _crypto_service = None
