"""
Circuit Breaker Pattern Implementation

Provides resilient fallback when external services (like Redis) fail.
Prevents cascading failures by failing fast after multiple errors.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Service is failing, all requests go to fallback
- HALF_OPEN: Testing if service recovered
"""
import asyncio
import logging
import time
from enum import Enum
from typing import Callable, TypeVar, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(str, Enum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Service down, using fallback
    HALF_OPEN = "half_open" # Testing recovery


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for async operations with automatic fallback.

    Usage:
        breaker = CircuitBreaker(name="redis", failure_threshold=3)

        async def redis_op():
            return await redis.publish(...)

        async def fallback_op():
            return await local_broadcast(...)

        result = await breaker.call(redis_op, fallback_op)
    """
    name: str = "default"
    failure_threshold: int = 3
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 1

    # Internal state (not exposed)
    _failures: int = field(default=0, init=False)
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _last_failure_time: Optional[float] = field(default=None, init=False)
    _half_open_calls: int = field(default=0, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    @property
    def state(self) -> CircuitState:
        """Returns current circuit state"""
        return self._state

    @property
    def is_closed(self) -> bool:
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        return self._state == CircuitState.OPEN

    async def call(
        self,
        primary: Callable[[], Any],
        fallback: Callable[[], Any]
    ) -> Any:
        """
        Execute primary function with fallback on failure.

        Args:
            primary: Main function to try
            fallback: Fallback function if primary fails or circuit is open

        Returns:
            Result from primary or fallback
        """
        async with self._lock:
            # Check if we should transition from OPEN to HALF_OPEN
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info(f"[{self.name}] Circuit HALF_OPEN - testing recovery")
                else:
                    # Still open, use fallback
                    logger.debug(f"[{self.name}] Circuit OPEN - using fallback")
                    return await self._execute_fallback(fallback)

            # Check HALF_OPEN call limit
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    # Too many test calls, wait for results
                    return await self._execute_fallback(fallback)
                self._half_open_calls += 1

        # Try primary function
        try:
            result = await self._execute_primary(primary)

            # Success - reset circuit if in HALF_OPEN
            async with self._lock:
                if self._state == CircuitState.HALF_OPEN:
                    self._state = CircuitState.CLOSED
                    self._failures = 0
                    logger.info(f"[{self.name}] Circuit CLOSED - service recovered")
                elif self._state == CircuitState.CLOSED:
                    # Reset failure count on success
                    self._failures = 0

            return result

        except Exception as e:
            async with self._lock:
                self._failures += 1
                self._last_failure_time = time.time()

                if self._state == CircuitState.HALF_OPEN:
                    # Recovery test failed
                    self._state = CircuitState.OPEN
                    logger.warning(f"[{self.name}] Circuit OPEN - recovery test failed: {e}")
                elif self._failures >= self.failure_threshold:
                    # Threshold exceeded
                    self._state = CircuitState.OPEN
                    logger.warning(f"[{self.name}] Circuit OPEN - {self._failures} failures: {e}")

            # Use fallback
            return await self._execute_fallback(fallback)

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try recovery"""
        if self._last_failure_time is None:
            return True
        return (time.time() - self._last_failure_time) >= self.recovery_timeout

    async def _execute_primary(self, func: Callable) -> Any:
        """Execute primary function"""
        if asyncio.iscoroutinefunction(func):
            return await func()
        return func()

    async def _execute_fallback(self, func: Callable) -> Any:
        """Execute fallback function"""
        if asyncio.iscoroutinefunction(func):
            return await func()
        return func()

    def reset(self):
        """Manually reset the circuit breaker"""
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._last_failure_time = None
        self._half_open_calls = 0
        logger.info(f"[{self.name}] Circuit manually reset")

    def trip(self):
        """Manually trip (open) the circuit breaker"""
        self._state = CircuitState.OPEN
        self._last_failure_time = time.time()
        logger.warning(f"[{self.name}] Circuit manually tripped")

    def get_stats(self) -> dict:
        """Returns circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self._state.value,
            "failures": self._failures,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure": self._last_failure_time
        }
