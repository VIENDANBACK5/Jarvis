import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class LocalLLMProvider:
    """Quản lý kết nối tới các mô hình mã nguồn mở chạy local (Ollama / vLLM)."""

    def __init__(self, base_url: str = "http://localhost:11434/v1"):
        self.base_url = base_url
        self.supported_models = [
            "qwen2.5-coder:7b",
            "qwen2.5-coder:32b",
            "llama3.3:70b",
            "deepseek-r1:8b"
        ]

    def test_connection(self) -> bool:
        """Kiểm tra kết nối mock tới local model server."""
        logger.info(f"LocalLLMProvider: Checking connection to {self.base_url}")
        return True

    def generate_completion(self, model_name: str, prompt: str, temperature: float = 0.2) -> str:
        """Gọi sinh văn bản từ mô hình mã nguồn mở local."""
        if model_name not in self.supported_models:
            logger.warning(f"Model {model_name} not tested. Proceeding anyway.")
        
        logger.info(f"LocalLLMProvider: Generating response using {model_name} (Temp: {temperature})")
        # Giả lập suy luận của Qwen Coder / DeepSeek R1
        if "deepseek-r1" in model_name:
            return "<think>Analyzing repository and fixing auth timeout</think>\n[PATCH] Apply deepseek timeout fix"
        return "[PATCH] Applied local open-source model patch"
