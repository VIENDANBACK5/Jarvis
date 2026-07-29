import json
import logging
from typing import Dict, Any, Optional
from backend.services.llm import get_llm

logger = logging.getLogger(__name__)

# Từ điển tĩnh các lỗi phổ biến (Tầng 1 - Rule-Based)
KNOWN_ERRORS = [
    {
        "trigger": "ModuleNotFoundError",
        "category": "dependency_error",
        "root_cause": "Thiếu thư viện hoặc package phụ thuộc.",
        "recommendation": "Sử dụng pip hoặc npm để cài đặt thư viện bị thiếu vào môi trường sandbox."
    },
    {
        "trigger": "SyntaxError",
        "category": "syntax_error",
        "root_cause": "Sai cú pháp mã nguồn Python.",
        "recommendation": "Kiểm tra lại các dấu đóng mở ngoặc, dấu hai chấm và thụt lề thụt dòng chuẩn xác."
    },
    {
        "trigger": "IndentationError",
        "category": "syntax_error",
        "root_cause": "Lỗi thụt dòng không chuẩn trong Python.",
        "recommendation": "Đảm bảo sử dụng đồng bộ khoảng trắng (spaces) hoặc tab, không trộn lẫn hai loại."
    },
    {
        "trigger": "AssertionError",
        "category": "test_failure",
        "root_cause": "Giá trị kỳ vọng của test case không khớp với giá trị thực tế trả về.",
        "recommendation": "Kiểm tra lại logic xử lý của hàm nghiệp vụ chính xem có bỏ sót điều kiện biên nào không."
    },
    {
        "trigger": "TimeoutError",
        "category": "timeout",
        "root_cause": "Tiến trình thực thi vượt quá thời hạn (timeout) quy định.",
        "recommendation": "Tối ưu hóa các vòng lặp vô hạn hoặc tăng thêm thời gian timeout cho sandbox."
    },
    {
        "trigger": "PermissionError",
        "category": "permission_error",
        "root_cause": "Không có đủ thẩm quyền đọc/ghi file hoặc thư mục chỉ định.",
        "recommendation": "Kiểm tra lại phân quyền hệ thống tập tin hoặc đảm bảo file không bị khóa bởi tiến trình khác."
    }
]


class FailureAnalyzer:
    async def analyze(self, error_message: str) -> Dict[str, str]:
        """Phân tích lỗi qua 2 tầng: Rule-Based tĩnh trước, nếu không khớp gọi LLM RCA."""
        # --- Tầng 1: Rule-Based Static Check ---
        for err in KNOWN_ERRORS:
            if err["trigger"] in error_message:
                logger.info(f"FailureAnalyzer (Tầng 1): Khớp lỗi tĩnh '{err['trigger']}'")
                return {
                    "category": err["category"],
                    "root_cause": err["root_cause"],
                    "recommendation": err["recommendation"]
                }

        # --- Tầng 2: LLM Root Cause Analysis (RCA) ---
        logger.info("FailureAnalyzer (Tầng 2): Lỗi không xác định, đang gọi LLM phân tích...")
        llm = get_llm()
        
        prompt = (
            f"Bạn là chuyên gia chuẩn đoán lỗi mã nguồn. Hãy phân tích lỗi sau đây:\n\n"
            f"Error Log:\n{error_message}\n\n"
            f"Trả về kết quả duy nhất ở định dạng JSON thô (không có markdown code block) chứa chính xác 3 trường sau:\n"
            f"{{\n"
            f"  \"category\": \"nhóm lỗi (ví dụ: logic_error, environment_error, api_error)\",\n"
            f"  \"root_cause\": \"nguyên nhân gốc ngắn gọn\",\n"
            f"  \"recommendation\": \"khuyến nghị bước sửa lỗi cụ thể\"\n"
            f"}}"
        )

        try:
            response = await llm.ainvoke([("user", prompt)])
            # Bóc tách nội dung thô loại bỏ markdown ```json
            cleaned_content = response.content.strip()
            if cleaned_content.startswith("```"):
                lines = cleaned_content.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned_content = "\n".join(lines).strip()

            result = json.loads(cleaned_content)
            return {
                "category": result.get("category", "unknown_error"),
                "root_cause": result.get("root_cause", "Không xác định rõ nguyên nhân."),
                "recommendation": result.get("recommendation", "Đọc lại tệp lỗi và kiểm thử thủ công.")
            }
        except Exception as e:
            logger.error(f"Lỗi khi gọi LLM RCA phân tích lỗi: {str(e)}")
            # Fallback mặc định
            return {
                "category": "unknown_error",
                "root_cause": "Lỗi không xác định từ log đầu ra.",
                "recommendation": "Kiểm tra lại cấu trúc file và thử chạy test suite thủ công."
            }
