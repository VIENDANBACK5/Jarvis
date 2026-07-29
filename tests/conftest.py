from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.main import app


@pytest_asyncio.fixture
async def client():
    """Async HTTP client for testing API endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def mock_llm_router(request):
    """Tự động mock LLM router để tránh gọi API thực tế khi chạy test."""
    if "test_local_model_routing" in request.node.name:
        yield None
        return

    from unittest.mock import patch, AsyncMock
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value = AsyncMock(content="Mocked LLM response")
    
    # Giả lập astream generator
    async def mock_stream(*args, **kwargs):
        yield AsyncMock(content="Mocked LLM response")
    mock_llm.astream = mock_stream

    with patch("backend.services.llm.router.LLMRouter.get_client", return_value=mock_llm) as p:
        yield p
