import logging
from typing import Dict, List, Callable
from backend.runtime.event import RuntimeEvent

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self):
        self._listeners: Dict[str, List[Callable[[RuntimeEvent], None]]] = {}

    def subscribe(self, event_type: str, callback: Callable[[RuntimeEvent], None]):
        """Đăng ký listener nhận sự kiện cho một loại event_type cụ thể."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def publish(self, event: RuntimeEvent):
        """Phát sóng sự kiện thời gian thực tới tất cả các listener đăng ký."""
        logger.info(f"EventBus [PUBLISH -> {event.event_type}]: {event.payload.get('detail', '')}")
        
        # Gọi cho listener cụ thể
        if event.event_type in self._listeners:
            for callback in self._listeners[event.event_type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"EventBus: Error in listener callback: {str(e)}")

        # Gọi cho listener lắng nghe toàn cục "*"
        if "*" in self._listeners:
            for callback in self._listeners["*"]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"EventBus: Error in global listener callback: {str(e)}")
