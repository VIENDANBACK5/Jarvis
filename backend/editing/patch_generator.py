import re
import logging

from backend.services.llm import get_llm

logger = logging.getLogger(__name__)


class PatchGenerator:
    @staticmethod
    async def generate_patch(
        file_path: str,
        original_code: str,
        task_desc: str,
        error_context: str = None
    ) -> str:
        """Kích hoạt LLM phân tích mã nguồn và sinh bản vá Unified Diff."""
        llm = get_llm()

        prompt = (
            "Bạn là một AI Software Engineer hàng đầu. Hãy tạo một bản vá dưới định dạng Unified Diff "
            "để thực hiện chỉnh sửa mã nguồn sau đây.\n\n"
            f"File cần sửa: {file_path}\n"
            f"Yêu cầu sửa đổi: {task_desc}\n"
        )

        if error_context:
            prompt += f"Thông tin lỗi chạy thử nghiệm:\n{error_context}\n\n"

        prompt += (
            f"Mã nguồn hiện tại của file {file_path}:\n"
            "```\n"
            f"{original_code}\n"
            "```\n\n"
            "Chỉ dẫn quan trọng:\n"
            "1. Chỉ trả về một khối code block ```diff duy nhất chứa bản vá Unified Diff chuẩn.\n"
            "2. Mỗi hunk phải bắt đầu bằng dòng chỉ mục dạng @@ -start,len +start,len @@ và có các dòng ngữ cảnh khớp chính xác.\n"
            "3. Không giải thích gì thêm ngoài khối code block."
        )

        logger.info(f"Đang yêu cầu LLM sinh bản vá cho file: {file_path}")
        response = await llm.ainvoke([("user", prompt)])
        content = response.content

        # Trích xuất phần diff được bọc trong ```diff
        diff_match = re.search(r"```diff\s*\n(.*?)\n```", content, re.DOTALL)
        if diff_match:
            return diff_match.group(1).strip()

        # Fallback trong trường hợp LLM không bọc code block đúng
        fallback_match = re.search(r"```\s*\n(.*?)\n```", content, re.DOTALL)
        if fallback_match:
            return fallback_match.group(1).strip()

        return content.strip()
