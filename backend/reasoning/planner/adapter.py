import os
import logging
from typing import Dict, Any

from backend.reasoning.diagnosis.stacktrace_parser import StacktraceParser
from backend.reasoning.diagnosis.evidence_collector import EvidenceCollector
from backend.reasoning.hypothesis.tree import HypothesisTree
from backend.reasoning.hypothesis.bayesian_update import BayesianUpdater

logger = logging.getLogger(__name__)


class PlannerAdapter:
    def __init__(self, workspace_dir: str, experience_dir: str):
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.experience_dir = os.path.abspath(experience_dir)
        self.collector = EvidenceCollector(self.workspace_dir, self.experience_dir)

    def generate_diagnostic_context(self, error_log: str) -> str:
        """Thực thi chẩn đoán lỗi nhân quả và sinh ngữ cảnh chèn vào Planner Node."""
        logger.info("PlannerAdapter: Bắt đầu chẩn đoán nguyên nhân lỗi...")
        
        # 1. Phân tích Stacktrace lỗi
        trace_data = StacktraceParser.parse_stacktrace(error_log)
        err_file = trace_data.get("filepath")
        err_msg = trace_data.get("error_message")

        # 2. Thu thập các bằng chứng định lượng liên quan
        evidence = self.collector.collect_evidence(err_file, err_msg)

        # 3. Tạo cây giả thuyết chẩn đoán mặc định
        tree = HypothesisTree()
        tree.add_hypothesis("Database Schema or Migration Mismatch", 0.34)
        tree.add_hypothesis("Source Code Syntax or Type Error", 0.33)
        tree.add_hypothesis("Dependency or Module Import Error", 0.33)

        # 4. Cập nhật xác suất có điều kiện Bayesian
        BayesianUpdater.update_probabilities(tree, evidence)
        ranked_hyps = tree.rank_hypotheses()
        top_hyp = ranked_hyps[0]

        # 5. Thiết lập cẩm nang khuyến nghị chẩn đoán (Diagnostic Experiment Plan)
        rec_tests = []
        if err_file:
            impact_data = self.collector.predictor.calculate_impact_score(os.path.join(self.workspace_dir, err_file))
            rec_tests = impact_data.get("affected_tests", [])

        # 6. Dựng chuỗi prompt hướng dẫn Planner
        context_lines = [
            "\n[BỘ SUY LUẬN NHÂN QUẢ HỆ THỐNG - CAUSAL REASONER REPORT]",
            f"- Tệp phát sinh lỗi: {err_file or 'N/A'}",
            f"- Thông báo lỗi: {err_msg}",
            "- Giả thuyết nguyên nhân gốc có xác suất cao nhất:",
            f"  * Giả thuyết: {top_hyp.name} (Xác suất tin cậy: {top_hyp.probability * 100:.1f}%)",
            "- Bằng chứng thu thập được:"
        ]
        for env in evidence:
            context_lines.append(f"  * {env}")

        if rec_tests:
            context_lines.append("- Khuyến nghị Test suite kiểm định khoanh vùng:")
            for test in rec_tests:
                context_lines.append(f"  * tests/{test}")

        logger.info("PlannerAdapter: Sinh ngữ cảnh chẩn đoán nhân quả thành công.")
        return "\n".join(context_lines) + "\n"
