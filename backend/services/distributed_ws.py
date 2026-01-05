"""
Distributed WebSocket Manager - Supports Redis for horizontal scaling

Provides WebSocket message broadcasting with:
- Local-only mode (REDIS_ENABLED=false): Original behavior
- Distributed mode (REDIS_ENABLED=true): Redis Streams for multi-instance

Features:
- Graceful degradation with Circuit Breaker
- Automatic fallback to local-only if Redis fails
- Consumer groups for message distribution
"""
import asyncio
import logging
from typing import List, Optional, Dict, Any
from fastapi import WebSocket

from services.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class DistributedConnectionManager:
    """
    WebSocket manager with optional Redis support.

    Behavior:
    - REDIS_ENABLED=false: Works locally (same as original)
    - REDIS_ENABLED=true: Broadcasts via Redis to other instances

    Uses Circuit Breaker pattern for resilient fallback.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._redis_client = None
        self._redis_enabled = False
        self._initialized = False
        self._circuit_breaker = CircuitBreaker(
            name="redis_ws",
            failure_threshold=3,
            recovery_timeout=30.0
        )

    async def initialize(self):
        """
        Initializes Redis connection if enabled.
        Should be called on application startup.
        """
        if self._initialized:
            return

        from config import settings

        self._redis_enabled = settings.REDIS_ENABLED

        if self._redis_enabled:
            from services.redis_client import create_redis_client

            self._redis_client = create_redis_client(
                redis_url=settings.REDIS_URL,
                channel_prefix=settings.REDIS_CHANNEL_PREFIX,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT
            )

            connected = await self._redis_client.connect()

            if connected:
                # Subscribe to incoming messages from other instances
                await self._redis_client.subscribe(self._handle_redis_message)
                logger.info("WebSocket manager initialized with Redis (distributed mode)")
            else:
                logger.warning("Redis unavailable - using local-only mode")
                self._redis_client = None
        else:
            logger.info("WebSocket manager initialized (local mode)")

        self._initialized = True

    async def shutdown(self):
        """
        Shuts down Redis connection.
        Should be called on application shutdown.
        """
        if self._redis_client:
            await self._redis_client.disconnect()
            logger.info("WebSocket manager shutdown complete")

    async def connect(self, websocket: WebSocket):
        """Accepts a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.debug(f"WebSocket connected. Total: {self.connection_count}")

    def disconnect(self, websocket: WebSocket):
        """Removes a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.debug(f"WebSocket disconnected. Total: {self.connection_count}")

    async def broadcast_log(self, log_entry: dict):
        """
        Broadcasts a log entry to all connected clients.
        In distributed mode, also publishes to Redis.
        """
        message = {"type": "log", "payload": log_entry}

        # Always broadcast locally first
        await self._broadcast_local(message)

        # If Redis enabled, also publish to Redis
        if self._redis_enabled and self._redis_client:
            await self._publish_with_fallback(
                lambda: self._redis_client.publish_log(log_entry)
            )

    async def broadcast_status(
        self,
        sistema_id: str,
        status: str,
        progresso: int = 0,
        mensagem: str = None
    ):
        """
        Broadcasts a status update to all connected clients.
        In distributed mode, also publishes to Redis.
        """
        payload = {
            "sistema_id": sistema_id,
            "status": status,
            "progresso": progresso,
            "mensagem": mensagem
        }
        message = {"type": "status", "payload": payload}

        await self._broadcast_local(message)

        if self._redis_enabled and self._redis_client:
            await self._publish_with_fallback(
                lambda: self._redis_client.publish_status(
                    sistema_id, status, progresso, mensagem or ""
                )
            )

    async def broadcast_job_complete(
        self,
        job_id: int,
        status: str,
        duracao: int = 0
    ):
        """
        Broadcasts a job completion event to all connected clients.
        In distributed mode, also publishes to Redis.
        """
        payload = {
            "job_id": job_id,
            "status": status,
            "duracao_segundos": duracao
        }
        message = {"type": "job_complete", "payload": payload}

        await self._broadcast_local(message)

        if self._redis_enabled and self._redis_client:
            await self._publish_with_fallback(
                lambda: self._redis_client.publish_job_complete(
                    job_id, status, duracao
                )
            )

    async def _broadcast_local(self, message: dict):
        """Broadcasts message to local WebSocket connections only"""
        disconnect_list = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Error sending WebSocket message: {e}")
                disconnect_list.append(connection)

        # Clean up disconnected clients
        for conn in disconnect_list:
            self.disconnect(conn)

    async def _publish_with_fallback(self, redis_func):
        """
        Publishes to Redis with circuit breaker fallback.
        If Redis fails too many times, stops trying temporarily.
        """
        async def do_publish():
            return await redis_func()

        async def fallback():
            # Just log - local broadcast already done
            logger.debug("Redis publish skipped (circuit open)")
            return False

        await self._circuit_breaker.call(do_publish, fallback)

    async def _handle_redis_message(self, message):
        """
        Handles messages received from Redis (from other instances).
        Broadcasts to local WebSocket connections.
        """
        ws_message = {
            "type": message.type.value,
            "payload": message.payload
        }
        await self._broadcast_local(ws_message)

    @property
    def connection_count(self) -> int:
        """Returns number of active WebSocket connections"""
        return len(self.active_connections)

    @property
    def is_distributed(self) -> bool:
        """Returns True if running in distributed mode with Redis"""
        return (
            self._redis_client is not None and
            self._redis_client.is_connected
        )

    def get_stats(self) -> Dict[str, Any]:
        """Returns manager statistics"""
        stats = {
            "connections": self.connection_count,
            "distributed_mode": self.is_distributed,
            "redis_enabled": self._redis_enabled,
            "circuit_breaker": self._circuit_breaker.get_stats()
        }

        if self._redis_client:
            stats["redis"] = self._redis_client.get_stats()

        return stats


# Singleton instance (created in app.py)
_manager_instance: Optional[DistributedConnectionManager] = None


def get_ws_manager() -> Optional[DistributedConnectionManager]:
    """Returns the WebSocket manager singleton"""
    return _manager_instance


def create_ws_manager() -> DistributedConnectionManager:
    """Creates and returns WebSocket manager singleton"""
    global _manager_instance
    _manager_instance = DistributedConnectionManager()
    return _manager_instance
