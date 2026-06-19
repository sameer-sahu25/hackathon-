import hashlib
import logging

logger = logging.getLogger(__name__)

SCRUB_FIELDS = [
    "phone", "phone_number", "income", "income_monthly",
    "ssn", "address", "full_address", "email",
    "password", "hashed_password", "access_token", "refresh_token",
    "authorization", "twilio_auth_token",
]


def scrub_dict(data: dict) -> dict:
    """Recursively scrub PII from a nested dictionary"""
    scrubbed_count = 0
    result = {}
    for key, value in data.items():
        if key.lower() in [f.lower() for f in SCRUB_FIELDS]:
            if key.lower() == "email":
                # Hash email instead of fully redacting for debugging
                if isinstance(value, str):
                    hashed = hashlib.sha256(value.encode()).hexdigest()[:16]
                    result[key] = f"[HASHED:{hashed}]"
                else:
                    result[key] = "[REDACTED]"
            else:
                result[key] = "[REDACTED]"
            scrubbed_count +=1
        elif isinstance(value, dict):
            nested_result, nested_count = scrub_dict(value)
            result[key] = nested_result
            scrubbed_count += nested_count
        elif isinstance(value, list):
            scrubbed_list = []
            for item in value:
                if isinstance(item, dict):
                    nested_result, nested_count = scrub_dict(item)
                    scrubbed_list.append(nested_result)
                    scrubbed_count += nested_count
                else:
                    scrubbed_list.append(item)
            result[key] = scrubbed_list
        else:
            result[key] = value

    if scrubbed_count >0:
        logger.debug(f"Scrubbed {scrubbed_count} PII fields from data")
    return result, scrubbed_count
