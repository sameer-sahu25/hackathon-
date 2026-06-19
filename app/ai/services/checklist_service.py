from app.ai.services.claude_service import ClaudeService
from app.ai.schemas.checklist import ChecklistResponse
from app.ai.schemas.urgency import IntakeData
from app.models.intake import Intake


class ChecklistService:
    def __init__(self):
        self.claude = ClaudeService()

    async def generate_from_intake(self, intake: Intake) -> ChecklistResponse:
        data = IntakeData(
            state=intake.state,
            county=intake.county,
            urgency_days=intake.urgency_days,
            income_monthly=intake.income_monthly,
            household_size=intake.household_size,
            situation_type=intake.situation_type.value,
            has_received_notice=intake.has_received_notice,
            language="EN"
        )
        
        return await self.claude.generate_checklist(data)
