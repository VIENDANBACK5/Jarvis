"""REST and WebSocket routes for the real Jarvis Agent Core."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.core.agent import AgentLoop
from backend.core.events import AgentEvent
from backend.core.llm.factory import create_llm_backend
from backend.core.permissions import PermissionBroker
from backend.core.session import AgentSession
from backend.core.tools.bash import BashTool
from backend.core.tools.edit import EditTool
from backend.core.tools.glob import GlobTool
from backend.core.tools.grep import GrepTool
from backend.core.tools.read import ReadTool
from backend.core.tools.registry import ToolBox
from backend.core.tools.todo import TodoTool
from backend.core.tools.write import WriteTool
from backend.workspace.scanner import WorkspaceScanner

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/agent", tags=["agent_core"])

# Store active sessions and permission brokers
agent_sessions: Dict[str, AgentSession] = {}
agent_loops: Dict[str, AgentLoop] = {}
agent_permissions: Dict[str, PermissionBroker] = {}
active_websockets: Dict[str, list[WebSocket]] = {}


class CreateSessionRequest(BaseModel):
    workspace_dir: str = "."
    provider: Optional[str] = None
    model: Optional[str] = None


class MessageRequest(BaseModel):
    text: str


class PermissionResponseRequest(BaseModel):
    request_id: str
    allowed: bool
    always: bool = False


@router.post("/sessions")
def create_session(req: CreateSessionRequest) -> Dict[str, Any]:
    ws_dir = os.path.abspath(req.workspace_dir)
    session = AgentSession(workspace_dir=ws_dir)
    permissions = PermissionBroker()
    
    try:
        llm = create_llm_backend(provider=req.provider, model=req.model)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create LLM backend: {e}")

    tools = ToolBox()
    tools.register(ReadTool())
    tools.register(WriteTool())
    tools.register(EditTool())
    tools.register(BashTool())
    tools.register(GlobTool())
    tools.register(GrepTool())
    tools.register(TodoTool())

    loop_engine = AgentLoop(session=session, llm=llm, tools=tools, permissions=permissions)

    sid = session.session_id
    agent_sessions[sid] = session
    agent_loops[sid] = loop_engine
    agent_permissions[sid] = permissions
    active_websockets[sid] = []

    return {"session_id": sid, "workspace_dir": ws_dir, "model": llm.model}


@router.post("/sessions/{session_id}/messages")
async def send_message(session_id: str, req: MessageRequest) -> Dict[str, Any]:
    if session_id not in agent_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    loop_engine = agent_loops[session_id]

    async def run_agent_in_background():
        async for event in loop_engine.run_turn(req.text):
            # Broadcast event to connected websockets
            if session_id in active_websockets:
                ws_list = list(active_websockets[session_id])
                for ws in ws_list:
                    try:
                        await ws.send_text(json.dumps(event.to_dict()))
                    except Exception:
                        pass

    asyncio.create_task(run_agent_in_background())
    return {"status": "started", "session_id": session_id}


@router.post("/sessions/{session_id}/permission")
def resolve_permission(session_id: str, req: PermissionResponseRequest) -> Dict[str, Any]:
    if session_id not in agent_permissions:
        raise HTTPException(status_code=404, detail="Session not found")

    broker = agent_permissions[session_id]
    success = broker.resolve(req.request_id, req.allowed, req.always)
    return {"status": "resolved" if success else "failed"}


@router.post("/sessions/{session_id}/interrupt")
def interrupt_session(session_id: str) -> Dict[str, Any]:
    if session_id not in agent_loops:
        raise HTTPException(status_code=404, detail="Session not found")

    agent_loops[session_id].interrupt()
    return {"status": "interrupted"}


@router.get("/sessions/{session_id}/tree")
def get_file_tree(session_id: str) -> Dict[str, Any]:
    if session_id not in agent_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    ws_dir = agent_sessions[session_id].workspace_dir
    scanner = WorkspaceScanner(ws_dir)
    return {"tree": scanner.get_file_tree()}


@router.websocket("/ws/{session_id}")
async def websocket_agent_events(websocket: WebSocket, session_id: str):
    await websocket.accept()
    if session_id not in active_websockets:
        active_websockets[session_id] = []
    active_websockets[session_id].append(websocket)

    try:
        while True:
            text = await websocket.receive_text()
            data = json.loads(text)
            if data.get("type") == "permission_response":
                rid = data.get("request_id")
                allowed = data.get("allowed", False)
                always = data.get("always", False)
                if session_id in agent_permissions:
                    agent_permissions[session_id].resolve(rid, allowed, always)
    except WebSocketDisconnect:
        if session_id in active_websockets and websocket in active_websockets[session_id]:
            active_websockets[session_id].remove(websocket)
