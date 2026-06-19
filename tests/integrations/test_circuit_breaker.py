import time
import pytest
from app.integrations.shared.circuit_breaker import CircuitBreaker, CircuitState


async def failing_task():
    raise Exception("Test failure")


async def success_task():
    return "Success!"


@pytest.mark.asyncio
async def test_circuit_starts_closed():
    """Test circuit breaker starts in closed state."""
    cb = CircuitBreaker("test")
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_opens_after_threshold():
    """Test circuit opens after failure threshold is hit."""
    cb = CircuitBreaker("test", failure_threshold=2)
    with pytest.raises(Exception):
        await cb(failing_task)
    with pytest.raises(Exception):
        await cb(failing_task)
    assert cb.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_circuit_half_open_after_timeout():
    """Test circuit moves to half-open after timeout after recovery time."""
    cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0.1)
    with pytest.raises(Exception):
        await cb(failing_task)  # triggers open
    time.sleep(0.2)  # wait past recovery time
    await cb._check_state()
    assert cb.state == CircuitState.HALF_OPEN


@pytest.mark.asyncio
async def test_circuit_closes_after_success_in_half_open():
    """Test circuit closes after successful call in half-open."""
    cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0.1)
    with pytest.raises(Exception):
        await cb(failing_task)
    time.sleep(0.2)  # move to half open
    cb.state = CircuitState.HALF_OPEN
    result = await cb(success_task)
    assert result == "Success!"
    assert cb.state == CircuitState.CLOSED
