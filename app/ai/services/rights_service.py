from app.ai.services.claude_service import ClaudeService


class RightsService:
    def __init__(self):
        self.claude = ClaudeService()

    async def get_state_rights(self, state: str, language: str = "EN") -> dict:
        return await self.claude.generate_rights_summary(state, language)
