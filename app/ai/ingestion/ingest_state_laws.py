from app.ai.pipeline.vector_store import PineconeVectorStore
from app.ai.ingestion.chunk_strategy import SmartChunker


class StateLawIngester:
    def __init__(self):
        self.vector_store = PineconeVectorStore()
        self.chunker = SmartChunker()

    async def ingest_state_laws(self, state: str):
        documents = []
        
        sample_laws = {
            "TX": [
                {
                    "title": "Texas Eviction Notice Requirements",
                    "content": "In Texas, landlords must give tenants a 3-day notice to quit or pay rent before filing for eviction for non-payment. For lease violations other than non-payment, landlords may give a 3-day notice to vacate.",
                    "url": "https://www.statutes.legis.state.tx.us/Docs/PR/htm/PR.24.htm"
                },
                {
                    "title": "Texas Tenant Rights",
                    "content": "Texas tenants have the right to safe and habitable housing. Landlords must make necessary repairs within a reasonable time. Tenants may be protected from retaliatory eviction.",
                    "url": "https://www.texaslawhelp.org"
                }
            ],
            "CA": [
                {
                    "title": "California Eviction Notice Requirements",
                    "content": "In California, landlords must give 3-day notice to pay rent or quit for non-payment. For lease violations, 3-day notice to cure or quit. For no-fault evictions, 30 or 60-day notice depending on tenancy length.",
                    "url": "https://www.courts.ca.gov"
                },
                {
                    "title": "California Rent Control",
                    "content": "Many California cities have rent control ordinances limiting rent increases and requiring just cause for eviction.",
                    "url": "https://www.dca.ca.gov"
                }
            ]
        }
        
        if state in sample_laws:
            laws = sample_laws[state]
            for law in laws:
                chunks = self.chunker.chunk(law["content"], {
                    "source": "STATE_LAW",
                    "state": state,
                    "content_type": "LAW",
                    "url": law["url"],
                    "authority_score": 0.9
                })
                documents.extend(chunks)
        
        if documents:
            await self.vector_store.upsert_documents(documents)
            print(f"Ingested {len(documents)} {state} law chunks")
        
        return len(documents)
