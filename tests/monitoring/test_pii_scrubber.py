import pytest
from app.monitoring.middleware.pii_scrubber import scrub_dict, SCRUB_FIELDS


def test_scrub_dict_top_level():
    data = {"phone": "123-456-7890", "name": "John Doe", "income": 50000}
    scrubbed, count = scrub_dict(data)
    assert scrubbed["phone"] == "[REDACTED]"
    assert scrubbed["income"] == "[REDACTED]"
    assert scrubbed["name"] == "John Doe"
    assert count ==2


def test_scrub_dict_nested():
    data = {"user": {"phone": "123-456-7890", "email": "test@example.com"}, "normal": "value"}
    scrubbed, count = scrub_dict(data)
    assert "HASHED" in scrubbed["user"]["email"]
    assert scrubbed["user"]["phone"] == "[REDACTED]"
    assert count ==2


def test_scrub_dict_list():
    data = {"people": [{"phone": "123-456-7890"}, {"phone": "098-765-4321"}, {"name": "Jane"}]}
    scrubbed, count = scrub_dict(data)
    for person in scrubbed["people"]:
        if "phone" in person:
            assert person["phone"] == "[REDACTED]"
    assert count ==2


def test_scrub_dict_case_insensitive():
    data = {"PHONE": "123-456-7890", "Email": "test@example.com"}
    scrubbed, count = scrub_dict(data)
    assert scrubbed["PHONE"] == "[REDACTED]"
    assert "HASHED" in scrubbed["Email"]
    assert count ==2


def test_scrub_dict_all_fields():
    data = {
        "phone": "123-456-7890",
        "phone_number": "098-765-4321",
        "income": 50000,
        "income_monthly": 4000,
        "ssn": "123-45-6789",
        "address": "123 Main St",
        "full_address": "123 Main St, Austin TX",
        "email": "test@example.com",
        "password": "testpass",
        "hashed_password": "hashed123",
        "access_token": "token123",
        "refresh_token": "token456",
        "authorization": "Bearer token789",
        "twilio_auth_token": "twilio123"
    }
    scrubbed, count = scrub_dict(data)
    for key in data:
        if key.lower() != "email":
            assert scrubbed[key] == "[REDACTED]"
        else:
            assert "HASHED" in scrubbed[key]
    assert count == len(data)
