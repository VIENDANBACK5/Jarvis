import os
import logging
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from backend.runtime.session import InteractiveSession
from backend.events.serializer import EventSerializer
from backend.api.websocket import event_broadcaster

router = APIRouter(prefix="/api/v1", tags=["gateway"])

# Memory store for active sessions
sessions_db: Dict[str, InteractiveSession] = {}


class MissionStartRequest(BaseModel):
    task_goal: str
    workspace_dir: str = "."
    target_file: str = "main.py"


class MessageRequest(BaseModel):
    session_id: str
    message: str


class ApprovalRequest(BaseModel):
    session_id: str
    approved: bool


@router.post("/mission/start")
async def start_mission(req: MissionStartRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    session = InteractiveSession(workspace_dir=req.workspace_dir)
    sessions_db[session.session_id] = session

    # Đăng ký listener chuyển tiếp mọi sự kiện từ EventBus sang WebSocket Broadcaster
    loop = asyncio.get_running_loop()

    def ws_forwarder(event):
        pub_event = EventSerializer.to_public_event(session.session_id, event)
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                event_broadcaster.broadcast_event(pub_event), 
                loop
            )

    session.runtime_loop.event_bus.subscribe("*", ws_forwarder)

    # Chạy tác vụ nền (Background Task) để giải phóng REST API ngay lập tức
    background_tasks.add_task(
        session.start_task,
        task_goal=req.task_goal,
        target_file=req.target_file
    )

    return {
        "session_id": session.session_id,
        "status": "RUNNING",
        "result": {"solved": False, "patch": ""}
    }


@router.post("/mission/approve")
def approve_mission(req: ApprovalRequest) -> Dict[str, Any]:
    if req.session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions_db[req.session_id]
    if req.approved:
        success = session.approve_patch()
        return {"session_id": session.session_id, "approved": success, "state": session.state}
    else:
        session.state = "CANCELLED"
        return {"session_id": session.session_id, "approved": False, "state": session.state}


@router.get("/mission/{session_id}")
def get_mission(session_id: str) -> Dict[str, Any]:
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions_db[session_id]
    return {
        "session_id": session.session_id,
        "state": session.state,
        "current_result": session.current_result
    }


@router.get("/files")
def list_workspace_files(workspace_dir: str = ".") -> Dict[str, Any]:
    abs_path = os.path.abspath(workspace_dir)
    files = []
    for root, _, filenames in os.walk(abs_path):
        for fname in filenames:
            if not fname.startswith(".") and not root.startswith(os.path.join(abs_path, ".")):
                rel_path = os.path.relpath(os.path.join(root, fname), abs_path)
                files.append(rel_path)
    return {"workspace_dir": abs_path, "files": files[:100]}
