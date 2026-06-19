from typing import Dict, Any


def normalize_211_result(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": raw.get("organization_name", "Unknown 211 Organization"),
        "description": raw.get("service_description", ""),
        "address": raw.get("physical_address", ""),
        "phone": raw.get("phone_number"),
        "website": raw.get("website"),
        "source": "API_211"
    }
