import pytest
from app.monitoring.sentry_config import scrub_event
from app.monitoring.middleware.pii_scrubber import scrub_dict


def test_scrub_event_user_context():
    event = {"user": {"id": "123", "email": "test@example.com", "ip": "1.2.3.4"}}
    scrubbed = scrub_event(event, {})
    assert scrubbed["user"] == {"id": "123"}


def test_scrub_event_extra_context():
    event = {"extra": {"phone": "123-456-7890", "state": "TX"}}
    scrubbed = scrub_event(event, {})
    assert scrubbed["extra"]["phone"] == "[REDACTED]"
    assert scrubbed["extra"]["state"] == "TX"


def test_scrub_event_request_data():
    event = {"request": {"data": {"income": 50000, "plan_id": "abc123"}}}
    scrubbed = scrub_event(event, {})
    assert scrubbed["request"]["data"]["income"] == "[REDACTED]"
    assert scrubbed["request"]["data"]["plan_id"] == "abc123"
