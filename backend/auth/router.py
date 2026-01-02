"""
Authentication Router

API endpoints for login, logout, token refresh, and user management.
"""
from fastapi import APIRouter, HTTPException, Depends, Request, status
from typing import List
import logging

from .models import (
    LoginRequest, Token, LoginResponse, LoginResponseUser, UserCreate, UserResponse, UserUpdate,
    PasswordChangeRequest, RefreshTokenRequest, UserRole
)
from .security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, decode_token
)
from .database import (
    get_user_by_username, get_user_by_id, create_user, get_all_users,
    update_last_login, update_password, update_user, delete_user,
    increment_failed_attempts, reset_failed_attempts, is_account_locked,
    store_refresh_token, revoke_refresh_token, revoke_all_user_tokens,
    is_refresh_token_valid, check_rate_limit
)
from .dependencies import get_current_user, require_admin
from .config import auth_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(request: Request, login_data: LoginRequest):
    """
    Authenticate user and return JWT tokens.

    - Rate limited to 5 attempts per minute per IP
    - Account locks after 5 failed attempts for 15 minutes
    """
    client_ip = request.client.host if request.client else "unknown"

    # Check rate limit
    if check_rate_limit(client_ip, "/api/auth/login", auth_settings.RATE_LIMIT_LOGIN):
        logger.warning(f"Rate limit exceeded for login from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )

    # Check if account is locked
    if is_account_locked(login_data.username):
        logger.warning(f"Login attempt on locked account: {login_data.username} from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account temporarily locked. Try again later."
        )

    # Verify credentials
    user = get_user_by_username(login_data.username)

    if not user or not verify_password(login_data.password, user.hashed_password):
        if user:
            increment_failed_attempts(user.id)
        logger.warning(f"Failed login for: {login_data.username} from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Reset failed attempts on successful login
    reset_failed_attempts(user.id)
    update_last_login(user.id)

    # Create tokens
    access_token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=UserRole(user.role)
    )

    refresh_token, token_hash = create_refresh_token(
        user_id=user.id,
        username=user.username,
        role=UserRole(user.role)
    )

    # Store refresh token hash
    store_refresh_token(
        user_id=user.id,
        token_hash=token_hash,
        expires_days=auth_settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    logger.info(f"Successful login: {login_data.username} from {client_ip}")

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=LoginResponseUser(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role.value,
            is_active=user.is_active
        )
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_data: RefreshTokenRequest):
    """
    Refresh access token using refresh token.

    - Validates refresh token
    - Issues new access token and rotates refresh token
    """
    payload = decode_token(refresh_data.refresh_token)

    if not payload or payload.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Verify refresh token is in database and not revoked
    if not is_refresh_token_valid(refresh_data.refresh_token, payload.user_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked or expired"
        )

    user = get_user_by_username(payload.sub)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found or disabled"
        )

    # Revoke old refresh token
    revoke_refresh_token(refresh_data.refresh_token)

    # Create new tokens (token rotation)
    access_token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=UserRole(user.role)
    )

    new_refresh_token, token_hash = create_refresh_token(
        user_id=user.id,
        username=user.username,
        role=UserRole(user.role)
    )

    store_refresh_token(
        user_id=user.id,
        token_hash=token_hash,
        expires_days=auth_settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(
    refresh_data: RefreshTokenRequest,
    current_user=Depends(get_current_user)
):
    """
    Logout user by revoking refresh token.
    """
    revoke_refresh_token(refresh_data.refresh_token)
    logger.info(f"User logged out: {current_user.username}")
    return {"message": "Successfully logged out"}


@router.post("/logout-all")
async def logout_all_sessions(current_user=Depends(get_current_user)):
    """
    Logout from all sessions by revoking all refresh tokens.
    """
    revoke_all_user_tokens(current_user.id)
    logger.info(f"All sessions logged out for: {current_user.username}")
    return {"message": "Successfully logged out from all sessions"}


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user=Depends(get_current_user)
):
    """
    Change user password.

    - Requires current password verification
    - Revokes all refresh tokens after password change
    """
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    new_hash = get_password_hash(password_data.new_password)
    update_password(current_user.id, new_hash)

    # Revoke all tokens to force re-login
    revoke_all_user_tokens(current_user.id)

    logger.info(f"Password changed for: {current_user.username}")
    return {"message": "Password changed successfully. Please login again."}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user=Depends(get_current_user)):
    """Get current authenticated user info"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


# Admin-only endpoints

@router.get("/users", response_model=List[UserResponse])
async def list_users(current_user=Depends(require_admin)):
    """List all users (admin only)"""
    return get_all_users()


@router.post("/users", response_model=UserResponse)
async def create_new_user(user_data: UserCreate, current_user=Depends(require_admin)):
    """Create new user (admin only)"""
    existing = get_user_by_username(user_data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    hashed_password = get_password_hash(user_data.password)
    user = create_user(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role
    )

    logger.info(f"New user created: {user_data.username} by {current_user.username}")
    return user


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, current_user=Depends(require_admin)):
    """Get user by ID (admin only)"""
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: int,
    user_update: UserUpdate,
    current_user=Depends(require_admin)
):
    """Update user (admin only)"""
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    update_user(
        user_id=user_id,
        email=user_update.email,
        role=user_update.role,
        is_active=user_update.is_active
    )

    updated_user = get_user_by_id(user_id)
    logger.info(f"User updated: {user.username} by {current_user.username}")

    return UserResponse(
        id=updated_user.id,
        username=updated_user.username,
        email=updated_user.email,
        role=updated_user.role,
        is_active=updated_user.is_active,
        created_at=updated_user.created_at,
        last_login=updated_user.last_login
    )


@router.delete("/users/{user_id}")
async def delete_user_endpoint(user_id: int, current_user=Depends(require_admin)):
    """Delete user (admin only)"""
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    delete_user(user_id)
    logger.info(f"User deleted: {user.username} by {current_user.username}")

    return {"message": f"User {user.username} deleted successfully"}
