import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from backend.api.gateway import router as gateway_router

app = FastAPI()
app.include_router(gateway_router)

client = TestClient(app)


def test_gateway_start_and_approve_mission(tmp_path):
    # 1. Start mission
    res = client.post("/api/v1/mission/start", json={
        "task_goal": "Fix authentication bug",
        "workspace_dir": str(tmp_path),
        "target_file": "auth.py"
    })

    assert res.status_code == 200
    data = res.json()
    assert "session_id" in data
    session_id = data["session_id"]

    # 2. Get mission status
    res_get = client.get(f"/api/v1/mission/{session_id}")
    assert res_get.status_code == 200
    assert res_get.json()["session_id"] == session_id

    # 3. Simulate completion and transition state to WAITING_APPROVAL for stable test assertion
    from backend.api.gateway import sessions_db
    sessions_db[session_id].state = "WAITING_APPROVAL"

    # 4. Approve patch
    res_app = client.post("/api/v1/mission/approve", json={
        "session_id": session_id,
        "approved": True
    })
    assert res_app.status_code == 200
    assert res_app.json()["approved"] is True


def test_gateway_list_files(tmp_path):
    res = client.get(f"/api/v1/files?workspace_dir={tmp_path}")
    assert res.status_code == 200
    assert "files" in res.json()
