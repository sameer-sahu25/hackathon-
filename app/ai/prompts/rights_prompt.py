RIGHTS_SUMMARY_PROMPT = """
Based on the retrieved state law context below, create a plain-language
summary of tenant rights for renters in {state} facing {situation_type}.

STATE LAW CONTEXT:
{rag_chunks}

Return ONLY JSON matching this schema:
{{
  "headline": "Your key right in this situation (1 sentence)",
  "notice_requirement": "How many days notice required in state",
  "can_be_evicted_for": ["Non-payment", "Lease violation"],
  "cannot_be_evicted_for": ["Retaliation", "Discrimination"],
  "key_protections": ["Protection 1", "Protection 2"],
  "rent_control_applies": true | false,
  "just_cause_required": true | false,
  "disclaimer": "This is informational guidance only, not legal advice. Contact Legal Aid for legal questions."
}}
"""
