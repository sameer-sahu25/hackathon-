from app.ai.services.claude_service import ClaudeService
from app.ai.schemas.action_plan import ActionPlanResponse, ActionPlanContext
from app.models.intake import Intake


class ActionPlanService:
    def __init__(self):
        self.claude = ClaudeService()

    async def generate_plan_from_intake(self, intake: Intake) -> ActionPlanResponse:
        context = ActionPlanContext(
            state=intake.state,
            county=intake.county,
            urgency_days=intake.urgency_days,
            income_monthly=intake.income_monthly,
            household_size=intake.household_size,
            situation_type=intake.situation_type.value,
            has_received_notice=intake.has_received_notice,
            language="EN"
        )
        
        return await self.claude.generate_action_plan(context)
