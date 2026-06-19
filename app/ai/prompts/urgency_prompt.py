URGENCY_CLASSIFICATION_PROMPT = """
Classify the urgency of this housing situation.

SITUATION DATA:
- Days until eviction: {urgency_days}
- Has received notice: {has_received_notice}
- Situation type: {situation_type}
- State: {state}

Return ONLY this JSON, nothing else:
{{
  "urgency_level": "CRITICAL | HIGH | MEDIUM | LOW",
  "urgency_reason": "One sentence explanation",
  "urgency_color": "RED | ORANGE | YELLOW | GREEN",
  "show_911": false,
  "show_211": true,
  "hours_to_act": 48
}}

CLASSIFICATION RULES:
- CRITICAL = eviction in <48 hours OR physical danger present
- HIGH = eviction notice received, 3-14 days remaining
- MEDIUM = behind on rent, no notice yet, 15-30 days
- LOW = preventive, no immediate threat, 30+ days
"""
