from app.ai.prompts.system_prompt import get_system_prompt, BASE_SYSTEM_PROMPT
from app.ai.prompts.action_plan_prompt import ACTION_PLAN_USER_PROMPT
from app.ai.prompts.urgency_prompt import URGENCY_CLASSIFICATION_PROMPT
from app.ai.prompts.rights_prompt import RIGHTS_SUMMARY_PROMPT
from app.ai.prompts.checklist_prompt import DOCUMENT_CHECKLIST_PROMPT
from app.ai.prompts.spanish_prompt import SPANISH_TRANSLATION_PROMPT

__all__ = [
    "get_system_prompt",
    "BASE_SYSTEM_PROMPT",
    "ACTION_PLAN_USER_PROMPT",
    "URGENCY_CLASSIFICATION_PROMPT",
    "RIGHTS_SUMMARY_PROMPT",
    "DOCUMENT_CHECKLIST_PROMPT",
    "SPANISH_TRANSLATION_PROMPT"
]
