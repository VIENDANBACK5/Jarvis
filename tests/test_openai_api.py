from unittest.mock import AsyncMock, patch
import pytest


@pytest.mark.asyncio
async def test_list_models(client):
    """Test endpoint GET /v1/models trả về đúng danh sách model và agent."""
    response = await client.get("/v1/models")
    assert response.status_code == 200
    
    data = response.json()
    assert "data" in data
    
    # Kiểm tra sự tồn tại của cả system model và custom agent
    model_ids = [m["id"] for m in data["data"]]
    assert "gpt-4o-mini" in model_ids
    assert "planner-agent" in model_ids
    assert "coder-agent" in model_ids


@pytest.mark.asyncio
@patch("backend.services.llm.router.LLMRouter.get_client")
async def test_chat_completions_agent(mock_get_client, client):
    """Test endpoint POST /v1/chat/completions khi gọi model là Agent."""
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value = AsyncMock(content="Kế hoạch: 1. Tạo repo, 2. Viết code.")
    mock_get_client.return_value = mock_llm

    payload = {
        "model": "planner-agent",
        "messages": [
            {"role": "user", "content": "Hãy lên kế hoạch phát triển dự án MyAI."}
        ],
        "stream": False
    }

    response = await client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "choices" in data
    assert len(data["choices"]) > 0
    assert data["choices"][0]["message"]["content"] == "Kế hoạch: 1. Tạo repo, 2. Viết code."
