from app.ai.pipeline.vector_store import PineconeVectorStore
from app.ai.ingestion.chunk_strategy import SmartChunker
from app.config import settings
import httpx


class HUDIngester:
    def __init__(self):
        self.vector_store = PineconeVectorStore()
        self.chunker = SmartChunker()
        self.api_key = settings.HUD_API_KEY

    async def ingest_programs(self, state: str = "ALL"):
        documents = []
        
        sample_programs = [
            {
                "name": "Emergency Rental Assistance Program (ERAP)",
                "description": "Provides emergency rental and utility assistance to households experiencing financial hardship due to COVID-19 or other economic shocks.",
                "eligibility": "Households with income at or below 80% of area median income",
                "url": "https://www.hud.gov/topics/rental_assistance/erap",
                "phone": "1-800-569-4287"
            },
            {
                "name": "Housing Choice Voucher Program (Section 8)",
                "description": "Helps very low-income families, the elderly, and persons with disabilities afford safe, decent, and sanitary housing in the private market.",
                "eligibility": "Very low-income families, elderly, or persons with disabilities",
                "url": "https://www.hud.gov/topics/housing_choice_voucher_program_section_8",
                "phone": "1-800-955-2232"
            },
            {
                "name": "Public Housing Program",
                "description": "Provides affordable housing for low-income families, elderly, and persons with disabilities.",
                "eligibility": "Low-income families, elderly, or persons with disabilities",
                "url": "https://www.hud.gov/topics/public_housing",
                "phone": "1-800-955-2232"
            }
        ]
        
        for program in sample_programs:
            full_text = f"{program['name']}\n\n{program['description']}\n\nEligibility: {program['eligibility']}\n\nPhone: {program['phone']}"
            chunks = self.chunker.chunk(full_text, {
                "source": "HUD",
                "state": state,
                "content_type": "PROGRAM",
                "url": program["url"],
                "authority_score": 0.95
            })
            documents.extend(chunks)
        
        if documents:
            await self.vector_store.upsert_documents(documents)
            print(f"Ingested {len(documents)} HUD program chunks")
        
        return len(documents)
