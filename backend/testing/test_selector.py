import os
import logging
from typing import List, Dict, Any

from backend.workspace.analyzer.architecture import ImpactAnalyzer

logger = logging.getLogger(__name__)


class TestSelector:
    __test__ = False

    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(base_dir)
        self.analyzer = ImpactAnalyzer(self.base_dir)

    def select_tests(self, modified_files: List[str], default_test_cmd: str = "pytest") -> Dict[str, Any]:
        """Phân tích các file thay đổi và lựa chọn các unit test tương ứng cần chạy.
        
        Trả về lệnh chạy test được tối ưu hóa và danh sách các test file bị ảnh hưởng.
        """
        # Khởi tạo đồ thị phụ thuộc
        self.analyzer.initialize()

        affected_tests = set()
        is_global_change = False

        for file in modified_files:
            rel_path = os.path.relpath(os.path.join(self.base_dir, file), self.base_dir).replace("\\", "/")
            
            # Nếu thay đổi các file cấu hình dùng chung hệ thống, coi như ảnh hưởng toàn cục
            if "config" in rel_path or "settings" in rel_path or rel_path == "docker-compose.yml":
                logger.info(f"Phát hiện thay đổi toàn cục trong {rel_path}. Sẽ chạy toàn bộ test suite.")
                is_global_change = True
                break

            # Phân tích tác động lan truyền của file cụ thể
            try:
                report = self.analyzer.analyze_impact(rel_path)
                for t in report.get("affected_tests", []):
                    affected_tests.add(t)
            except Exception as e:
                logger.warning(f"Không thể phân tích tác động cho {rel_path}: {str(e)}")

        if is_global_change or not affected_tests:
            # Chạy toàn bộ test suite
            return {
                "command": default_test_cmd,
                "affected_tests": [],
                "run_all": True
            }

        # Tạo lệnh chạy tối ưu hóa trỏ cụ thể vào các file test bị ảnh hưởng
        test_files_str = " ".join(list(affected_tests))
        optimized_cmd = f"pytest {test_files_str}"

        return {
            "command": optimized_cmd,
            "affected_tests": list(affected_tests),
            "run_all": False
        }
