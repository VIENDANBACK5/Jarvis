import pytest
from backend.runtime.event import RuntimeEvent
from backend.runtime.event_bus import EventBus


def test_event_bus_publish_subscribe():
    bus = EventBus()
    received_events = []

    def on_task_created(event: RuntimeEvent):
        received_events.append(event)

    bus.subscribe("TASK_CREATED", on_task_created)

    event = RuntimeEvent(
        event_type="TASK_CREATED",
        payload={"detail": "Fix login bug"}
    )
    bus.publish(event)

    assert len(received_events) == 1
    assert received_events[0].event_type == "TASK_CREATED"
    assert received_events[0].payload["detail"] == "Fix login bug"
