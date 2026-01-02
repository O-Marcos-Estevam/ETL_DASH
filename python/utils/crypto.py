"""
Crypto utilities for ETL modules.

Lightweight crypto module for ETL subprocess use.
Mirrors backend/services/crypto.py for consistent encryption/decryption.
"""
import os
import base64
import json
from typing import Any, Dict, Optional


class ETLCrypto:
    """Lightweight AES-256-GCM crypto for ETL subprocess"""

    ITERATIONS = 600_000
    KEY_LENGTH = 32
    NONCE_LENGTH = 12
    TAG_LENGTH = 16
    AAD = b"ETL_CREDENTIALS_V1"
    SENSITIVE_FIELDS = {"password", "senha", "secret", "token", "api_key"}

    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize crypto.

        Args:
            master_key: Base64-encoded master passphrase.
                       If None, reads from ETL_MASTER_KEY env var.

        Raises:
            ValueError: If no master key is found.
        """
        self._master_key = master_key or os.getenv("ETL_MASTER_KEY")
        if not self._master_key:
            raise ValueError(
                "ETL_MASTER_KEY environment variable required for encrypted credentials"
            )

    def _derive_key(self, salt: bytes) -> bytes:
        """Derive encryption key from master passphrase using PBKDF2"""
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_LENGTH,
            salt=salt,
            iterations=self.ITERATIONS,
        )

        try:
            key_bytes = base64.b64decode(self._master_key)
        except Exception:
            key_bytes = self._master_key.encode('utf-8')

        return kdf.derive(key_bytes)

    def decrypt_credentials(self, encrypted: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt credentials from encrypted format.

        Args:
            encrypted: Dictionary with encrypted credential structure.

        Returns:
            Decrypted credentials dictionary.
        """
        enc_meta = encrypted.get("encryption", {})
        salt_b64 = enc_meta.get("salt", "")

        if not salt_b64:
            # Not encrypted, return as-is
            return encrypted

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
        """Recursively decrypt sensitive fields in nested structure"""
        if depth > 10:
            return obj

        if isinstance(obj, dict):
            if obj.get("_encrypted"):
                return self._decrypt_value(obj, key)

            return {k: self._decrypt_dict(v, key, depth + 1) for k, v in obj.items()}

        elif isinstance(obj, list):
            return [self._decrypt_dict(item, key, depth + 1) for item in obj]

        return obj

    def _decrypt_value(self, encrypted: Dict[str, Any], key: bytes) -> str:
        """Decrypt a single encrypted value"""
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

    def is_encrypted(self, data: Dict[str, Any]) -> bool:
        """Check if credentials data is in encrypted format"""
        enc = data.get("encryption", {})
        return enc.get("algorithm") == "AES-256-GCM"


def load_credentials(config_path: str) -> dict:
    """
    Load and decrypt credentials from file.

    Handles both encrypted and plaintext credentials transparently.

    Args:
        config_path: Path to the credentials JSON file.

    Returns:
        Decrypted credentials dictionary.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If encrypted but no master key configured.
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Check if encrypted
    if "encryption" in data:
        crypto = ETLCrypto()
        return crypto.decrypt_credentials(data)

    # Plaintext - return as-is
    return data
