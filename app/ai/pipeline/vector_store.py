from pinecone import Pinecone, ServerlessSpec
from typing import Optional
from app.config import settings
from app.ai.pipeline.embeddings import OpenAIEmbeddings


class SearchResult:
    def __init__(self, id: str, score: float, metadata: dict, text: str):
        self.id = id
        self.score = score
        self.metadata = metadata
        self.text = text


class PineconeVectorStore:
    def __init__(self):
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.PINECONE_INDEX_NAME
        self.embeddings = OpenAIEmbeddings()
        
        # Create index if it doesn't exist
        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=settings.PINECONE_ENVIRONMENT)
            )
        self.index = self.pc.Index(self.index_name)

    async def upsert_documents(self, documents: list[dict]) -> int:
        batch_size = 100
        total_upserted = 0
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            texts = [doc["text"] for doc in batch]
            embeddings = await self.embeddings.embed_texts(texts)
            
            vectors = []
            for j, (doc, emb) in enumerate(zip(batch, embeddings)):
                vectors.append({
                    "id": doc.get("id", f"doc_{i + j}"),
                    "values": emb,
                    "metadata": doc.get("metadata", {})
                })
            
            self.index.upsert(vectors=vectors)
            total_upserted += len(vectors)
        
        return total_upserted

    async def semantic_search(
        self,
        query: str,
        state: str,
        top_k: int = 5,
        content_type: Optional[str] = None,
        min_score: float = 0.75
    ) -> list[SearchResult]:
        query_embedding = await self.embeddings.embed_text(query)
        
        filter_dict = {"state": state}
        if content_type:
            filter_dict["content_type"] = content_type
        
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            filter=filter_dict,
            include_metadata=True
        )
        
        search_results = []
        for match in results.matches:
            if match.score >= min_score:
                search_results.append(
                    SearchResult(
                        id=match.id,
                        score=match.score,
                        metadata=match.metadata,
                        text=match.metadata.get("text", "")
                    )
                )
        
        return search_results

    async def get_state_laws(self, state: str) -> list[SearchResult]:
        return await self.semantic_search(
            query="tenant rights eviction laws",
            state=state,
            content_type="LAW",
            top_k=10
        )

    async def get_assistance_programs(
        self,
        state: str,
        county: str,
        income: int,
        household_size: int
    ) -> list[SearchResult]:
        results = await self.semantic_search(
            query=f"rental assistance {county} {state}",
            state=state,
            content_type="PROGRAM",
            top_k=10
        )
        return results
