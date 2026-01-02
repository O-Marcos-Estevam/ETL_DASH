"""
FastAPI Authentication Dependencies

Dependency injection functions for route protection.
"""
from fastapi import Depends, HTTPException, status, WebSocket, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List

from .security import decode_token
from .database import get_user_by_username
from .models import UserRole, UserInDB

# HTTP Bearer token extractor
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserInDB:
    """
    Validate JWT token and return current user.

    Use as a dependency in protected routes.

    Raises:
        HTTPException: 401 if token is invalid or expired.
        HTTPException: 403 if user is disabled.
    """
    token = credentials.credentials
    payload = decode_token(token)

    if not payload or payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = get_user_by_username(payload.sub)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    return user


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """
    Alias for get_current_user with active check.

    Convenience dependency for code readability.
    """
    return current_user


def require_role(allowed_roles: List[UserRole]):
    """
    Factory function to create role-based dependency.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role([UserRole.ADMIN]))])
        async def admin_endpoint():
            ...

    Or:
        @router.get("/admin-only")
        async def admin_endpoint(user: UserInDB = Depends(require_role([UserRole.ADMIN]))):
            ...
    """
    async def role_checker(
        current_user: UserInDB = Depends(get_current_user)
    ) -> UserInDB:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user

    return role_checker


# Convenience dependencies for common role checks
require_admin = require_role([UserRole.ADMIN])
require_viewer = require_role([UserRole.ADMIN, UserRole.VIEWER])


async def get_ws_user(
    websocket: WebSocket,
    token: str = Query(None)
) -> UserInDB:
    """
    Authenticate WebSocket connections via query parameter.

    Usage: ws://host/ws?token=<jwt_token>

    Raises:
        WebSocketException: Closes connection with appropriate code if auth fails.
    """
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token required"
        )

    payload = decode_token(token)

    if not payload or payload.type != "access":
        await websocket.close(code=4001, reason="Invalid token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user = get_user_by_username(payload.sub)

    if not user or not user.is_active:
        await websocket.close(code=4003, reason="User not found or disabled")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found or disabled"
        )

    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
) -> UserInDB | None:
    """
    Optionally authenticate user if token is provided.

    Returns None if no token or invalid token.
    Useful for endpoints that work with or without auth.
    """
    if not credentials:
        return None

    token = credentials.credentials
    payload = decode_token(token)

    if not payload or payload.type != "access":
        return None

    user = get_user_by_username(payload.sub)

    if not user or not user.is_active:
        return None

    return user
