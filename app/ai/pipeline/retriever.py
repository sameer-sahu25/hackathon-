from typing import List
from app.ai.pipeline.vector_store import PineconeVectorStore, SearchResult
from app.ai.pipeline.reranker import ResultReranker


class Retriever:
    def __init__(self):
        self.vector_store = PineconeVectorStore()
        self.reranker = ResultReranker()

    async def retrieve(self, state: str, situation_type: str, county: str) -> List[SearchResult]:
        queries = [
            f"{state} tenant eviction notice requirements",
            f"{state} rental assistance programs {county}",
            f"{situation_type} tenant rights protections"
        ]
        
        all_results = []
        for query in queries:
            results = await self.vector_store.semantic_search(
                query=query,
                state=state,
                top_k=5
            )
            all_results.extend(results)
        
        return self.reranker.rerank(all_results, top_n=6)
