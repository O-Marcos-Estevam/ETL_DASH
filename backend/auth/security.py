"""
Security Utilities

Password hashing and JWT token operations.
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import hashlib
import secrets

from passlib.context import CryptContext
from jose import JWTError, jwt

from .config import auth_settings
from .models import TokenPayload, UserRole

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify.
        hashed_password: Bcrypt hash to verify against.

    Returns:
        True if password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password to hash.

    Returns:
        Bcrypt hash of the password.
    """
    return pwd_context.hash(password)


def create_access_token(
    user_id: int,
    username: str,
    role: UserRole,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: User's database ID.
        username: User's username.
        role: User's role.
        expires_delta: Optional custom expiration time.

    Returns:
        Encoded JWT access token.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + auth_settings.access_token_expires

    payload = {
        "sub": username,
        "user_id": user_id,
        "role": role.value if isinstance(role, UserRole) else role,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }

    return jwt.encode(
        payload,
        auth_settings.SECRET_KEY,
        algorithm=auth_settings.ALGORITHM
    )


def create_refresh_token(
    user_id: int,
    username: str,
    role: UserRole
) -> Tuple[str, str]:
    """
    Create a JWT refresh token and its hash for storage.

    Args:
        user_id: User's database ID.
        username: User's username.
        role: User's role.

    Returns:
        Tuple of (refresh_token, token_hash).
    """
    expire = datetime.utcnow() + auth_settings.refresh_token_expires

    payload = {
        "sub": username,
        "user_id": user_id,
        "role": role.value if isinstance(role, UserRole) else role,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": secrets.token_hex(16)  # Unique token ID
    }

    token = jwt.encode(
        payload,
        auth_settings.SECRET_KEY,
        algorithm=auth_settings.ALGORITHM
    )

    # Create hash for storage (to verify without storing the full token)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    return token, token_hash


def decode_token(token: str) -> Optional[TokenPayload]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string.

    Returns:
        TokenPayload if valid, None otherwise.
    """
    try:
        payload = jwt.decode(
            token,
            auth_settings.SECRET_KEY,
            algorithms=[auth_settings.ALGORITHM]
        )
        return TokenPayload(**payload)
    except JWTError:
        return None


def get_token_hash(token: str) -> str:
    """
    Get SHA256 hash of a token.

    Args:
        token: Token string.

    Returns:
        Hexadecimal hash string.
    """
    return hashlib.sha256(token.encode()).hexdigest()
