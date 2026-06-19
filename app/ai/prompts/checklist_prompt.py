DOCUMENT_CHECKLIST_PROMPT = """
Generate a situation-specific document checklist for a renter in {state}, {county}
facing {situation_type} with {urgency_days} days until eviction.

Return ONLY JSON matching this schema:
{{
  "documents": [
    {{
      "document": "Lease agreement",
      "why_needed": "Proves tenancy terms",
      "where_to_get": "Your landlord or your copy",
      "is_critical": true
    }}
  ],
  "disclaimer": "This is informational guidance only, not legal advice. Contact Legal Aid for legal questions."
}}
"""
