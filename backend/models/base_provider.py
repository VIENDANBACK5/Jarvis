import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class BaseLLMProvider:
    """Giao diện trừu tượng hóa nhà cung cấp mô hình (LLM Provider Interface)."""

    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        raise NotImplementedError("Each provider must implement generate()")

    def health_check(self) -> bool:
        raise NotImplementedError("Each provider must implement health_check()")

    def get_context_window(self) -> int:
        return 4096


class OpenAIProvider(BaseLLMProvider):
    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        logger.info(f"OpenAIProvider: Generating completion using {self.model_name}")
        return f"[OpenAI {self.model_name}] Synthesized patch based on prompt"

    def health_check(self) -> bool:
        return True


class OllamaProvider(BaseLLMProvider):
    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        logger.info(f"OllamaProvider: Generating completion using {self.model_name}")
        return f"[Ollama {self.model_name}] Synthesized patch based on prompt"

    def health_check(self) -> bool:
        return True


class VLLMProvider(BaseLLMProvider):
    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        logger.info(f"VLLMProvider: Generating completion using {self.model_name}")
        return f"[vLLM {self.model_name}] Synthesized patch based on prompt"

    def health_check(self) -> bool:
        return True
