import os
import json
import pytest

from backend.autonomy.hypothesis.evidence import EvidenceGatherer
from backend.autonomy.hypothesis.ranking import HypothesisRanker
from backend.autonomy.experiment.planner import ExperimentPlanner
from backend.autonomy.experiment.isolation import IsolationManager
from backend.autonomy.evaluation.statistics import StatisticalValidator


def test_evidence_gatherer(tmp_path):
    # Tạo mock trajectories
    task1 = [
        {"event_type": "action", "action_name": "edit_file"},
        {"event_type": "observation", "outputs": {"error": "syntax error", "category": "syntax_error"}}
    ]
    task2 = [
        {"event_type": "action", "action_name": "open_file"},
        {"event_type": "observation", "outputs": {"error": "another syntax error", "category": "syntax_error"}}
    ]
    task3 = [
        {"event_type": "action", "action_name": "run_test"},
        {"event_type": "observation", "outputs": {"error": "ModuleNotFoundError", "category": "dependency_error"}}
    ]

    with open(tmp_path / "task_1.json", "w") as f:
        json.dump(task1, f)
    with open(tmp_path / "task_2.json", "w") as f:
        json.dump(task2, f)
    with open(tmp_path / "task_3.json", "w") as f:
        json.dump(task3, f)

    gatherer = EvidenceGatherer(str(tmp_path))
    evidence = gatherer.gather_evidence("syntax_error")

    assert evidence["error_category"] == "syntax_error"
    assert evidence["failed_tasks_count"] == 2
    assert len(evidence["patterns"]) == 2


def test_hypothesis_ranker():
    hypotheses = [
        {
            "hypothesis_id": "hyp-1",
            "expected_gain": 0.30,
            "complexity_effort": 1.0  # ROI = 0.30 / 1.0 = 0.30
        },
        {
            "hypothesis_id": "hyp-2",
            "expected_gain": 0.60,
            "complexity_effort": 3.0  # ROI = 0.60 / 3.0 = 0.20
        },
        {
            "hypothesis_id": "hyp-3",
            "expected_gain": 0.50,
            "complexity_effort": 2.0  # ROI = 0.50 / 2.0 = 0.25
        }
    ]

    ranked = HypothesisRanker.rank_hypotheses(hypotheses)
    
    assert ranked[0]["hypothesis_id"] == "hyp-1"  # ROI = 0.30
    assert ranked[1]["hypothesis_id"] == "hyp-3"  # ROI = 0.25
    assert ranked[2]["hypothesis_id"] == "hyp-2"  # ROI = 0.20


def test_experiment_planner():
    planner = ExperimentPlanner()
    hypothesis = {
        "hypothesis_id": "hyp-999",
        "target_file": "backend/config/prompts/coder.txt",
        "proposed_change": "Thử nghiệm thay đổi prompt"
    }

    steps = planner.plan_experiment(hypothesis)
    assert len(steps) == 5
    assert steps[0]["action"] == "create_branch"
    assert steps[0]["branch_name"] == "experiment/hyp-999"
    assert steps[2]["action"] == "apply_modification"
    assert steps[2]["change"] == "Thử nghiệm thay đổi prompt"


def test_isolation_manager(tmp_path):
    file_path = tmp_path / "settings.py"
    file_path.write_text("DEBUG = True\n", encoding="utf-8")

    manager = IsolationManager(str(tmp_path))

    # 1. Backup file
    assert manager.backup_file("settings.py") is True

    # 2. Modify file
    file_path.write_text("DEBUG = False\n", encoding="utf-8")

    # 3. Restore file
    assert manager.restore_file("settings.py") is True
    assert file_path.read_text(encoding="utf-8") == "DEBUG = True\n"


def test_statistical_validator():
    # 1. Cải tiến thực sự có ý nghĩa (rewards tăng mạnh)
    old_rewards = [0.55, 0.60, 0.58, 0.62, 0.59]
    new_rewards = [0.85, 0.90, 0.88, 0.82, 0.89]

    significant, msg = StatisticalValidator.validate_improvement(old_rewards, new_rewards)
    assert significant is True
    assert "T-Test" in msg

    # 2. Cải tiến không đáng kể (rewards tương đương)
    old_rewards_flat = [0.60, 0.62, 0.61, 0.63, 0.60]
    new_rewards_flat = [0.61, 0.63, 0.62, 0.64, 0.61]

    significant_flat, msg_flat = StatisticalValidator.validate_improvement(old_rewards_flat, new_rewards_flat)
    assert significant_flat is False
