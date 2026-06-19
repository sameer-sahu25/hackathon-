ACTION_PLAN_USER_PROMPT = """
RENTER SITUATION:
================
State: {state}
County: {county}
Days Until Eviction Deadline: {urgency_days}
Monthly Household Income: ${income_monthly}
Household Size: {household_size} people
Situation Type: {situation_type}
Has Received Notice: {has_received_notice}
Language Preference: {language}

RETRIEVED STATE LAW CONTEXT (from legal database):
==================================================
{rag_chunks}

PRIOR STEPS TAKEN THIS SESSION:
================================
{prior_steps}

YOUR TASK:
==========
Based on the renter's specific situation and the retrieved 
state law context above, generate a complete, personalized 
housing stability action plan.

CRITICAL: You MUST return ONLY valid JSON matching this schema.
No preamble. No explanation. No markdown. ONLY pure JSON.

REQUIRED JSON OUTPUT SCHEMA:
{{
  "urgency_level": "CRITICAL | HIGH | MEDIUM | LOW",
  "urgency_reason": "1-2 sentence plain language explanation",
  "urgency_color": "RED | ORANGE | YELLOW | GREEN",
  
  "action_steps": [
    {{
      "step_number": 1,
      "title": "Short action title (max 8 words)",
      "description": "Detailed instruction in plain language",
      "deadline_description": "Human readable deadline",
      "deadline_hours": 72,
      "contact_name": "Organization or person name",
      "contact_phone": "+1-xxx-xxx-xxxx or null",
      "contact_url": " https://...  or null",
      "responsible_party": "Renter | Legal Aid | Court | Agency",
      "is_critical": true | false,
      "estimated_time_minutes": 30
    }}
  ],
  
  "resources": [
    {{
      "name": "Full organization name",
      "type": "LEGAL_AID | RENTAL_ASSISTANCE | SHELTER | FOOD_BANK | MEDIATION | COURT | HOTLINE",
      "description": "1 sentence about what they do",
      "phone": "+1-xxx-xxx-xxxx",
      "url": " https://... ",
      "hours": "Mon-Fri 9AM-5PM or 24/7",
      "eligibility_notes": "Income limit or household size req",
      "is_free": true | false,
      "priority": 1
    }}
  ],
  
  "rights_summary": {{
    "headline": "Your key right in this situation (1 sentence)",
    "notice_requirement": "How many days notice required in state",
    "can_be_evicted_for": ["Non-payment", "Lease violation"],
    "cannot_be_evicted_for": ["Retaliation", "Discrimination"],
    "key_protections": ["Protection 1", "Protection 2"],
    "rent_control_applies": true | false,
    "just_cause_required": true | false
  }},
  
  "documents_needed": [
    {{
      "document": "Lease agreement",
      "why_needed": "Proves tenancy terms",
      "where_to_get": "Your landlord or your copy",
      "is_critical": true
    }}
  ],
  
  "escalation_flag": true | false,
  "escalation_reason": "Why human help is needed now or null",
  "escalation_contact": "211 | Legal Aid name | Shelter name",
  
  "disclaimer": "This is informational guidance only, not legal advice. Contact Legal Aid for legal questions.",
  
  "estimated_resolution_days": 14,
  "confidence_score": 0.92
}}
"""
