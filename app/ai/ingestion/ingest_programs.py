from app.ai.pipeline.vector_store import PineconeVectorStore
from app.ai.ingestion.chunk_strategy import SmartChunker
from app.config import settings
import httpx


class ProgramsIngester:
    def __init__(self):
        self.vector_store = PineconeVectorStore()
        self.chunker = SmartChunker()
        self.api_211_key = settings.API_211_KEY

    async def ingest_211_programs(self, state: str = "ALL"):
        documents = []
        
        sample_programs = [
            {
                "name": "Local 211 Hotline",
                "type": "HOTLINE",
                "description": "Free 24/7 hotline for housing, food, utility assistance, and more.",
                "phone": "211",
                "url": "https://www.211.org",
                "hours": "24/7"
            },
            {
                "name": "Legal Aid Society",
                "type": "LEGAL_AID",
                "description": "Free or low-cost legal assistance for tenants facing eviction.",
                "phone": "1-866-854-5972",
                "url": "https://www.lsc.gov",
                "hours": "Mon-Fri 9AM-5PM"
            },
            {
                "name": "National Low Income Housing Coalition",
                "type": "RESOURCE",
                "description": "Advocates for affordable housing and provides resources for tenants.",
                "phone": "202-662-1530",
                "url": "https://nlihc.org",
                "hours": "Mon-Fri 9AM-5PM"
            }
        ]
        
        for program in sample_programs:
            full_text = f"{program['name']}\n\n{program['description']}\n\nPhone: {program['phone']}\n\nHours: {program['hours']}"
            chunks = self.chunker.chunk(full_text, {
                "source": "211" if program["name"] == "Local 211 Hotline" else "NLIHC",
                "state": state,
                "content_type": "PROGRAM",
                "url": program["url"],
                "authority_score": 0.85
            })
            documents.extend(chunks)
        
        if documents:
            await self.vector_store.upsert_documents(documents)
            print(f"Ingested {len(documents)} program chunks")
        
        return len(documents)
