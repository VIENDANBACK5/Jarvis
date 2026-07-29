from pathlib import Path
import pytest
from backend.core.agent import AgentLoop
from backend.core.events import EventType
from backend.core.llm.base import Completion, LLMBackend, TextChunk
from backend.core.permissions import PermissionBroker
from backend.core.session import AgentSession
from backend.core.tools.read import ReadTool
from backend.core.tools.registry import ToolBox


class FakeLLMBackend(LLMBackend):
    model = "fake-model"
    provider = "fake"

    async def stream(self, system, messages, tools, max_tokens=8192, temperature=None):
        yield TextChunk(text="Analyzing project...")
        yield Completion(
            content=[{"type": "text", "text": "Analyzing project..."}],
            tool_calls=[],
            text="Analyzing project...",
            stop_reason="end_turn"
        )


@pytest.mark.asyncio
async def test_agent_loop_turn(tmp_path):
    ws = Path(tmp_path)
    session = AgentSession(workspace=ws)
    llm = FakeLLMBackend()
    tools = ToolBox()
    tools.register(ReadTool())
    permissions = PermissionBroker(workspace=ws)

    loop = AgentLoop(session=session, llm=llm, tools=tools, permissions=permissions)

    events = []
    async for evt in loop.run_turn("Inspect workspace"):
        events.append(evt)

    event_types = [e.type for e in events]
    assert EventType.NOTICE in event_types
    assert EventType.TEXT_DELTA in event_types
    assert EventType.TURN_COMPLETE in event_types
