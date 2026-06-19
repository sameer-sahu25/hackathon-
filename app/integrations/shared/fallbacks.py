from typing import List, Dict

FALLBACK_DATA = {
    "TX": [
        {
            "name": "211 Texas",
            "phone": "211",
            "website": "https://www.211texas.org",
            "description": "Free, confidential information and referral service for health and human services."
        },
        {
            "name": "National Coalition for the Homeless",
            "phone": "1-202-462-4822",
            "website": "https://www.nationalhomeless.org",
            "description": "Advocacy and resources for homeless individuals."
        },
        {
            "name": "Legal Aid of Texas",
            "website": "https://www.legalaidtx.org",
            "description": "Free legal assistance for low-income Texans."
        }
    ],
    "CA": [
        {
            "name": "211 California",
            "phone": "211",
            "website": "https://www.211ca.org",
            "description": "Free, confidential information and referral service."
        },
        {
            "name": "National Coalition for the Homeless",
            "phone": "1-202-462-4822",
            "website": "https://www.nationalhomeless.org",
            "description": "Advocacy and resources."
        },
        {
            "name": "Legal Services of Northern California",
            "website": "https://www.lsnc.net",
            "description": "Free legal help for low-income Californians."
        }
    ],
    "NY": [
        {
            "name": "211 New York",
            "phone": "211",
            "website": "https://www.211ny.org",
            "description": "Free, confidential information and referral service."
        },
        {
            "name": "National Coalition for the Homeless",
            "phone": "1-202-462-4822",
            "website": "https://www.nationalhomeless.org",
            "description": "Advocacy and resources."
        },
        {
            "name": "Legal Aid Society",
            "website": "https://www.legalaidnyc.org",
            "description": "Free legal assistance in NYC."
        }
    ],
    "FL": [
        {
            "name": "211 Florida",
            "phone": "211",
            "website": "https://www.211florida.org",
            "description": "Free, confidential information and referral service."
        },
        {
            "name": "National Coalition for the Homeless",
            "phone": "1-202-462-4822",
            "website": "https://www.nationalhomeless.org",
            "description": "Advocacy and resources."
        },
        {
            "name": "Florida Legal Services",
            "website": "https://www.floridalegalservices.org",
            "description": "Free legal help for low-income Floridians."
        }
    ],
    "IL": [
        {
            "name": "211 Illinois",
            "phone": "211",
            "website": "https://www.211illinois.org",
            "description": "Free, confidential information and referral service."
        },
        {
            "name": "National Coalition for the Homeless",
            "phone": "1-202-462-4822",
            "website": "https://www.nationalhomeless.org",
            "description": "Advocacy and resources."
        },
        {
            "name": "Land of Lincoln Legal Aid",
            "website": "https://www.lollegal.org",
            "description": "Free legal assistance in Illinois."
        }
    ]
}


def get_fallback_resources(state: str) -> List[Dict]:
    return FALLBACK_DATA.get(state.upper(), FALLBACK_DATA.get("TX", []))
