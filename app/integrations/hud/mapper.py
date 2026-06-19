from typing import Dict, Any


def normalize_hud_program(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": raw.get("program_name", "Unknown HUD Program"),
        "description": raw.get("description", ""),
        "state": raw.get("state"),
        "county": raw.get("county"),
        "eligibility": raw.get("eligibility_criteria", ""),
        "website": raw.get("website_url"),
        "phone": raw.get("phone_number"),
        "source": "HUD"
    }
