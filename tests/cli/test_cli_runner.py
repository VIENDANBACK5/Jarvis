import pytest
from backend.runtime.mission_controller import MissionController
from backend.runtime.agent_runtime import AgentRuntime


def test_mission_controller_budget():
    mission = MissionController(
        task_id="TEST-001",
        goal="Fix authentication bug",
        repo_path=".",
        max_iterations=2
    )
    mission.start()
    assert mission.is_active() is True

    step1 = mission.increment_step(tokens_in_step=500)
    assert step1 is True

    step2 = mission.increment_step(tokens_in_step=500)
    assert step2 is True

    # Quá số bước tối đa (max_iterations = 2)
    step3 = mission.increment_step(tokens_in_step=500)
    assert step3 is False
    assert mission.state == "MAX_ITERATIONS_EXCEEDED"


def test_agent_runtime_e2e_execution(tmp_path):
    runtime = AgentRuntime(storage_dir=str(tmp_path))
    res = runtime.execute_mission(
        task_id="TEST-E2E",
        task_goal="Fix JWT authentication expiration timeout",
        repo_path=str(tmp_path),
        target_file="auth.py",
        patch_code="[PATCH] Fix JWT token refresh logic"
    )

    assert res["status"] == "SUCCESS"
    assert res["review_status"] == "approved"
    assert res["reward"] > 0.80
    assert res["events_count"] > 0
