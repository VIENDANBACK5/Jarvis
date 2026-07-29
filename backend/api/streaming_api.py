import asyncio
import json
import logging
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.runtime.event_bus import EventBus
from backend.runtime.event import RuntimeEvent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["streaming"])


class StreamingManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"StreamingManager: Client connected for session {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"StreamingManager: Client disconnected for session {session_id}")

    async def send_event(self, session_id: str, event: RuntimeEvent):
        if session_id in self.active_connections:
            ws = self.active_connections[session_id]
            data = {
                "event_type": event.event_type,
                "payload": event.payload,
                "timestamp": event.timestamp
            }
            await ws.send_text(json.dumps(data))


streaming_manager = StreamingManager()


@router.websocket("/stream/{session_id}")
async def websocket_stream_endpoint(websocket: WebSocket, session_id: str):
    await streaming_manager.connect(session_id, websocket)
    try:
        while True:
            # Lắng nghe ping/pong hoặc lệnh client
            data = await websocket.receive_text()
            logger.info(f"WebSocket [{session_id}] received: {data}")
    except WebSocketDisconnect:
        streaming_manager.disconnect(session_id)
