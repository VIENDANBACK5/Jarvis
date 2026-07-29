import pytest
from backend.runtime.hierarchical_planner import HierarchicalPlanner
from backend.runtime.cognitive_os import HierarchicalCognitiveOS


def test_hierarchical_planner_replan():
    planner = HierarchicalPlanner()
    goals = planner.decompose_task("Fix authentication bug")
    assert len(goals) == 5

    replanned = planner.replan_on_rejection("Security violation in patch")
    assert replanned[2]["completed"] is False


def test_hierarchical_cognitive_os_mission(tmp_path):
    os_engine = HierarchicalCognitiveOS(workspace_dir=str(tmp_path))
    res = os_engine.run_mission(
        task_id="OS-TEST-001",
        task_goal="Fix database session timeout bug",
        target_file="db.py",
        patch_code="[PATCH] Fix pool timeout"
    )

    assert res["status"] == "SUCCESS"
    assert res["review_status"] == "approved"
    assert res["sub_goals_count"] == 5
    assert "db.py" in res["modified_files"]
