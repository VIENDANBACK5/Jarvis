import json
import logging
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.events.event import PublicEvent, PublicEventType
from backend.events.serializer import EventSerializer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["events"])


class WebSocketEventBroadcaster:
    def __init__(self):
        self.active_sockets: Dict[str, WebSocket] = {}

    async def register(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_sockets[session_id] = websocket
        logger.info(f"Broadcaster: WebSocket connected for session {session_id}")

    def unregister(self, session_id: str):
        if session_id in self.active_sockets:
            del self.active_sockets[session_id]
            logger.info(f"Broadcaster: WebSocket disconnected for session {session_id}")

    async def broadcast_event(self, event: PublicEvent):
        if event.session_id in self.active_sockets:
            ws = self.active_sockets[event.session_id]
            json_payload = EventSerializer.serialize_json(event)
            await ws.send_text(json_payload)


event_broadcaster = WebSocketEventBroadcaster()


@router.websocket("/events/{session_id}")
async def websocket_event_endpoint(websocket: WebSocket, session_id: str):
    await event_broadcaster.register(session_id, websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            logger.info(f"WebSocket [{session_id}] client message: {msg}")
    except WebSocketDisconnect:
        event_broadcaster.unregister(session_id)
