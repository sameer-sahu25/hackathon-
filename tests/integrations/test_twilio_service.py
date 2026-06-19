import pytest
from unittest.mock import MagicMock, patch
from app.integrations.twilio.service import TwilioService


@pytest.fixture
def twilio_service():
    with patch("app.integrations.twilio.service.get_twilio_client") as mock_client:
        with patch("app.integrations.twilio.service.get_from_number") as mock_from:
            mock_from.return_value = "+18005551234"
            yield TwilioService()


@pytest.mark.asyncio
async def test_send_sms_success(twilio_service):
    """Test successful SMS send."""
    mock_message = MagicMock()
    mock_message.sid = "SM12345"
    mock_message.status = "queued"
    
    with patch.object(twilio_service.client.messages, "create") as mock_create:
        mock_create.return_value = mock_message
        result = await twilio_service.send_sms(to="+15125556789", body="Test!")
        assert result["sid"] == "SM12345"
        assert result["status"] == "queued"


@pytest.mark.asyncio
async def test_send_sms_invalid_phone(twilio_service):
    """Test invalid phone number raises error."""
    with pytest.raises(Exception):
        await twilio_service.send_sms(to="invalid", body="Test!")


@pytest.mark.asyncio
async def test_send_sms_fallback(twilio_service):
    """Test that SMS send falls back to local queue on failure."""
    with patch.object(twilio_service.client.messages, "create") as mock_create:
        mock_create.side_effect = Exception("Twilio down!")
        result = await twilio_service.send_sms(to="+15125556789", body="Test!")
        assert result["sid"].startswith("LOCAL_")
        assert result["status"] == "queued_fallback"
