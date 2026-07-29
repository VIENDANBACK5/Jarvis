import os
import re
import logging
from typing import List, Dict, Any, Optional

from backend.workspace.scanner import WorkspaceScanner
from backend.workspace.index.symbol_store import SymbolStore
from backend.editing.patch_applier import PatchApplier
from backend.editing.patch_validator import PatchValidator
from backend.sandbox import get_sandbox_manager

logger = logging.getLogger(__name__)


class CodingTools:
    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(base_dir)
        self.scanner = WorkspaceScanner(self.base_dir)

    def _is_safe_path(self, path: str) -> bool:
        """Đảm bảo đường dẫn thao tác nằm hoàn toàn trong thư mục base_dir."""
        target_path = os.path.abspath(os.path.join(self.base_dir, path))
        return target_path.startswith(self.base_dir)

    def list_files(self) -> List[str]:
        """Liệt kê toàn bộ các file mã nguồn hợp lệ trong dự án."""
        files = self.scanner.scan()
        return [f["path"] for f in files]

    def search_code(self, query: str, is_regex: bool = False) -> List[Dict[str, Any]]:
        """Tìm kiếm chuỗi hoặc biểu thức chính quy (regex) trên toàn codebase."""
        results = []
        files = self.list_files()
        
        try:
            pattern = re.compile(query, re.IGNORECASE) if is_regex else None
        except re.error as e:
            logger.error(f"Regex query không hợp lệ '{query}': {str(e)}")
            return []

        for rel_path in files:
            full_path = os.path.join(self.base_dir, rel_path)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    for idx, line in enumerate(f, 1):
                        matched = False
                        if pattern:
                            if pattern.search(line):
                                matched = True
                        else:
                            if query.lower() in line.lower():
                                matched = True
                                
                        if matched:
                            results.append({
                                "filepath": rel_path,
                                "line_number": idx,
                                "line_content": line.strip()
                            })
            except Exception as e:
                logger.debug(f"Không thể đọc file {rel_path} khi search: {str(e)}")

        return results[:100]  # Giới hạn tối đa 100 kết quả để tránh tràn context

    def open_file(self, path: str, start_line: int = 1, end_line: Optional[int] = None) -> str:
        """Đọc nội dung một khoảng dòng cụ thể trong file kèm số dòng."""
        if not self._is_safe_path(path):
            return f"Error: Quyền truy cập bị từ chối. Thao tác ngoài thư mục làm việc."

        full_path = os.path.abspath(os.path.join(self.base_dir, path))
        if not os.path.exists(full_path):
            return f"Error: Không tìm thấy file tại '{path}'"

        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                
            total_lines = len(lines)
            start = max(1, start_line)
            end = min(total_lines, end_line) if end_line else total_lines

            output = []
            for idx in range(start, end + 1):
                # Hiển thị số dòng chuẩn để LLM dễ viết Unified Diff
                output.append(f"{idx}: {lines[idx - 1]}")
                
            return "".join(output)
        except Exception as e:
            return f"Error: Không thể đọc file: {str(e)}"

    def edit_file(self, path: str, diff_patch: str) -> Dict[str, Any]:
        """Áp dụng bản vá Unified Diff lên file chỉ định kèm kiểm tra an toàn và cú pháp."""
        if not self._is_safe_path(path):
            return {
                "success": False,
                "error": "Quyền truy cập bị từ chối. Thao tác ngoài thư mục làm việc."
            }

        full_path = os.path.abspath(os.path.join(self.base_dir, path))
        if not os.path.exists(full_path):
            return {
                "success": False,
                "error": f"Không tìm thấy file để chỉnh sửa tại '{path}'"
            }

        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                original_code = f.read()

            # 1. Kiểm tra tính hợp lệ và cú pháp (Syntax dry-run)
            is_valid, err_msg = PatchValidator.validate_patch(original_code, diff_patch, filename=path)
            if not is_valid:
                return {
                    "success": False,
                    "error": f"Kiểm tra bản vá thất bại: {err_msg}"
                }

            # 2. Áp dụng bản vá thực tế
            success, patched_code, apply_err = PatchApplier.apply_patch(original_code, diff_patch)
            if not success:
                return {
                    "success": False,
                    "error": f"Lỗi áp dụng bản vá: {apply_err}"
                }

            # 3. Ghi đè file xuống ổ cứng
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(patched_code)

            return {
                "success": True,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Lỗi không xác định khi edit file: {str(e)}"
            }

    async def run_test(
        self,
        test_target: str,
        sandbox_image: str = "python:3.11-slim",
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Chạy unit test chỉ định cô lập trong Sandbox Docker."""
        sandbox_manager = get_sandbox_manager()
        
        try:
            # Khởi chạy hoặc lấy container sandbox
            sandbox = await sandbox_manager.get_or_create(workspace_dir=self.base_dir, image=sandbox_image)
            
            # Thực thi câu lệnh test trong môi trường cô lập
            cmd = f"pytest {test_target}" if test_target else "pytest"
            result = await sandbox.execute(cmd, timeout=timeout)
            
            # Nếu không tìm thấy lệnh pytest (exit code 127), tự động fallback sang python standard library unittest
            if result["exit_code"] == 127:
                unit_cmd = f"python -m unittest {test_target}" if test_target else "python -m unittest"
                result = await sandbox.execute(unit_cmd, timeout=timeout)

            return {
                "exit_code": result["exit_code"],
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "timeout": result["timeout"]
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Lỗi khởi chạy Sandbox hoặc thực thi test: {str(e)}",
                "timeout": False
            }
