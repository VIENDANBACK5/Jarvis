import pytest
from backend.models.local_providers import LocalLLMProvider


def test_local_llm_provider():
    provider = LocalLLMProvider()
    assert provider.test_connection() is True

    res_qwen = provider.generate_completion("qwen2.5-coder:7b", "Hello Coder")
    assert "local open-source" in res_qwen

    res_ds = provider.generate_completion("deepseek-r1:8b", "Solve deadlock")
    assert "<think>" in res_ds
