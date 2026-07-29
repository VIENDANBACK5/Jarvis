import os
import json
import pytest

from backend.reasoning.causal.graph import CausalGraph, CausalNode
from backend.reasoning.diagnosis.stacktrace_parser import StacktraceParser
from backend.reasoning.diagnosis.evidence_collector import EvidenceCollector
from backend.reasoning.hypothesis.tree import HypothesisTree
from backend.reasoning.hypothesis.bayesian_update import BayesianUpdater
from backend.reasoning.planner.adapter import PlannerAdapter


def test_causal_graph():
    graph = CausalGraph()
    
    node_sym = CausalNode(node_type="symptom", name="API 500", source="llm")
    node_cause1 = CausalNode(node_type="cause", name="Database Migration Missing", source="experience")
    node_cause2 = CausalNode(node_type="cause", name="Code Syntax Error", source="rule")

    graph.add_node(node_sym)
    graph.add_node(node_cause1)
    graph.add_node(node_cause2)

    graph.add_edge(node_sym.id, node_cause1.id)
    graph.add_edge(node_sym.id, node_cause2.id)

    causes = graph.get_possible_causes("API 500")
    assert len(causes) == 2
    assert any(c.name == "Database Migration Missing" for c in causes)


def test_stacktrace_parser():
    stacktrace = (
        "Traceback (most recent call last):\n"
        "  File \"backend/services/payment.py\", line 125, in charge\n"
        "    result = stripe.charge()\n"
        "AttributeError: module 'stripe' has no attribute 'charge'\n"
    )
    result = StacktraceParser.parse_stacktrace(stacktrace)
    
    assert result["filepath"] == "backend/services/payment.py"
    assert result["line_number"] == 125
    assert "AttributeError" in result["error_message"]


def test_bayesian_updater():
    tree = HypothesisTree()
    tree.add_hypothesis("Database Schema or Migration Mismatch", 0.34)
    tree.add_hypothesis("Source Code Syntax or Type Error", 0.33)
    tree.add_hypothesis("Dependency or Module Import Error", 0.33)

    evidence = [
        "World Model: File contains migration settings.",
        "Experience Store: Ghi nhận 2 lần lỗi migration trong quá khứ."
    ]

    # Cập nhật Bayesian
    BayesianUpdater.update_probabilities(tree, evidence)
    ranked = tree.rank_hypotheses()
    
    # Giả thuyết Database (migration) sẽ có xác suất vọt lên cao nhất
    assert ranked[0].name == "Database Schema or Migration Mismatch"
    assert ranked[0].probability > 0.60


def test_planner_adapter_integration(tmp_path):
    ws_dir = tmp_path / "app"
    exp_dir = tmp_path / "experiences"
    os.makedirs(ws_dir / "backend")
    os.makedirs(ws_dir / "tests")
    os.makedirs(exp_dir)

    # 1. Tạo file nguồn để dựng world model
    payment_code = (
        "class PaymentService:\n"
        "    def charge(self):\n"
        "        pass\n"
    )
    with open(ws_dir / "backend" / "payment.py", "w", encoding="utf-8") as f:
        f.write(payment_code)

    # 2. Tạo file test
    test_code = (
        "from backend.payment import PaymentService\n"
        "def test_payment():\n"
        "    pass\n"
    )
    with open(ws_dir / "tests" / "test_payment.py", "w", encoding="utf-8") as f:
        f.write(test_code)

    # Khởi động PlannerAdapter
    adapter = PlannerAdapter(str(ws_dir), str(exp_dir))

    # Tạo log lỗi giả lập liên quan đến file payment
    error_log = (
        "Traceback (most recent call last):\n"
        "  File \"backend/payment.py\", line 10, in charge\n"
        "    pass\n"
        "AttributeError: PaymentService has no attribute charge\n"
    )

    context = adapter.generate_diagnostic_context(error_log)
    
    # Xác minh các đề xuất báo cáo có định dạng đầy đủ
    assert "CAUSAL REASONER REPORT" in context
    assert "backend/payment.py" in context
    assert "AttributeError" in context
    assert "test_payment.py" in context
