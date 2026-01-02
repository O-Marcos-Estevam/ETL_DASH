"""
Authentication Pydantic Models

Data models for users, tokens, and authentication requests/responses.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum
import re


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    VIEWER = "viewer"


class UserCreate(BaseModel):
    """Request model for creating a new user"""
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = None
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.VIEWER

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v


class UserUpdate(BaseModel):
    """Request model for updating a user"""
    email: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Response model for user data"""
    id: int
    username: str
    email: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class UserInDB(UserResponse):
    """User model with hashed password (internal use)"""
    hashed_password: str


class Token(BaseModel):
    """Response model for authentication tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class LoginResponseUser(BaseModel):
    """User info returned in login response"""
    id: int
    username: str
    email: Optional[str] = None
    role: str
    is_active: bool = True


class LoginResponse(BaseModel):
    """Response model for login (includes user info)"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: LoginResponseUser


class TokenPayload(BaseModel):
    """JWT token payload structure"""
    sub: str  # username
    user_id: int
    role: str
    exp: datetime
    iat: datetime
    type: str  # "access" or "refresh"
    jti: Optional[str] = None  # JWT ID for refresh tokens


class LoginRequest(BaseModel):
    """Request model for login"""
    username: str
    password: str


class PasswordChangeRequest(BaseModel):
    """Request model for password change"""
    current_password: str
    new_password: str = Field(..., min_length=8)

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh"""
    refresh_token: str
