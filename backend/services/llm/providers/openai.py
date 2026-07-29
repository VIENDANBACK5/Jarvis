from langchain_openai import ChatOpenAI
from backend.config import get_settings


def get_openai_client(model_name: str = None, temperature: float = None) -> ChatOpenAI:
    settings = get_settings()
    model = model_name or settings.model_name or "gpt-4o-mini"
    temp = temperature if temperature is not None else settings.llm_temperature
    
    return ChatOpenAI(
        model=model,
        api_key=settings.openai_api_key,
        temperature=temp,
    )
