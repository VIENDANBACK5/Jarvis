# pyrefly: ignore [missing-import]
from langchain_core.language_models.chat_models import BaseChatModel
from backend.services.llm.providers import (
    get_openai_client, 
    get_ollama_client, 
    get_deepseek_client,
    get_anthropic_client,
    get_gemini_client
)


class LLMRouter:
    @staticmethod
    def get_client(model_id: str, temperature: float = None) -> BaseChatModel:
        """Định tuyến và trả về client tương thích dựa trên model_id."""
        if not model_id:
            from backend.config import get_settings
            model_id = get_settings().model_name

        if "/" in model_id:
            provider, model_name = model_id.split("/", 1)
        else:
            model_id_lower = model_id.lower()
            if "gpt" in model_id_lower:
                provider, model_name = "openai", model_id
            elif "claude" in model_id_lower:
                provider, model_name = "anthropic", model_id
            elif "gemini" in model_id_lower:
                provider, model_name = "gemini", model_id
            elif "deepseek-r1" in model_id_lower:
                provider, model_name = "ollama", model_id
            elif "deepseek" in model_id_lower:
                provider, model_name = "deepseek", model_id
            elif "qwen" in model_id_lower or "llama" in model_id_lower or "mistral" in model_id_lower:
                provider, model_name = "ollama", model_id
            else:
                provider, model_name = "openai", model_id

        provider = provider.lower()
        if provider == "openai":
            return get_openai_client(model_name=model_name, temperature=temperature)
        elif provider == "ollama":
            return get_ollama_client(model_name=model_name, temperature=temperature)
        elif provider == "deepseek":
            return get_deepseek_client(model_name=model_name, temperature=temperature)
        elif provider == "anthropic":
            return get_anthropic_client(model_name=model_name, temperature=temperature)
        elif provider == "gemini":
            return get_gemini_client(model_name=model_name, temperature=temperature)
        else:
            raise ValueError(f"Provider '{provider}' không được hỗ trợ.")


def get_llm(model_id: str = None, temperature: float = None) -> BaseChatModel:
    """Helper function tiện lợi để lấy ChatModel."""
    return LLMRouter.get_client(model_id, temperature)
