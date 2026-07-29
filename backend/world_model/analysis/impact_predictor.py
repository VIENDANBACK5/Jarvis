import os
import logging
from typing import Dict, Any, List

from backend.world_model.graph.dependency_graph import DependencyGraph
from backend.world_model.graph.call_graph import CallGraph
from backend.world_model.graph.test_graph import CoverageGraph

logger = logging.getLogger(__name__)


class ImpactPredictor:
    def __init__(self, workspace_dir: str):
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.dep_graph = DependencyGraph()
        self.call_graph = CallGraph()
        self.test_graph = CoverageGraph()
        
        # Tự động dựng biểu đồ khi khởi tạo
        self.dep_graph.build_graph(self.workspace_dir)
        self.test_graph.build_test_graph(self.workspace_dir)

    def calculate_impact_score(self, filepath: str, method_name: str = "") -> Dict[str, Any]:
        """Tính toán điểm số tác động (Impact Score) và khoanh vùng Test Suite bị ảnh hưởng."""
        rel_path = os.path.relpath(os.path.abspath(filepath), self.workspace_dir).replace("\\", "/")
        
        # 1. Tìm các tệp phụ thuộc (D)
        dependent_files = self.dep_graph.get_dependent_files(rel_path)
        d_score = float(len(dependent_files))

        # 2. Tìm các caller methods (C)
        caller_methods = []
        if method_name:
            # Ví dụ: ClassName.method_name
            caller_methods = self.call_graph.get_callers(method_name)
        c_score = float(len(caller_methods))

        # 3. Tìm các test cases bao phủ (T)
        associated_tests = self.test_graph.get_associated_tests(rel_path)
        t_score = float(len(associated_tests))

        # 4. Tính toán độ criticality (R)
        criticality = 1.0
        # Nếu là các module core quan trọng
        if any(core in rel_path for core in ["graph", "sandbox", "security", "coordinator"]):
            criticality = 2.0

        # Công thức: Impact = w1 * D + w2 * C + w3 * T + w4 * R
        # Trọng số chuẩn: w1=0.3, w2=0.3, w3=0.2, w4=0.2
        w1, w2, w3, w4 = 0.3, 0.3, 0.2, 0.2
        impact_score = (w1 * d_score) + (w2 * c_score) + (w3 * t_score) + (w4 * criticality)
        impact_score = round(impact_score, 3)

        # Quyết định risk level
        if impact_score < 1.0:
            risk_level = "LOW"
        elif impact_score < 3.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        # Đưa khuyến nghị lập kế hoạch chạy test case
        recommendations = []
        if associated_tests:
            recommendations.append(f"Chạy kiểm thử khoanh vùng: pytest " + " ".join(associated_tests))
        else:
            recommendations.append("Không tìm thấy test suite trực tiếp. Đề xuất viết bổ sung test case mới.")

        if risk_level == "HIGH":
            recommendations.append("CẢNH BÁO: Tác động của thay đổi rất lớn. Hãy chạy kiểm thử hồi quy toàn diện regression suite.")

        result = {
            "target_file": rel_path,
            "impact_score": impact_score,
            "risk_level": risk_level,
            "affected_modules": dependent_files,
            "affected_tests": associated_tests,
            "recommendations": recommendations
        }
        
        logger.info(
            f"ImpactPredictor: Analyzed {rel_path} | "
            f"Score: {impact_score} | Risk: {risk_level} | Associated Tests: {len(associated_tests)}"
        )
        return result
