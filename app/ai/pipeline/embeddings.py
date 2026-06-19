from openai import AsyncOpenAI
from typing import List
from app.config import settings
from app.ai.pipeline.cache_service import CacheService
import logging

logger = logging.getLogger(__name__)


class OpenAIEmbeddings:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = getattr(settings, 'OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
        self.cache_service = CacheService()

    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text, using cache if available"""
        # Check cache first
        cached = await self.cache_service.get_embedding(text)
        if cached:
            return cached
        
        # If not cached, call OpenAI
        response = await self.client.embeddings.create(model=self.model, input=text)
        embedding = response.data[0].embedding
        
        # Cache the result
        await self.cache_service.set_embedding(text, embedding)
        
        return embedding

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts in batch, using cache where possible"""
        embeddings = []
        texts_to_embed = []
        indices = []
        
        # Check which texts are already cached
        for i, text in enumerate(texts):
            cached = await self.cache_service.get_embedding(text)
            if cached:
                embeddings.append(cached)
            else:
                texts_to_embed.append(text)
                indices.append(i)
        
        # Embed the remaining texts in a batch
        if texts_to_embed:
            response = await self.client.embeddings.create(model=self.model, input=texts_to_embed)
            
            # Cache the new embeddings and add to results
            for i, embedding in zip(indices, [d.embedding for d in response.data]):
                await self.cache_service.set_embedding(texts_to_embed[indices.index(i)], embedding)
                # Insert into correct position
                while len(embeddings) <= i:
                    embeddings.append(None)
                embeddings[i] = embedding
        
        return embeddings
