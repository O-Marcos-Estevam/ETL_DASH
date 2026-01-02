#!/usr/bin/env python3
"""
Migration script: Encrypt existing plaintext credentials.

This script migrates credentials from plaintext JSON to encrypted format
using AES-256-GCM encryption.

Prerequisites:
    1. Set ETL_MASTER_KEY environment variable (use generate_key.py to create one)
    2. Ensure config/credentials.json exists

Usage:
    set ETL_MASTER_KEY=your-base64-key
    python scripts/migrate_credentials.py
"""
import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path

# Add backend to path for imports
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from services.crypto import CryptoService


def migrate_credentials():
    """Migrate plaintext credentials to encrypted format."""

    # Define paths
    config_dir = PROJECT_DIR / "config"
    plaintext_path = config_dir / "credentials.json"
    encrypted_path = config_dir / "credentials.encrypted.json"
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = config_dir / f"credentials.backup.{timestamp}.json"

    print("=" * 70)
    print("ETL CREDENTIALS MIGRATION")
    print("=" * 70)
    print()

    # Step 1: Check master key
    print("[1/6] Checking master key...")
    master_key = os.getenv("ETL_MASTER_KEY")
    if not master_key:
        print()
        print("ERROR: ETL_MASTER_KEY environment variable not set!")
        print()
        print("To set it:")
        print("  Windows: set ETL_MASTER_KEY=your-base64-key")
        print("  Linux:   export ETL_MASTER_KEY=your-base64-key")
        print()
        print("To generate a key:")
        print("  python scripts/generate_key.py")
        print()
        sys.exit(1)
    print("      Master key found.")

    # Step 2: Check plaintext file exists
    print("[2/6] Checking source file...")
    if not plaintext_path.exists():
        print()
        print(f"ERROR: Plaintext credentials not found at:")
        print(f"       {plaintext_path}")
        print()
        sys.exit(1)
    print(f"      Found: {plaintext_path}")

    # Step 3: Create backup
    print("[3/6] Creating backup...")
    shutil.copy2(plaintext_path, backup_path)
    print(f"      Backup saved to: {backup_path}")

    # Step 4: Load plaintext credentials
    print("[4/6] Loading plaintext credentials...")
    try:
        with open(plaintext_path, "r", encoding="utf-8") as f:
            credentials = json.load(f)

        # Count sensitive fields
        def count_passwords(obj, count=0):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k.lower() in ("password", "senha", "secret", "token", "api_key"):
                        if isinstance(v, str) and v:
                            count += 1
                    elif isinstance(v, (dict, list)):
                        count = count_passwords(v, count)
            elif isinstance(obj, list):
                for item in obj:
                    count = count_passwords(item, count)
            return count

        pwd_count = count_passwords(credentials)
        print(f"      Loaded successfully. Found {pwd_count} sensitive fields to encrypt.")
    except json.JSONDecodeError as e:
        print()
        print(f"ERROR: Invalid JSON in credentials file: {e}")
        sys.exit(1)

    # Step 5: Encrypt
    print("[5/6] Encrypting credentials with AES-256-GCM...")
    try:
        crypto = CryptoService(master_key)
        encrypted = crypto.encrypt_credentials(credentials)

        with open(encrypted_path, "w", encoding="utf-8") as f:
            json.dump(encrypted, f, indent=4, ensure_ascii=False)

        print(f"      Encrypted file saved to: {encrypted_path}")
    except Exception as e:
        print()
        print(f"ERROR: Encryption failed: {e}")
        sys.exit(1)

    # Step 6: Validate
    print("[6/6] Validating encryption...")
    try:
        with open(encrypted_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        decrypted = crypto.decrypt_credentials(loaded)

        # Compare a sample password
        original_pwd = None
        decrypted_pwd = None

        # Find first password in original
        def find_first_password(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k.lower() == "password" and isinstance(v, str) and v:
                        return v
                    elif isinstance(v, dict):
                        result = find_first_password(v)
                        if result:
                            return result
            return None

        original_pwd = find_first_password(credentials)
        decrypted_pwd = find_first_password(decrypted)

        if original_pwd and original_pwd == decrypted_pwd:
            print("      Validation PASSED - Decryption successful!")
        elif not original_pwd:
            print("      No passwords found to validate (empty credentials?)")
        else:
            print("      WARNING: Validation may have issues")

    except Exception as e:
        print()
        print(f"ERROR: Validation failed: {e}")
        print()
        print("The encrypted file may be corrupted. Restoring from backup...")
        if backup_path.exists():
            shutil.copy2(backup_path, encrypted_path)
        sys.exit(1)

    # Success!
    print()
    print("=" * 70)
    print("MIGRATION COMPLETE!")
    print("=" * 70)
    print()
    print(f"  Backup:    {backup_path}")
    print(f"  Encrypted: {encrypted_path}")
    print()
    print("Next steps:")
    print()
    print("  1. Verify the application works with encrypted credentials")
    print("  2. Delete the plaintext file (after verification):")
    print(f"     del {plaintext_path}")
    print()
    print("  3. Delete the backup (after verification):")
    print(f"     del {backup_path}")
    print()
    print("  4. Ensure ETL_MASTER_KEY is set in your production environment")
    print()
    print("=" * 70)


if __name__ == "__main__":
    migrate_credentials()
