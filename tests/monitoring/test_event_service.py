import pytest
from unittest.mock import patch, AsyncMock
from app.monitoring.services.event_service import EventService


@pytest.mark.asyncio
async def test_track_event_validates_properties():
    with patch("app.monitoring.services.event_service.posthog") as mock_posthog:
        await EventService.track(
            event_name="session_started",
            distinct_id="test-user-123",
            properties={"language": "EN", "is_anonymous": True, "phone": "123-456-7890"}  # phone should be scrubbed
        )
        # Wait for background task
        import asyncio
        await asyncio.sleep(0.1)
        # Check that capture was called with scrubbed properties
        assert mock_posthog.capture.called
        call_kwargs = mock_posthog.capture.call_args[1]
        assert call_kwargs["distinct_id"] == "test-user-123"
        assert call_kwargs["event"] == "session_started"
        # Phone should NOT be present or should be scrubbed
        props = call_kwargs["properties"]
        assert "phone" not in props or props["phone"] == "[REDACTED]"


@pytest.mark.asyncio
async def test_track_event_failure_does_not_raise():
    with patch("app.monitoring.services.event_service.posthog.capture") as mock_capture:
        mock_capture.side_effect = Exception("PostHog down!")
        # Should NOT raise an exception
        await EventService.track(
            event_name="session_started",
            distinct_id="test-user-123"
        )
        import asyncio
        await asyncio.sleep(0.1)
        assert mock_capture.called
