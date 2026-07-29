from langchain_openai import ChatOpenAI
from backend.config import get_settings


def get_gemini_client(model_name: str = None, temperature: float = None) -> ChatOpenAI:
    settings = get_settings()
    model = model_name or "gemini-1.5-pro"
    temp = temperature if temperature is not None else settings.llm_temperature
    
    # Sử dụng Google Gemini OpenAI-compatible endpoint
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    api_key = settings.google_api_key or "none"
    
    return ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=temp,
    )
