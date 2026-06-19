import time
from enum import Enum
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 1
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.half_open_calls = 0

    async def __call__(self, func: Callable, *args, **kwargs) -> Any:
        await self._check_state()
        
        if self.state == CircuitState.OPEN:
            logger.warning(f"Circuit breaker '{self.name}' is OPEN, skipping call")
            raise Exception(f"Circuit '{self.name}' is open")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    async def _check_state(self):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                logger.info(f"Circuit breaker '{self.name}' moving to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
        elif self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                self.state = CircuitState.OPEN

    def _on_success(self):
        logger.info(f"Circuit breaker '{self.name}' success")
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.half_open_calls = 0

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        logger.warning(f"Circuit breaker '{self.name}' failure count: {self.failure_count}")
        
        if self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
            logger.error(f"Circuit breaker '{self.name}' OPENING")
            self.state = CircuitState.OPEN
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN


# Singleton circuit breakers per integration
_twilio_circuit: CircuitBreaker = None
_google_maps_circuit: CircuitBreaker = None
_hud_circuit: CircuitBreaker = None
_api_211_circuit: CircuitBreaker = None
_data_gov_circuit: CircuitBreaker = None


def get_twilio_circuit() -> CircuitBreaker:
    global _twilio_circuit
    if _twilio_circuit is None:
        _twilio_circuit = CircuitBreaker("twilio")
    return _twilio_circuit


def get_google_maps_circuit() -> CircuitBreaker:
    global _google_maps_circuit
    if _google_maps_circuit is None:
        _google_maps_circuit = CircuitBreaker("google_maps")
    return _google_maps_circuit


def get_hud_circuit() -> CircuitBreaker:
    global _hud_circuit
    if _hud_circuit is None:
        _hud_circuit = CircuitBreaker("hud")
    return _hud_circuit


def get_api_211_circuit() -> CircuitBreaker:
    global _api_211_circuit
    if _api_211_circuit is None:
        _api_211_circuit = CircuitBreaker("api_211")
    return _api_211_circuit


def get_data_gov_circuit() -> CircuitBreaker:
    global _data_gov_circuit
    if _data_gov_circuit is None:
        _data_gov_circuit = CircuitBreaker("data_gov")
    return _data_gov_circuit
