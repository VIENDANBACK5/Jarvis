import pytest
from unittest.mock import patch
from backend.services.llm.router import LLMRouter


def test_local_model_routing():
    with patch("backend.services.llm.router.get_ollama_client") as mock_ollama, \
         patch("backend.services.llm.router.get_openai_client") as mock_openai, \
         patch("backend.services.llm.router.get_deepseek_client") as mock_deepseek:

        # 1. Test deepseek-r1 gets routed to ollama
        LLMRouter.get_client("deepseek-r1:8b")
        mock_ollama.assert_called_once_with(model_name="deepseek-r1:8b", temperature=None)
        mock_ollama.reset_mock()

        # 2. Test qwen coder gets routed to ollama
        LLMRouter.get_client("qwen2.5-coder:32b")
        mock_ollama.assert_called_once_with(model_name="qwen2.5-coder:32b", temperature=None)
        mock_ollama.reset_mock()

        # 3. Test llama gets routed to ollama
        LLMRouter.get_client("llama3.3:70b")
        mock_ollama.assert_called_once_with(model_name="llama3.3:70b", temperature=None)
        mock_ollama.reset_mock()

        # 4. Test normal deepseek gets routed to deepseek provider
        LLMRouter.get_client("deepseek-chat")
        mock_deepseek.assert_called_once_with(model_name="deepseek-chat", temperature=None)
