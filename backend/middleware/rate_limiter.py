"""
Rate Limiting Middleware

Protects API endpoints from abuse with per-IP rate limiting.
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from typing import Dict
import asyncio
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using in-memory storage.

    For production with multiple workers, consider using Redis.
    """

    def __init__(self, app, default_limit: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.requests: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: asyncio.Task | None = None

        # Endpoint-specific limits (requests per minute)
        self.endpoint_limits = {
            "/api/auth/login": 5,
            "/api/auth/refresh": 10,
            "/api/execute": 10,
            "/api/cancel": 10,
            "/ws": 10,
        }

        # Endpoints to skip rate limiting
        self.skip_endpoints = {
            "/api/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        }

    async def dispatch(self, request: Request, call_next):
        # Start cleanup task on first request (when event loop is available)
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self.cleanup_old_entries())

        # Skip rate limiting for certain endpoints
        path = request.url.path
        if path in self.skip_endpoints:
            return await call_next(request)

        # Skip static files
        if path.startswith("/static/") or path.startswith("/assets/"):
            return await call_next(request)

        client_ip = self._get_client_ip(request)

        # Find matching endpoint limit
        limit = self.default_limit
        for endpoint, endpoint_limit in self.endpoint_limits.items():
            if path.startswith(endpoint):
                limit = endpoint_limit
                break

        # Check rate limit
        async with self._lock:
            is_limited = self._check_rate_limit(client_ip, path, limit)

        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": str(self.window_seconds)}
            )

        response = await call_next(request)

        # Add rate limit headers
        async with self._lock:
            remaining = self._get_remaining(client_ip, path, limit)

        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(self.window_seconds)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, considering proxies"""
        # Check for forwarded headers (when behind proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Direct connection
        return request.client.host if request.client else "unknown"

    def _check_rate_limit(self, key: str, endpoint: str, limit: int) -> bool:
        """
        Check if request should be rate limited.

        Returns True if rate limited, False if allowed.
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)

        cache_key = f"{key}:{endpoint}"

        if cache_key in self.requests:
            entry = self.requests[cache_key]

            if entry["window_start"] < window_start:
                # Window expired, reset
                self.requests[cache_key] = {
                    "count": 1,
                    "window_start": now
                }
                return False
            elif entry["count"] >= limit:
                return True
            else:
                entry["count"] += 1
                return False
        else:
            self.requests[cache_key] = {
                "count": 1,
                "window_start": now
            }
            return False

    def _get_remaining(self, key: str, endpoint: str, limit: int) -> int:
        """Get remaining requests in current window"""
        cache_key = f"{key}:{endpoint}"

        if cache_key in self.requests:
            return limit - self.requests[cache_key]["count"]

        return limit

    async def cleanup_old_entries(self):
        """Periodically clean up old rate limit entries to prevent memory leak"""
        logger.info("Rate limiter cleanup task started")
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes

                async with self._lock:
                    now = datetime.now()
                    cutoff = now - timedelta(seconds=self.window_seconds * 2)

                    to_delete = [
                        key for key, entry in self.requests.items()
                        if entry["window_start"] < cutoff
                    ]

                    for key in to_delete:
                        del self.requests[key]

                    if to_delete:
                        logger.debug(f"Rate limiter cleanup: removed {len(to_delete)} stale entries")
            except asyncio.CancelledError:
                logger.info("Rate limiter cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Rate limiter cleanup error: {e}")
