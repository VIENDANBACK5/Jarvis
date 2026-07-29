import pytest

from backend.graph import agent


@pytest.mark.asyncio
async def test_agent_returns_response():
    result = await agent.ainvoke({"query": "test query"})
    assert "response" in result
    # Mock LLM router trả về response mock không rỗng
    assert len(result["response"]) > 0


@pytest.mark.asyncio
async def test_agent_handles_empty_query():
    result = await agent.ainvoke({"query": ""})
    # Theo thiết kế, query rỗng sẽ trả về error hoặc response
    assert "error" in result or "response" in result

