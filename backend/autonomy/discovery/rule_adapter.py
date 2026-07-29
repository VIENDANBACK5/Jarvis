import logging
from backend.autonomy.discovery.principle_store import PrincipleStore

logger = logging.getLogger(__name__)


class RuleAdapter:
    def __init__(self, store: PrincipleStore):
        self.store = store

    def format_rules_for_prompt(self) -> str:
        """Cấu hình kết xuất danh sách nguyên lý đúc kết để chèn làm luật cứng vào prompt hệ thống."""
        principles = self.store.load_principles()
        if not principles:
            return ""

        logger.info(f"RuleAdapter: Loaded {len(principles)} principles to enforce in system prompt.")
        
        prompt_lines = [
            "\n[BỘ LUẬT CỨNG ĐÚC KẾT HỆ THỐNG - RULE ENFORCEMENT]",
            "Dựa trên các lỗi hệ thống lịch sử, bắt buộc tuân thủ nghiêm ngặt các quy tắc thiết kế sau:"
        ]
        
        for p in principles:
            if p.status == "validated":
                prompt_lines.append(f"- [{p.id}] {p.derived_rule} (Xác suất tin cậy: {p.confidence * 100:.1f}%)")

        if len(prompt_lines) <= 2:
            return ""

        return "\n".join(prompt_lines) + "\n"
