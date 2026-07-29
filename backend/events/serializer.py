import json
from typing import Dict, Any
from backend.events.event import PublicEvent, PublicEventType
from backend.runtime.event import RuntimeEvent


class EventSerializer:
    """Chuyển đổi các sự kiện nội bộ của Jarvis thành đối tượng PublicEvent chuẩn hóa độc lập UI."""

    @staticmethod
    def to_public_event(session_id: str, runtime_event: RuntimeEvent) -> PublicEvent:
        event_type_map = {
            "TASK_CREATED": PublicEventType.MISSION_STARTED,
            "MISSION_COMPLETED": PublicEventType.MISSION_FINISHED,
            "SEARCH_COMPLETED": PublicEventType.WORLD_MODEL_UPDATED,
            "FILE_READ": PublicEventType.FILE_OPENED,
            "PATCH_GENERATED": PublicEventType.PATCH_CREATED,
            "TEST_PASSED": PublicEventType.TOOL_EXECUTED,
        }

        public_type = event_type_map.get(runtime_event.event_type, PublicEventType.TOOL_EXECUTED)
        detail = runtime_event.payload.get("detail", "Event triggered")

        return PublicEvent(
            event_id=f"evt-{int(runtime_event.timestamp * 1000)}",
            session_id=session_id,
            event_type=public_type,
            summary=detail,
            payload=runtime_event.payload,
            timestamp=runtime_event.timestamp
        )

    @staticmethod
    def serialize_json(event: PublicEvent) -> str:
        return json.dumps(event.model_dump())
