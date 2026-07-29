from langchain_openai import ChatOpenAI
from backend.config import get_settings


def get_anthropic_client(model_name: str = None, temperature: float = None) -> ChatOpenAI:
    settings = get_settings()
    model = model_name or "claude-3-5-sonnet"
    temp = temperature if temperature is not None else settings.llm_temperature
    
    # Sử dụng base_url của Agent Router nếu được khai báo
    base_url = "https://agentrouter.org/v1"
    api_key = settings.anthropic_api_key or "sk-KniNseOboXi5Zr4anQ7BiZQg1b7N41L8ybi9ePxgNgxs8B46"
    
    return ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=temp,
    )
