#!/usr/bin/env python3
"""
Generate a secure master key for credentials encryption.

This script generates a cryptographically secure 256-bit key
and provides instructions for setting it up.

Usage:
    python scripts/generate_key.py
"""
import base64
import secrets


def generate_master_key():
    """Generate a cryptographically secure master key."""
    # Generate 32 random bytes (256 bits)
    key_bytes = secrets.token_bytes(32)
    key_b64 = base64.b64encode(key_bytes).decode('ascii')

    print("=" * 70)
    print("ETL MASTER KEY GENERATED SUCCESSFULLY")
    print("=" * 70)
    print()
    print(f"Base64 Key: {key_b64}")
    print()
    print("-" * 70)
    print("SETUP INSTRUCTIONS")
    print("-" * 70)
    print()
    print("Option 1: Environment Variable (Recommended)")
    print()
    print("  Windows (CMD):")
    print(f"    set ETL_MASTER_KEY={key_b64}")
    print()
    print("  Windows (PowerShell):")
    print(f'    $env:ETL_MASTER_KEY="{key_b64}"')
    print()
    print("  Linux/Mac:")
    print(f"    export ETL_MASTER_KEY={key_b64}")
    print()
    print("-" * 70)
    print()
    print("Option 2: .env File")
    print()
    print("  Add to your .env file:")
    print(f"    ETL_MASTER_KEY={key_b64}")
    print()
    print("-" * 70)
    print()
    print("Option 3: Key File (for portable deployments)")
    print()
    print("  Save to config/.master_key:")
    print(f"    echo {key_b64} > config/.master_key")
    print()
    print("=" * 70)
    print("SECURITY WARNINGS")
    print("=" * 70)
    print()
    print("  1. NEVER commit this key to version control")
    print("  2. Use DIFFERENT keys for dev/staging/production")
    print("  3. Store securely - without this key, credentials CANNOT be decrypted")
    print("  4. Consider using a secrets manager in production")
    print()
    print("=" * 70)
    print()

    # Also save to a file for convenience (user can delete after copying)
    try:
        with open("GENERATED_KEY.txt", "w") as f:
            f.write(f"ETL_MASTER_KEY={key_b64}\n")
        print("Key also saved to: GENERATED_KEY.txt")
        print("(Delete this file after copying the key!)")
    except Exception:
        pass

    return key_b64


if __name__ == "__main__":
    generate_master_key()
