from typing import List
from app.ai.pipeline.vector_store import SearchResult


class ResultReranker:
    def __init__(self):
        self.authority_scores = {
            "HUD": 1.0,
            "STATE_LAW": 0.9,
            "NLIHC": 0.8,
            "COURT": 0.85,
            "211": 0.75
        }

    def rerank(self, results: List[SearchResult], top_n: int = 6) -> List[SearchResult]:
        scored_results = []
        
        for result in results:
            authority = result.metadata.get("source", "OTHER")
            authority_score = self.authority_scores.get(authority, 0.5)
            combined_score = result.score * authority_score
            scored_results.append((combined_score, result))
        
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        seen_texts = set()
        unique_results = []
        for score, result in scored_results:
            text_hash = hash(result.text)
            if text_hash not in seen_texts:
                seen_texts.add(text_hash)
                unique_results.append(result)
                if len(unique_results) >= top_n:
                    break
        
        return unique_results
