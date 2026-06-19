from app.ai.services.claude_service import ClaudeService


class TranslationService:
    def __init__(self):
        self.claude = ClaudeService()

    async def translate(self, content: str, target_lang: str = "ES") -> str:
        return await self.claude.translate_content(content, target_lang)
