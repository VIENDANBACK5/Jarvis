import json
import uuid
import logging
from typing import Dict, Any, Optional

from backend.services.llm import get_llm

logger = logging.getLogger(__name__)


class HypothesisGenerator:
    def __init__(self):
        pass

    async def generate_hypothesis(self, miner_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Optimizer Meta-Agent phân tích bottlenecks và sinh giả thuyết cải tiến prompts/configs."""
        logger.info("HypothesisGenerator: Optimizer Meta-Agent đang phân tích bottlenecks...")
        
        llm = get_llm()
        
        prompt = (
            f"Bạn là Optimizer Meta-Agent điều hành Jarvis. Hãy phân tích bottlenecks thực tế của Agent sau:\n"
            f"{json.dumps(miner_stats, indent=2)}\n\n"
            f"Hãy đưa ra 1 đề xuất cải tiến Prompts/Weights duy nhất để tối ưu hóa hiệu năng của Agent.\n"
            f"Trả về kết quả duy nhất ở định dạng JSON thô (không có markdown code block) chứa chính xác các trường sau:\n"
            f"{{\n"
            f"  \"hypothesis_id\": \"hyp-XXX\",\n"
            f"  \"description\": \"mô tả ngắn gọn về giải pháp tối ưu\",\n"
            f"  \"target_file\": \"đường dẫn file prompts được phép tự sửa đổi (ví dụ: backend/config/prompts/coder.txt)\",\n"
            f"  \"proposed_change\": \"nội dung thay đổi chi tiết hoặc chỉ thị bổ sung mới cho prompt\",\n"
            f"  \"confidence\": 0.85\n"
            f"}}"
        )

        try:
            response = await llm.ainvoke([("user", prompt)])
            cleaned_content = response.content.strip()
            if cleaned_content.startswith("```"):
                lines = cleaned_content.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned_content = "\n".join(lines).strip()

            proposal = json.loads(cleaned_content)
            logger.info(f"HypothesisGenerator: Generated hypothesis {proposal.get('hypothesis_id')} for {proposal.get('target_file')}")
            return proposal
        except Exception as e:
            logger.error(f"Lỗi khi sinh giả thuyết cải tiến: {str(e)}")
            # Fallback mặc định
            return {
                "hypothesis_id": f"hyp-{uuid.uuid4().hex[:8]}",
                "description": "Bổ sung chỉ thị kiểm tra import kỹ hơn.",
                "target_file": "backend/config/prompts/coder.txt",
                "proposed_change": "Hãy luôn kiểm tra các thư viện import xem có tồn tại không trước khi import sử dụng.",
                "confidence": 0.50
            }
