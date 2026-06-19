import asyncio
import json
from typing import List
import logging
from app.config import settings
from app.ai.pipeline.retriever import Retriever
from app.ai.pipeline.cache_service import CacheService
from app.ai.pipeline.vector_store import SearchResult

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Full RAG orchestration pipeline with caching and parallel queries"""
    
    def __init__(self):
        self.retriever = Retriever()
        self.cache_service = CacheService()

    def _format_context(self, results: List[SearchResult]) -> str:
        """Format RAG results into a context string for Claude"""
        context_parts = []
        for i, result in enumerate(results, 1):
            source = result.metadata.get("source", "Unknown")
            url = result.metadata.get("url", "")
            context_parts.append(
                f"[SOURCE {i} - {source}] (Score: {result.score:.2f})\n"
                f"URL: {url}\n"
                f"CONTENT: {result.text}\n"
            )
        return "\n".join(context_parts)

    async def run(self, state: str, situation_type: str, county: str) -> str:
        """
        Run RAG pipeline:
        1. Check cache
        2. If not cached, run parallel RAG queries
        3. Deduplicate and rerank
        4. Cache and return formatted context
        """
        # Check cache first
        cached_chunks = await self.cache_service.get_rag_chunks(state, situation_type, county)
        if cached_chunks:
            logger.info("RAG cache hit, returning cached context")
            results = [
                SearchResult(
                    id=chunk["id"],
                    score=chunk["score"],
                    metadata=chunk["metadata"],
                    text=chunk["text"]
                )
                for chunk in cached_chunks
            ]
            return self._format_context(results)

        # Build search queries
        queries = [
            f"{state} tenant eviction notice requirements",
            f"{state} rental assistance programs {county}",
            f"{situation_type} tenant rights protections"
        ]

        # Run parallel RAG queries
        tasks = [
            self.retriever.vector_store.semantic_search(
                query=query,
                state=state,
                top_k=5,
                content_type=None,
                min_score=0.75
            )
            for query in queries
        ]
        all_results_flat = []
        for result_list in await asyncio.gather(*tasks):
            all_results_flat.extend(result_list)

        # Rerank and deduplicate
        final_results = self.retriever.reranker.rerank(all_results_flat, top_n=6)

        # Prepare chunks for caching
        chunks_to_cache = [
            {
                "id": res.id,
                "score": res.score,
                "metadata": res.metadata,
                "text": res.text
            }
            for res in final_results
        ]

        # Cache the results
        await self.cache_service.set_rag_chunks(state, situation_type, county, chunks_to_cache)

        # Log RAG retrieval
        import time
        logger.info(
            json.dumps({
                "event": "rag_retrieved",
                "state": state,
                "chunks_count": len(final_results),
                "avg_score": sum(res.score for res in final_results) / len(final_results) if final_results else 0.0,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            })
        )

        return self._format_context(final_results)
