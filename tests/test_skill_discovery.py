import os
import json
import pytest

from backend.learning.experience import Experience, ExperienceStore
from backend.learning.trajectory.normalizer import TrajectoryNormalizer
from backend.learning.skills.extractor import SkillExtractor
from backend.learning.skills.evaluator import SkillEvaluator
from backend.learning.skills.consolidator import SkillConsolidator
from backend.learning.memory.skill_store import SkillStore
from backend.learning.skill_discovery import SkillDiscoverer


def test_trajectory_normalizer():
    trajectory = [
        {"event_type": "action", "action_name": "search_code"},
        {"event_type": "action", "action_name": "open_file"},
        {"event_type": "action", "action_name": "edit_file"},
        {"event_type": "action", "action_name": "run_test"}
    ]
    normalized = TrajectoryNormalizer.normalize_actions(trajectory)
    assert normalized == ["LOCATE", "INSPECT", "MODIFY", "VERIFY"]


def test_skill_extractor():
    exp = Experience(
        task_id="task-123",
        goal="Fix FastAPI request timeout issue",
        trajectory=[
            {"event_type": "action", "action_name": "open_file"},
            {"event_type": "action", "action_name": "edit_file"}
        ],
        reward=0.9
    )
    
    skill = SkillExtractor.extract_skill(exp)
    
    assert skill["name"] == "fix_fastapi_request"
    assert "fastapi" in skill["trigger_tags"]
    assert skill["procedure"] == ["INSPECT", "MODIFY"]
    assert skill["reward"] == 0.9


def test_skill_evaluator():
    skill = {
        "reward": 0.8,
        "usage_count": 2,
        "success_rate": 1.0
    }
    # Formula: Confidence = 0.8 * log(2 + 1) * 1.0 = 0.8 * 1.0986 = 0.879
    confidence = SkillEvaluator.calculate_confidence(skill)
    assert confidence == 0.879

    # Kiểm thử A/B Testing
    assert SkillEvaluator.evaluate_ab_test(0.85, 0.65) is True
    assert SkillEvaluator.evaluate_ab_test(0.50, 0.70) is False


def test_skill_consolidator():
    skills = [
        {
            "name": "fastapi_timeout",
            "trigger_tags": ["fastapi", "timeout", "request"],
            "procedure": ["INSPECT", "MODIFY"],
            "usage_count": 1,
            "success_rate": 1.0,
            "reward": 0.9
        },
        {
            "name": "fastapi_network_error",
            "trigger_tags": ["fastapi", "network", "timeout"],
            "procedure": ["LOCATE", "INSPECT", "VERIFY"],
            "usage_count": 2,
            "success_rate": 0.8,
            "reward": 0.7
        }
    ]

    consolidated = SkillConsolidator.consolidate_skills(skills)
    
    # 2 skills trên có độ tương đồng trigger tag >= 0.40 (có 'fastapi' và 'timeout')
    assert len(consolidated) == 1
    merged = consolidated[0]
    assert "fastapi" in merged["trigger_tags"]
    assert "network" in merged["trigger_tags"]
    assert merged["usage_count"] == 3
    assert merged["success_rate"] == 0.90  # (1.0 + 0.8) / 2
    assert "LOCATE" in merged["procedure"]
    assert "MODIFY" in merged["procedure"]


def test_skill_discoverer_flow(tmp_path):
    workspace_dir = tmp_path / "workspace"
    experience_dir = tmp_path / "experiences"
    os.makedirs(workspace_dir)
    os.makedirs(experience_dir)

    # 1. Tạo mock experience thành công
    exp = Experience(
        task_id="task-success",
        goal="Fix redis connection pool limit leak",
        trajectory=[
            {"event_type": "action", "action_name": "search_code"},
            {"event_type": "action", "action_name": "edit_file"}
        ],
        reward=0.95
    )
    store = ExperienceStore(str(experience_dir))
    store.save_experience(exp)

    # 2. Khởi động SkillDiscoverer
    discoverer = SkillDiscoverer(str(workspace_dir), str(experience_dir))
    discovered = discoverer.discover_new_skills()

    # 3. Xác thực kết quả
    assert len(discovered) == 1
    skill = discovered[0]
    assert skill["name"] == "fix_redis_connection"
    assert "redis" in skill["trigger_tags"]

    # Xác minh files được ghi đúng
    assert os.path.exists(workspace_dir / "skills.json")
    assert os.path.exists(workspace_dir / "skills" / "markdown" / "fix_redis_connection.md")
