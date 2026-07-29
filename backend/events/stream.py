import logging
from typing import List, Dict, Any

from backend.events.event import Event, Action, Observation

logger = logging.getLogger(__name__)


class EventStream:
    def __init__(self):
        self._events: List[Event] = []

    def add_event(self, event: Event):
        """Thêm một sự kiện mới vào luồng sự kiện."""
        self._events.append(event)
        logger.debug(f"EventStream: Added {event.event_type} | {event.event_id}")

    def get_events(self) -> List[Event]:
        """Lấy toàn bộ danh sách sự kiện hiện tại."""
        return self._events

    def clear(self):
        """Xóa toàn bộ lịch sử sự kiện."""
        self._events.clear()

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Chuyển đổi toàn bộ luồng sự kiện thành dạng danh sách JSON để lưu trữ."""
        return [e.model_dump() for e in self._events]

    def load_from_dict_list(self, dict_list: List[Dict[str, Any]]):
        """Khởi dựng lại luồng sự kiện từ danh sách cấu trúc JSON dict."""
        self.clear()
        for d in dict_list:
            e_type = d.get("event_type")
            if e_type == "action":
                self.add_event(Action(**d))
            elif e_type == "observation":
                self.add_event(Observation(**d))
            else:
                self.add_event(Event(**d))
