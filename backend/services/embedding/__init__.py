# Service for managing embeddings
from langchain_openai import OpenAIEmbeddings
from backend.config import get_settings


def get_embeddings():
    settings = get_settings()
    return OpenAIEmbeddings(
        api_key=settings.openai_api_key,
        model="text-embedding-3-small"
    )
