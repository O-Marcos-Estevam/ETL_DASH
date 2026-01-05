"""
Integration tests for distributed WebSocket (Redis)

Tests:
- Circuit Breaker functionality
- Redis Streams client (mocked)
- Distributed WebSocket manager with fallback
"""
import pytest
import asyncio
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.circuit_breaker import CircuitBreaker, CircuitState


# =============================================================================
# Circuit Breaker Tests
# =============================================================================

@pytest.mark.asyncio
class TestCircuitBreaker:
    """Tests for Circuit Breaker pattern"""

    async def test_circuit_starts_closed(self):
        """Circuit breaker starts in CLOSED state"""
        breaker = CircuitBreaker(name="test")

        assert breaker.state == CircuitState.CLOSED
        assert breaker.is_closed
        assert not breaker.is_open

    async def test_closed_passes_to_primary(self):
        """In CLOSED state, primary function is called"""
        breaker = CircuitBreaker(name="test")

        async def primary():
            return "primary_result"

        async def fallback():
            return "fallback_result"

        result = await breaker.call(primary, fallback)

        assert result == "primary_result"
        assert breaker.is_closed

    async def test_opens_after_threshold_failures(self):
        """Circuit opens after failure threshold is reached"""
        breaker = CircuitBreaker(name="test", failure_threshold=3)

        async def failing_primary():
            raise Exception("Service unavailable")

        async def fallback():
            return "fallback_result"

        # First 3 failures should open the circuit
        for i in range(3):
            result = await breaker.call(failing_primary, fallback)
            assert result == "fallback_result"

        assert breaker.is_open

    async def test_open_uses_fallback_immediately(self):
        """In OPEN state, fallback is used immediately without calling primary"""
        breaker = CircuitBreaker(name="test", failure_threshold=1)

        call_count = 0

        async def failing_primary():
            nonlocal call_count
            call_count += 1
            raise Exception("Service unavailable")

        async def fallback():
            return "fallback"

        # Trip the circuit
        await breaker.call(failing_primary, fallback)
        assert breaker.is_open

        # Reset call count
        call_count = 0

        # This should use fallback without calling primary
        result = await breaker.call(failing_primary, fallback)

        assert result == "fallback"
        assert call_count == 0  # Primary was not called

    async def test_half_open_after_recovery_timeout(self):
        """Circuit transitions to HALF_OPEN after recovery timeout"""
        breaker = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.1)

        async def failing_primary():
            raise Exception("Service unavailable")

        async def fallback():
            return "fallback"

        # Trip the circuit
        await breaker.call(failing_primary, fallback)
        assert breaker.is_open

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Next call should try primary (HALF_OPEN state)
        async def recovering_primary():
            return "recovered"

        result = await breaker.call(recovering_primary, fallback)

        assert result == "recovered"
        assert breaker.is_closed  # Success in HALF_OPEN closes the circuit

    async def test_half_open_reopens_on_failure(self):
        """Circuit reopens if test call fails in HALF_OPEN state"""
        breaker = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.1)

        async def failing_primary():
            raise Exception("Service unavailable")

        async def fallback():
            return "fallback"

        # Trip the circuit
        await breaker.call(failing_primary, fallback)
        assert breaker.is_open

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Try primary again (still failing)
        result = await breaker.call(failing_primary, fallback)

        assert result == "fallback"
        assert breaker.is_open  # Reopened

    async def test_success_resets_failure_count(self):
        """Successful calls reset the failure counter"""
        breaker = CircuitBreaker(name="test", failure_threshold=3)

        async def failing_primary():
            raise Exception("Fail")

        async def success_primary():
            return "success"

        async def fallback():
            return "fallback"

        # 2 failures
        await breaker.call(failing_primary, fallback)
        await breaker.call(failing_primary, fallback)
        assert breaker._failures == 2

        # 1 success resets counter
        await breaker.call(success_primary, fallback)
        assert breaker._failures == 0
        assert breaker.is_closed

    async def test_manual_reset(self):
        """Circuit can be manually reset"""
        breaker = CircuitBreaker(name="test", failure_threshold=1)

        async def failing():
            raise Exception("Fail")

        await breaker.call(failing, AsyncMock())
        assert breaker.is_open

        breaker.reset()

        assert breaker.is_closed
        assert breaker._failures == 0

    async def test_manual_trip(self):
        """Circuit can be manually tripped"""
        breaker = CircuitBreaker(name="test")
        assert breaker.is_closed

        breaker.trip()

        assert breaker.is_open

    def test_get_stats(self):
        """Stats are returned correctly"""
        breaker = CircuitBreaker(name="test_breaker", failure_threshold=5)

        stats = breaker.get_stats()

        assert stats["name"] == "test_breaker"
        assert stats["state"] == "closed"
        assert stats["failures"] == 0
        assert stats["failure_threshold"] == 5

    async def test_sync_functions_supported(self):
        """Circuit breaker works with sync functions"""
        breaker = CircuitBreaker(name="test")

        def sync_primary():
            return "sync_result"

        def sync_fallback():
            return "sync_fallback"

        result = await breaker.call(sync_primary, sync_fallback)

        assert result == "sync_result"


# =============================================================================
# Redis Client Tests (Mocked)
# =============================================================================

@pytest.mark.asyncio
class TestRedisStreamClient:
    """Tests for Redis Streams client with mocked Redis"""

    async def test_client_creation(self):
        """Client can be created"""
        from services.redis_client import RedisStreamClient

        client = RedisStreamClient(
            redis_url="redis://localhost:6379",
            channel_prefix="test"
        )

        assert client.redis_url == "redis://localhost:6379"
        assert client.channel_prefix == "test"
        assert client.instance_id is not None

    async def test_stream_name_uses_prefix(self):
        """Stream name includes prefix"""
        from services.redis_client import RedisStreamClient

        client = RedisStreamClient(
            redis_url="redis://localhost:6379",
            channel_prefix="myprefix"
        )

        assert "myprefix" in client.stream_name

    async def test_is_connected_false_when_not_connected(self):
        """is_connected returns False when not connected"""
        from services.redis_client import RedisStreamClient

        client = RedisStreamClient(redis_url="redis://localhost:6379")

        assert not client.is_connected

    async def test_publish_fails_when_not_connected(self):
        """Publishing fails gracefully when not connected"""
        from services.redis_client import RedisStreamClient, StreamMessage, MessageType

        client = RedisStreamClient(redis_url="redis://localhost:6379")

        message = StreamMessage(
            type=MessageType.LOG,
            payload={"test": "data"},
            source_instance="test"
        )

        result = await client.publish(message)

        assert result is False

    @patch('services.redis_client.REDIS_AVAILABLE', True)
    async def test_connect_handles_failure_gracefully(self):
        """Connect handles connection failure gracefully"""
        from services.redis_client import RedisStreamClient

        with patch('services.redis_client.aioredis') as mock_aioredis:
            mock_aioredis.from_url.return_value.ping = AsyncMock(
                side_effect=Exception("Connection refused")
            )

            client = RedisStreamClient(redis_url="redis://bad:6379")
            result = await client.connect()

            assert result is False
            assert not client.is_connected

    @patch('services.redis_client.REDIS_AVAILABLE', True)
    async def test_connect_success(self):
        """Connect succeeds with working Redis"""
        from services.redis_client import RedisStreamClient

        with patch('services.redis_client.aioredis') as mock_aioredis:
            mock_redis = MagicMock()
            mock_redis.ping = AsyncMock()
            mock_redis.xgroup_create = AsyncMock()
            mock_aioredis.from_url.return_value = mock_redis

            client = RedisStreamClient(redis_url="redis://localhost:6379")
            result = await client.connect()

            assert result is True
            assert client.is_connected

    def test_get_stats(self):
        """Stats are returned correctly"""
        from services.redis_client import RedisStreamClient

        client = RedisStreamClient(redis_url="redis://localhost:6379")

        stats = client.get_stats()

        assert "instance_id" in stats
        assert "connected" in stats
        assert "stream_name" in stats
        assert stats["connected"] is False


@pytest.mark.asyncio
class TestStreamMessage:
    """Tests for StreamMessage dataclass"""

    def test_message_to_dict(self):
        """Message converts to dict for Redis"""
        from services.redis_client import StreamMessage, MessageType

        message = StreamMessage(
            type=MessageType.LOG,
            payload={"level": "INFO", "sistema": "test"},
            source_instance="instance-1"
        )

        data = message.to_dict()

        assert data["type"] == "log"
        assert "level" in data["payload"]
        assert data["source"] == "instance-1"

    def test_message_from_dict(self):
        """Message can be created from Redis data"""
        from services.redis_client import StreamMessage, MessageType
        import json

        data = {
            "type": "status",
            "payload": json.dumps({"sistema_id": "maps", "status": "running"}),
            "source": "instance-2"
        }

        message = StreamMessage.from_dict(data, "1234-0")

        assert message.type == MessageType.STATUS
        assert message.payload["sistema_id"] == "maps"
        assert message.source_instance == "instance-2"
        assert message.timestamp == "1234-0"


# =============================================================================
# Distributed WebSocket Manager Tests
# =============================================================================

@pytest.mark.asyncio
class TestDistributedConnectionManager:
    """Tests for Distributed WebSocket Manager"""

    async def test_manager_creation(self):
        """Manager can be created"""
        from services.distributed_ws import DistributedConnectionManager

        manager = DistributedConnectionManager()

        assert manager.active_connections == []
        assert not manager._initialized

    async def test_local_mode_initialization(self):
        """Manager initializes in local mode when Redis disabled"""
        from services.distributed_ws import DistributedConnectionManager

        manager = DistributedConnectionManager()

        with patch('config.settings') as mock_settings:
            mock_settings.REDIS_ENABLED = False

            await manager.initialize()

            assert manager._initialized
            assert not manager._redis_enabled
            assert manager._redis_client is None

    async def test_connect_websocket(self):
        """WebSocket can be connected"""
        from services.distributed_ws import DistributedConnectionManager

        manager = DistributedConnectionManager()

        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()

        await manager.connect(mock_ws)

        assert mock_ws in manager.active_connections
        assert manager.connection_count == 1

    async def test_disconnect_websocket(self):
        """WebSocket can be disconnected"""
        from services.distributed_ws import DistributedConnectionManager

        manager = DistributedConnectionManager()

        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()

        await manager.connect(mock_ws)
        manager.disconnect(mock_ws)

        assert mock_ws not in manager.active_connections
        assert manager.connection_count == 0

    async def test_broadcast_log_local(self):
        """Log is broadcast to local connections"""
        from services.distributed_ws import DistributedConnectionManager

        manager = DistributedConnectionManager()

        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(mock_ws)
        await manager.broadcast_log({"level": "INFO", "sistema": "test"})

        mock_ws.send_json.assert_called_once()
        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "log"
        assert call_args["payload"]["level"] == "INFO"

    async def test_broadcast_status_local(self):
        """Status is broadcast to local connections"""
        from services.distributed_ws import DistributedConnectionManager

        manager = DistributedConnectionManager()

        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(mock_ws)
        await manager.broadcast_status("maps", "running", 50, "Processando...")

        mock_ws.send_json.assert_called_once()
        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "status"
        assert call_args["payload"]["sistema_id"] == "maps"
        assert call_args["payload"]["progresso"] == 50

    async def test_broadcast_job_complete_local(self):
        """Job complete is broadcast to local connections"""
        from services.distributed_ws import DistributedConnectionManager

        manager = DistributedConnectionManager()

        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(mock_ws)
        await manager.broadcast_job_complete(123, "completed", 45)

        mock_ws.send_json.assert_called_once()
        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "job_complete"
        assert call_args["payload"]["job_id"] == 123
        assert call_args["payload"]["duracao_segundos"] == 45

    async def test_failed_connection_is_removed(self):
        """Failed connections are removed on broadcast"""
        from services.distributed_ws import DistributedConnectionManager

        manager = DistributedConnectionManager()

        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock(side_effect=Exception("Connection closed"))

        await manager.connect(mock_ws)
        assert manager.connection_count == 1

        await manager.broadcast_log({"test": "data"})

        assert manager.connection_count == 0

    async def test_is_distributed_false_without_redis(self):
        """is_distributed returns False when Redis not connected"""
        from services.distributed_ws import DistributedConnectionManager

        manager = DistributedConnectionManager()

        assert not manager.is_distributed

    async def test_get_stats_local_mode(self):
        """Stats are returned correctly in local mode"""
        from services.distributed_ws import DistributedConnectionManager

        manager = DistributedConnectionManager()

        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        await manager.connect(mock_ws)

        stats = manager.get_stats()

        assert stats["connections"] == 1
        assert stats["distributed_mode"] is False
        assert "circuit_breaker" in stats


@pytest.mark.asyncio
class TestDistributedManagerWithRedis:
    """Tests for Distributed Manager with mocked Redis"""

    async def test_distributed_initialization(self):
        """Manager initializes in distributed mode with Redis"""
        from services.distributed_ws import DistributedConnectionManager

        manager = DistributedConnectionManager()

        with patch('config.settings') as mock_settings:
            mock_settings.REDIS_ENABLED = True
            mock_settings.REDIS_URL = "redis://localhost:6379"
            mock_settings.REDIS_CHANNEL_PREFIX = "test"
            mock_settings.REDIS_SOCKET_TIMEOUT = 5.0

            with patch('services.redis_client.create_redis_client') as mock_create:
                mock_client = MagicMock()
                mock_client.connect = AsyncMock(return_value=True)
                mock_client.subscribe = AsyncMock()
                mock_client.is_connected = True
                mock_create.return_value = mock_client

                await manager.initialize()

                assert manager._initialized
                assert manager._redis_enabled
                mock_client.subscribe.assert_called_once()

    async def test_broadcast_publishes_to_redis(self):
        """Broadcasting publishes to Redis when enabled"""
        from services.distributed_ws import DistributedConnectionManager

        manager = DistributedConnectionManager()
        manager._redis_enabled = True
        manager._redis_client = MagicMock()
        manager._redis_client.publish_log = AsyncMock(return_value=True)
        manager._redis_client.is_connected = True

        await manager.broadcast_log({"level": "INFO", "test": "data"})

        manager._redis_client.publish_log.assert_called_once()

    async def test_redis_failure_triggers_circuit_breaker(self):
        """Redis failures trigger circuit breaker"""
        from services.distributed_ws import DistributedConnectionManager

        manager = DistributedConnectionManager()
        manager._redis_enabled = True
        manager._redis_client = MagicMock()
        manager._redis_client.publish_log = AsyncMock(side_effect=Exception("Redis error"))
        manager._redis_client.is_connected = True

        # Multiple failures should open circuit
        for _ in range(5):
            await manager.broadcast_log({"test": "data"})

        assert manager._circuit_breaker.is_open

    async def test_handle_redis_message_broadcasts_locally(self):
        """Messages from Redis are broadcast to local connections"""
        from services.distributed_ws import DistributedConnectionManager
        from services.redis_client import StreamMessage, MessageType

        manager = DistributedConnectionManager()

        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()
        await manager.connect(mock_ws)

        # Simulate receiving message from Redis
        redis_message = StreamMessage(
            type=MessageType.LOG,
            payload={"level": "INFO", "sistema": "remote"},
            source_instance="other-instance"
        )

        await manager._handle_redis_message(redis_message)

        mock_ws.send_json.assert_called_once()
        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "log"
        assert call_args["payload"]["sistema"] == "remote"


# =============================================================================
# Fallback Behavior Tests
# =============================================================================

@pytest.mark.asyncio
class TestFallbackBehavior:
    """Tests for graceful degradation when Redis fails"""

    async def test_local_broadcast_continues_when_redis_fails(self):
        """Local broadcasts continue even when Redis fails"""
        from services.distributed_ws import DistributedConnectionManager

        manager = DistributedConnectionManager()
        manager._redis_enabled = True
        manager._redis_client = MagicMock()
        manager._redis_client.publish_log = AsyncMock(side_effect=Exception("Redis down"))
        manager._redis_client.is_connected = True

        # Connect a local WebSocket
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()
        await manager.connect(mock_ws)

        # Broadcast should still work locally
        await manager.broadcast_log({"level": "INFO", "test": "data"})

        # Local client should have received the message
        mock_ws.send_json.assert_called_once()

    async def test_circuit_recovery_resumes_redis(self):
        """After circuit recovery, Redis publishing resumes"""
        from services.distributed_ws import DistributedConnectionManager

        manager = DistributedConnectionManager()
        manager._redis_enabled = True
        manager._redis_client = MagicMock()
        manager._redis_client.is_connected = True
        manager._circuit_breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.1
        )

        call_count = 0

        async def failing_then_succeeding(log_entry):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Temporary failure")
            return True

        manager._redis_client.publish_log = failing_then_succeeding

        # First 2 calls fail, circuit opens
        await manager.broadcast_log({"test": 1})
        await manager.broadcast_log({"test": 2})
        assert manager._circuit_breaker.is_open

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Next call should try Redis again
        await manager.broadcast_log({"test": 3})

        # Should have attempted Redis (3 total calls)
        assert call_count == 3
