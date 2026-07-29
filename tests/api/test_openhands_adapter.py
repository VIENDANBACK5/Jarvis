import pytest
from backend.api.openhands_adapter import OpenHandsEventAdapter
from backend.runtime.event import RuntimeEvent


def test_openhands_event_adapter_mapping():
    # 1. Test Jarvis -> OpenHands
    event = RuntimeEvent(
        event_type="PATCH_GENERATED",
        payload={"detail": "Generated patch in main.py", "patch": "+ def fix(): pass"}
    )
    oh_obs = OpenHandsEventAdapter.jarvis_event_to_openhands(event)

    assert oh_obs["observation"] == "edit"
    assert "Generated Patch" in oh_obs["content"]

    # 2. Test OpenHands -> Jarvis Action
    oh_action = {
        "action": "edit",
        "args": {"path": "auth.py", "content": "+ fix"}
    }
    jarvis_cmd = OpenHandsEventAdapter.openhands_action_to_jarvis(oh_action)

    assert jarvis_cmd["tool"] == "edit_file"
    assert jarvis_cmd["kwargs"]["filepath"] == "auth.py"
