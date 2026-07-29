import json
import logging
from typing import Dict, Any

from backend.services.llm import get_llm
from backend.self_modify.policy import SelfModificationPolicy
from backend.self_modify.proposal import SelfModificationProposal

logger = logging.getLogger(__name__)


class IndependentJudgeAgent:
    def __init__(self):
        pass

    async def verify_proposal(self, proposal: SelfModificationProposal) -> Dict[str, Any]:
        """Independent Judge Agent đánh giá mức độ an toàn và chất lượng của đề xuất."""
        logger.info(f"IndependentJudgeAgent: Đang kiểm duyệt đề xuất {proposal.proposal_id}...")
        
        # 1. Rà soát chính sách bảo mật trước
        allowed, reason = SelfModificationPolicy.is_modification_allowed(proposal.target_file)
        if not allowed:
            logger.warning(f"IndependentJudgeAgent: Bác bỏ vì vi phạm chính sách bảo mật: {reason}")
            return {"approved": False, "reason": reason}

        # 2. LLM đóng vai trò phán quyết độc lập phân tích mã độc, backdoor
        llm = get_llm()
        
        prompt = (
            f"Bạn là Independent Judge Agent bảo vệ Jarvis. Hãy rà soát đề xuất tự sửa đổi sau:\n"
            f"Target File: {proposal.target_file}\n"
            f"Proposed Change: {proposal.proposed_change}\n"
            f"Rationale: {proposal.rationale}\n\n"
            f"Hãy kiểm tra nghiêm ngặt xem thay đổi này có cài cắm backdoor, phá hủy Sandbox, "
            f"gây rò rỉ mã độc hoặc gây sụp đổ logic hệ thống không.\n"
            f"Trả về kết quả duy nhất ở định dạng JSON thô chứa chính xác các trường sau:\n"
            f"{{\n"
            f"  \"approved\": true,\n"
            f"  \"reason\": \"phân tích chi tiết lý do duyệt hoặc bác bỏ\"\n"
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

            result = json.loads(cleaned_content)
            logger.info(f"IndependentJudgeAgent: Phán quyết xong: Approved={result.get('approved')} | Reason={result.get('reason')}")
            return result
        except Exception as e:
            logger.error(f"Lỗi trong quá trình Judge duyệt đề xuất: {str(e)}")
            return {"approved": False, "reason": f"Lỗi hệ thống khi phân tích LLM: {str(e)}"}
