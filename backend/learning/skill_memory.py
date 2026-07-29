import os
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class SkillMemory:
    def __init__(self, db_path: str):
        self.db_path = os.path.abspath(db_path)
        self.skills: List[Dict[str, Any]] = []
        self.load_skills()

    def load_skills(self):
        """Đọc cơ sở dữ liệu skills.json."""
        if not os.path.exists(self.db_path):
            self.skills = self._get_default_skills()
            self.save_skills()
            return

        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.skills = data.get("skills", [])
        except Exception as e:
            logger.error(f"Lỗi khi đọc file skills.json: {str(e)}")
            self.skills = self._get_default_skills()

    def save_skills(self):
        """Ghi lưu cơ sở dữ liệu skills.json."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump({"skills": self.skills}, f, indent=2, ensure_ascii=False)
            logger.debug("SkillMemory: Saved skills.json successfully.")
        except Exception as e:
            logger.error(f"Lỗi khi lưu file skills.json: {str(e)}")

    def retrieve_skills(self, error_message: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Lọc và lấy ra Top-K kỹ năng phù hợp nhất dựa trên từ khóa lỗi kích hoạt (trigger_tags)."""
        matched_skills = []
        
        for skill in self.skills:
            score = 0
            for tag in skill.get("trigger_tags", []):
                if tag.lower() in error_message.lower():
                    score += 1
            
            if score > 0:
                matched_skills.append((score, skill))

        # Sắp xếp theo score giảm dần, sau đó theo tỷ lệ thành công (success_rate) giảm dần
        matched_skills.sort(key=lambda x: (x[0], x[1].get("success_rate", 0.0)), reverse=True)
        
        return [item[1] for item in matched_skills[:limit]]

    def update_skill_stats(self, skill_name: str, success: bool):
        """Cập nhật thống kê tỷ lệ thành công và số lần sử dụng của một kỹ năng."""
        for skill in self.skills:
            if skill["name"] == skill_name:
                usage = skill.get("usage_count", 0) + 1
                curr_rate = skill.get("success_rate", 0.0)
                
                # Tính tỷ lệ thành công mới chạy tịnh tiến lũy tích
                new_rate = (curr_rate * (usage - 1) + (1.0 if success else 0.0)) / usage
                
                skill["usage_count"] = usage
                skill["success_rate"] = round(new_rate, 2)
                
                logger.info(f"SkillMemory: Updated stats for {skill_name} -> usage: {usage}, rate: {new_rate:.2f}")
                self.save_skills()
                break

    def _get_default_skills(self) -> List[Dict[str, Any]]:
        """Khởi dựng danh sách các kỹ năng kỹ thuật mẫu ban đầu."""
        return [
            {
                "name": "asyncio_deadlock_fix",
                "trigger_tags": ["deadlock", "await", "timeout", "asyncio"],
                "success_rate": 0.80,
                "usage_count": 10,
                "procedure": [
                    "Kiểm tra xem loop có bị chặn bởi các tác vụ blocking I/O không.",
                    "Sử dụng asyncio.shield hoặc timeout kiểm soát vòng lặp.",
                    "Đảm bảo các task async được cancel an toàn khi xảy ra ngoại lệ."
                ]
            },
            {
                "name": "dependency_resolver",
                "trigger_tags": ["modulenotfounderror", "import", "dependency"],
                "success_rate": 0.95,
                "usage_count": 20,
                "procedure": [
                    "Xác định chính xác tên gói package bị thiếu từ ModuleNotFoundError.",
                    "Chạy lệnh cài đặt gói đó vào môi trường cô lập.",
                    "Nếu là import tương đối, kiểm tra lại biến sys.path hoặc PYTHONPATH."
                ]
            },
            {
                "name": "syntax_error_healer",
                "trigger_tags": ["syntaxerror", "indentationerror", "unexpected token"],
                "success_rate": 0.90,
                "usage_count": 15,
                "procedure": [
                    "Định vị dòng báo lỗi và rà soát các dấu ngoặc (), [], {} liền trước.",
                    "Sửa các ký tự thụt lề lỗi bằng công cụ định dạng code.",
                    "Chạy lệnh kiểm tra cú pháp khô (dry-run/compile) trước khi ghi đĩa."
                ]
            }
        ]
