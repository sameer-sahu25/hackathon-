from typing import List
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from app.config import settings
import logging

logger = logging.getLogger(__name__)

embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)

try:
    vectorstore = PineconeVectorStore(
        index_name=settings.PINECONE_INDEX_NAME,
        embedding=embeddings,
        pinecone_api_key=settings.PINECONE_API_KEY
    )
except Exception as e:
    logger.warning(f"Failed to initialize Pinecone vector store: {e}")
    vectorstore = None


async def retrieve_relevant_docs(
    query: str,
    state: str,
    situation_type: str,
    k: int = 5
) -> List[str]:
    if vectorstore is None:
        return []
    try:
        enhanced_query = f"{state} tenant rights: {situation_type}. {query}"
        docs = vectorstore.similarity_search(enhanced_query, k=k)
        return [doc.page_content for doc in docs]
    except Exception as e:
        logger.error(f"RAG retrieval failed: {e}")
        return []
