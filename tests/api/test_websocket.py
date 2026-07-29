import pytest
from backend.events.event import PublicEvent, PublicEventType
from backend.events.serializer import EventSerializer
from backend.runtime.event import RuntimeEvent
from backend.api.websocket import WebSocketEventBroadcaster


def test_event_serializer():
    rt_event = RuntimeEvent(
        event_type="PATCH_GENERATED",
        payload={"detail": "Patch created in auth.py"}
    )

    pub_event = EventSerializer.to_public_event("session-123", rt_event)
    assert pub_event.session_id == "session-123"
    assert pub_event.event_type == PublicEventType.PATCH_CREATED

    json_str = EventSerializer.serialize_json(pub_event)
    assert "PatchCreated" in json_str


def test_websocket_broadcaster_safeguard():
    broadcaster = WebSocketEventBroadcaster()
    assert len(broadcaster.active_sockets) == 0

    broadcaster.unregister("non-existent-session")
    assert len(broadcaster.active_sockets) == 0
