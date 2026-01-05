"""
Authentication Configuration

JWT and security settings for the ETL Dashboard.
"""
import os
from datetime import timedelta


class AuthSettings:
    """Authentication settings loaded from environment variables"""

    # JWT Configuration
    SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "CHANGE_ME_IN_PRODUCTION_USE_STRONG_SECRET_32_CHARS"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))

    # Password Policy
    MIN_PASSWORD_LENGTH: int = 8
    REQUIRE_SPECIAL_CHAR: bool = True
    REQUIRE_UPPERCASE: bool = True
    REQUIRE_NUMBER: bool = True

    # Account Security
    MAX_FAILED_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15

    # Rate Limiting (requests per minute)
    RATE_LIMIT_LOGIN: int = 5
    RATE_LIMIT_API: int = 100
    RATE_LIMIT_WEBSOCKET: int = 10

    # Cookie Configuration (HttpOnly for security)
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"  # True in production (HTTPS)
    COOKIE_SAMESITE: str = os.getenv("COOKIE_SAMESITE", "lax")  # "lax", "strict", or "none"
    COOKIE_DOMAIN: str = os.getenv("COOKIE_DOMAIN", "")  # Leave empty for same domain
    COOKIE_PATH: str = "/"
    ACCESS_TOKEN_COOKIE: str = "etl_access_token"
    REFRESH_TOKEN_COOKIE: str = "etl_refresh_token"

    @property
    def access_token_expires(self) -> timedelta:
        """Access token expiration timedelta"""
        return timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

    @property
    def refresh_token_expires(self) -> timedelta:
        """Refresh token expiration timedelta"""
        return timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)


# Singleton settings instance
auth_settings = AuthSettings()
