import os
import json
import pytest

from backend.reasoning.diagnosis.diagnostic_experiment import DiagnosticExperimentGenerator
from backend.reasoning.diagnosis.evidence_updater import EvidenceUpdater
from backend.reasoning.hypothesis.tree import HypothesisTree
from backend.reasoning.causal.evolution import CausalEvolution
from backend.reasoning.experiment.prioritizer import ExperimentPrioritizer


def test_diagnostic_experiment_generator():
    generator = DiagnosticExperimentGenerator()
    
    exp = generator.generate_experiment("Database Schema Mismatch")
    assert exp.hypothesis == "Database Schema Mismatch"
    assert "compare database schema" in exp.experiment_actions
    assert exp.success_condition == "difference detected"


def test_evidence_updater():
    generator = DiagnosticExperimentGenerator()
    exp = generator.generate_experiment("Database Schema Mismatch")

    tree = HypothesisTree()
    tree.add_hypothesis("Database Schema Mismatch", 0.34)
    tree.add_hypothesis("Source Code Syntax or Type Error", 0.33)
    tree.add_hypothesis("Dependency or Module Import Error", 0.33)

    # 1. Thử nghiệm thành công -> Tăng niềm tin Bayesian
    evidence1 = EvidenceUpdater.execute_and_update(tree, exp, "difference detected in migrations")
    assert len(evidence1) == 1
    assert "Xác nhận giả thuyết" in evidence1[0]
    
    ranked1 = tree.rank_hypotheses()
    assert ranked1[0].name == "Database Schema Mismatch"
    assert ranked1[0].probability > 0.40

    # 2. Thử nghiệm bác bỏ -> Hạ niềm tin Bayesian
    tree2 = HypothesisTree()
    tree2.add_hypothesis("Database Schema Mismatch", 0.34)
    tree2.add_hypothesis("Source Code Syntax or Type Error", 0.33)
    tree2.add_hypothesis("Dependency or Module Import Error", 0.33)
    
    evidence2 = EvidenceUpdater.execute_and_update(tree2, exp, "no anomalies found")
    assert len(evidence2) == 1
    assert "Bác bỏ giả thuyết" in evidence2[0]
    
    ranked2 = tree2.rank_hypotheses()
    assert ranked2[-1].name == "Database Schema Mismatch"
    assert ranked2[-1].probability < 0.10


def test_causal_evolution(tmp_path):
    graph_file = tmp_path / "causal_graph.json"

    # 1. Khởi tạo và cập nhật thành công -> Tăng trọng số
    ok = CausalEvolution.update_causal_weights(
        str(graph_file),
        symptom="API 500",
        cause="Database Schema Mismatch",
        success=True,
        context={"framework": "FastAPI", "database": "PostgreSQL"}
    )
    assert ok is True

    with open(graph_file, "r") as f:
        data = json.load(f)
    assert data["links"][0]["confidence"] == 0.55  # Khởi đầu success = True -> 0.55

    # 2. Cập nhật thành công lần nữa -> Tiếp tục tăng trọng số
    CausalEvolution.update_causal_weights(
        str(graph_file),
        symptom="API 500",
        cause="Database Schema Mismatch",
        success=True,
        context={"framework": "FastAPI", "database": "PostgreSQL"}
    )
    with open(graph_file, "r") as f:
        data2 = json.load(f)
    assert data2["links"][0]["confidence"] == 0.60  # 0.55 + 0.05 = 0.60


def test_experiment_prioritizer():
    experiments = [
        {
            "name": "exp-1",
            "probability": 0.70,
            "impact": 2.0,
            "cost": 1.0  # Value = (0.70 * 2.0) / 1.0 = 1.40
        },
        {
            "name": "exp-2",
            "probability": 0.80,
            "impact": 1.0,
            "cost": 2.0  # Value = (0.80 * 1.0) / 2.0 = 0.40
        },
        {
            "name": "exp-3",
            "probability": 0.50,
            "impact": 3.0,
            "cost": 1.0  # Value = (0.50 * 3.0) / 1.0 = 1.50
        }
    ]

    prioritized = ExperimentPrioritizer.prioritize_experiments(experiments)
    
    assert prioritized[0]["name"] == "exp-3"  # Value = 1.50
    assert prioritized[1]["name"] == "exp-1"  # Value = 1.40
    assert prioritized[2]["name"] == "exp-2"  # Value = 0.40
