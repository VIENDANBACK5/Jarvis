from langchain_openai import ChatOpenAI
from backend.config import get_settings


def get_ollama_client(model_name: str = None, temperature: float = None) -> ChatOpenAI:
    settings = get_settings()
    # If run in docker, localhost might need to be host.docker.internal or a configured url
    # We can fetch this from settings.database_url or a new env var if needed.
    # For now, default to http://localhost:11434/v1 or override via env
    model = model_name or "qwen2.5:7b-instruct"
    temp = temperature if temperature is not None else settings.llm_temperature
    
    return ChatOpenAI(
        model=model,
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        temperature=temp,
    )
