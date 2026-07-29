import os
from langchain_openai import ChatOpenAI
from backend.config import get_settings


def get_deepseek_client(model_name: str = None, temperature: float = None) -> ChatOpenAI:
    settings = get_settings()
    model = model_name or "deepseek-chat"
    temp = temperature if temperature is not None else settings.llm_temperature
    
    # Check for DEEPSEEK_API_KEY in environment or settings
    api_key = os.getenv("DEEPSEEK_API_KEY") or settings.openai_api_key
    
    return ChatOpenAI(
        model=model,
        base_url="https://api.deepseek.com/v1",
        api_key=api_key,
        temperature=temp,
    )
