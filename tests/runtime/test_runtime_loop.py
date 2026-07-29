import pytest
from backend.runtime.runtime_loop import AgentRuntimeLoop
from backend.runtime.action_history import ActionHistoryTracker


def test_action_history_tracker():
    tracker = ActionHistoryTracker()
    tracker.record_step("Observe", "main.py", "Scanned files")
    tracker.record_step("Edit", "main.py", "Applied diff")

    assert len(tracker.steps) == 2
    summary = tracker.get_summary()
    assert "Step 1: [Observe]" in summary
    assert "Step 2: [Edit]" in summary


def test_agent_runtime_loop_execution(tmp_path):
    loop = AgentRuntimeLoop(workspace_dir=str(tmp_path))

    steps_recorded = []
    def on_step(info):
        steps_recorded.append(info)

    res = loop.run_loop(
        task_goal="Fix auth session timeout",
        target_file="auth.py",
        patch_code="[PATCH] Refresh JWT token on expiry",
        on_step_callback=on_step
    )

    assert res["solved"] is True
    assert res["status"] == "SUCCESS"
    assert len(steps_recorded) == 5
    assert res["steps_count"] == 5
