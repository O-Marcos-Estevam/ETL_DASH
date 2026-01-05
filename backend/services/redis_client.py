"""
Redis Streams Client - For Distributed WebSocket

Uses Redis Streams instead of Pub/Sub for guaranteed message delivery.
Consumer groups ensure each message is processed by each instance.

Features:
- Graceful degradation if Redis unavailable
- Automatic reconnection
- Message persistence with configurable retention
- Consumer group support for horizontal scaling
"""
import asyncio
import json
import logging
import socket
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, Callable, Any, Dict, List

logger = logging.getLogger(__name__)

# Check if redis is available
try:
    import redis.asyncio as aioredis
    from redis.exceptions import ConnectionError as RedisConnectionError, ResponseError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None
    RedisConnectionError = Exception
    ResponseError = Exception
    logger.warning("Redis not available - install with: pip install redis")


class MessageType(str, Enum):
    """Types of WebSocket messages"""
    LOG = "log"
    STATUS = "status"
    JOB_COMPLETE = "job_complete"


@dataclass
class StreamMessage:
    """Message format for Redis Streams"""
    type: MessageType
    payload: dict
    source_instance: str
    timestamp: str = ""

    def to_dict(self) -> Dict[str, str]:
        """Convert to dict for Redis XADD"""
        return {
            "type": self.type.value,
            "payload": json.dumps(self.payload),
            "source": self.source_instance
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str], msg_id: str = "") -> "StreamMessage":
        """Create from Redis stream entry"""
        return cls(
            type=MessageType(data.get("type", "log")),
            payload=json.loads(data.get("payload", "{}")),
            source_instance=data.get("source", "unknown"),
            timestamp=msg_id
        )


class RedisStreamClient:
    """
    Redis Streams client for distributed WebSocket messaging.

    Uses Streams (not Pub/Sub) for:
    - Message persistence
    - Guaranteed delivery via consumer groups
    - Automatic cleanup with MAXLEN
    """

    STREAM_NAME = "etl:events"
    CONSUMER_GROUP = "ws_consumers"
    MAX_STREAM_LENGTH = 10000  # Keep last 10k messages

    def __init__(
        self,
        redis_url: str,
        channel_prefix: str = "etl",
        socket_timeout: float = 5.0
    ):
        self.redis_url = redis_url
        self.channel_prefix = channel_prefix
        self.socket_timeout = socket_timeout

        # Generate unique instance ID
        hostname = socket.gethostname()[:8]
        self.instance_id = f"{hostname}-{uuid.uuid4().hex[:8]}"

        self._redis: Optional[Any] = None
        self._connected = False
        self._running = False
        self._listener_task: Optional[asyncio.Task] = None
        self._handler: Optional[Callable] = None
        self._reconnect_task: Optional[asyncio.Task] = None

        logger.info(f"RedisStreamClient created: instance={self.instance_id}")

    @property
    def stream_name(self) -> str:
        return f"{self.channel_prefix}:{self.STREAM_NAME.split(':')[1]}"

    @property
    def is_connected(self) -> bool:
        return self._connected and self._redis is not None

    async def connect(self) -> bool:
        """
        Connects to Redis server.

        Returns:
            True if connected successfully, False otherwise
        """
        if not REDIS_AVAILABLE:
            logger.warning("Redis library not available")
            return False

        try:
            self._redis = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_timeout
            )

            # Test connection
            await self._redis.ping()
            self._connected = True
            logger.info(f"Connected to Redis: {self.redis_url}")

            # Ensure consumer group exists
            await self._ensure_consumer_group()

            return True

        except (RedisConnectionError, Exception) as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self._connected = False
            self._redis = None
            return False

    async def _ensure_consumer_group(self):
        """Creates consumer group if it doesn't exist"""
        try:
            await self._redis.xgroup_create(
                self.stream_name,
                self.CONSUMER_GROUP,
                mkstream=True,
                id="0"
            )
            logger.info(f"Created consumer group: {self.CONSUMER_GROUP}")
        except ResponseError as e:
            if "BUSYGROUP" in str(e):
                # Group already exists
                pass
            else:
                raise

    async def disconnect(self):
        """Disconnects from Redis"""
        self._running = False

        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self._reconnect_task:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass

        if self._redis:
            await self._redis.close()
            self._redis = None

        self._connected = False
        logger.info("Disconnected from Redis")

    async def publish(self, message: StreamMessage) -> bool:
        """
        Publishes a message to the stream.

        Args:
            message: The message to publish

        Returns:
            True if published successfully
        """
        if not self.is_connected:
            return False

        try:
            await self._redis.xadd(
                self.stream_name,
                message.to_dict(),
                maxlen=self.MAX_STREAM_LENGTH,
                approximate=True
            )
            return True

        except (RedisConnectionError, Exception) as e:
            logger.error(f"Error publishing to Redis: {e}")
            self._connected = False
            return False

    async def publish_log(self, log_entry: dict) -> bool:
        """Publishes a log entry"""
        message = StreamMessage(
            type=MessageType.LOG,
            payload=log_entry,
            source_instance=self.instance_id
        )
        return await self.publish(message)

    async def publish_status(
        self,
        sistema_id: str,
        status: str,
        progresso: int = 0,
        mensagem: str = ""
    ) -> bool:
        """Publishes a status update"""
        message = StreamMessage(
            type=MessageType.STATUS,
            payload={
                "sistema_id": sistema_id,
                "status": status,
                "progresso": progresso,
                "mensagem": mensagem
            },
            source_instance=self.instance_id
        )
        return await self.publish(message)

    async def publish_job_complete(
        self,
        job_id: int,
        status: str,
        duracao: int = 0
    ) -> bool:
        """Publishes a job completion event"""
        message = StreamMessage(
            type=MessageType.JOB_COMPLETE,
            payload={
                "job_id": job_id,
                "status": status,
                "duracao_segundos": duracao
            },
            source_instance=self.instance_id
        )
        return await self.publish(message)

    async def subscribe(self, handler: Callable[[StreamMessage], Any]):
        """
        Subscribes to the stream and processes messages.

        Args:
            handler: Async function to handle incoming messages
        """
        if not self.is_connected:
            logger.warning("Cannot subscribe - not connected to Redis")
            return

        self._handler = handler
        self._running = True

        self._listener_task = asyncio.create_task(
            self._listen_loop(),
            name=f"redis_listener_{self.instance_id}"
        )

        logger.info(f"Subscribed to stream: {self.stream_name}")

    async def _listen_loop(self):
        """Main loop for consuming messages from stream"""
        consumer_name = self.instance_id

        while self._running:
            try:
                if not self.is_connected:
                    # Try to reconnect
                    await asyncio.sleep(5)
                    await self.connect()
                    continue

                # Read new messages for this consumer
                messages = await self._redis.xreadgroup(
                    self.CONSUMER_GROUP,
                    consumer_name,
                    {self.stream_name: ">"},  # Only new messages
                    count=10,
                    block=1000  # 1 second block
                )

                if messages:
                    for stream, entries in messages:
                        for msg_id, data in entries:
                            try:
                                stream_msg = StreamMessage.from_dict(data, msg_id)

                                # Skip messages from self
                                if stream_msg.source_instance == self.instance_id:
                                    await self._redis.xack(
                                        self.stream_name,
                                        self.CONSUMER_GROUP,
                                        msg_id
                                    )
                                    continue

                                # Process message
                                if self._handler:
                                    if asyncio.iscoroutinefunction(self._handler):
                                        await self._handler(stream_msg)
                                    else:
                                        self._handler(stream_msg)

                                # Acknowledge message
                                await self._redis.xack(
                                    self.stream_name,
                                    self.CONSUMER_GROUP,
                                    msg_id
                                )

                            except Exception as e:
                                logger.error(f"Error processing message {msg_id}: {e}")
                                # Still acknowledge to prevent redelivery
                                await self._redis.xack(
                                    self.stream_name,
                                    self.CONSUMER_GROUP,
                                    msg_id
                                )

            except asyncio.CancelledError:
                break
            except (RedisConnectionError, Exception) as e:
                logger.error(f"Error in listener loop: {e}")
                self._connected = False
                await asyncio.sleep(5)  # Wait before retry

    def get_stats(self) -> dict:
        """Returns client statistics"""
        return {
            "instance_id": self.instance_id,
            "connected": self._connected,
            "stream_name": self.stream_name,
            "consumer_group": self.CONSUMER_GROUP,
            "running": self._running
        }


# Singleton instance
_client_instance: Optional[RedisStreamClient] = None


def get_redis_client() -> Optional[RedisStreamClient]:
    """Returns the Redis client singleton"""
    return _client_instance


def create_redis_client(
    redis_url: str,
    channel_prefix: str = "etl",
    socket_timeout: float = 5.0
) -> RedisStreamClient:
    """Creates and returns Redis client singleton"""
    global _client_instance
    _client_instance = RedisStreamClient(
        redis_url=redis_url,
        channel_prefix=channel_prefix,
        socket_timeout=socket_timeout
    )
    return _client_instance
