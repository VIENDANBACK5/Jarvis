import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from backend.self_modify.policy import SelfModificationPolicy
from backend.self_modify.proposal import SelfModificationProposal
from backend.self_modify.judge import IndependentJudgeAgent
from backend.self_modify.evaluator import SelfModificationEvaluator
from backend.self_modify.merger import SelfModificationMerger


def test_self_modification_policy():
    # 1. File trong whitelist prompts -> Được phép sửa
    allowed, err = SelfModificationPolicy.is_modification_allowed("backend/config/prompts/coder.txt")
    assert allowed is True
    assert err is None

    # 2. File trong blacklist sandbox -> Bị cấm sửa
    blocked, err_b = SelfModificationPolicy.is_modification_allowed("backend/sandbox/service.py")
    assert blocked is False
    assert "Cấm tự động sửa đổi" in err_b


def test_self_modification_proposal():
    proposal = SelfModificationProposal(
        target_file="backend/config/prompts/coder.txt",
        proposed_change="Hãy lập trình thông minh hơn.",
        rationale="Nâng cao chất lượng prompt"
    )
    assert proposal.proposal_id.startswith("prop-")
    assert proposal.target_file == "backend/config/prompts/coder.txt"
    assert proposal.confidence == 0.85


@pytest.mark.asyncio
async def test_judge_agent_decision():
    judge = IndependentJudgeAgent()

    # 1. Đề xuất hợp lệ và an toàn -> Approved
    proposal_ok = SelfModificationProposal(
        target_file="backend/config/prompts/coder.txt",
        proposed_change="Hãy kiểm tra các import cẩn thận.",
        rationale="Tránh lỗi ModuleNotFoundError"
    )
    
    mock_llm_ok = MagicMock()
    mock_llm_ok.ainvoke = AsyncMock(return_value=MagicMock(content="{\"approved\": true, \"reason\": \"Mã thay đổi hoàn toàn an toàn và logic tốt.\"}"))

    with patch("backend.self_modify.judge.get_llm", return_value=mock_llm_ok):
        res = await judge.verify_proposal(proposal_ok)
        assert res["approved"] is True

    # 2. Đề xuất vi phạm chính sách file -> Reject ngay lập tức không gọi LLM
    proposal_blocked = SelfModificationProposal(
        target_file="backend/sandbox/sandbox.py",
        proposed_change="Sửa core sandbox",
        rationale="Hack sandbox"
    )
    res_blocked = await judge.verify_proposal(proposal_blocked)
    assert res_blocked["approved"] is False
    assert "Cấm tự động sửa đổi" in res_blocked["reason"]


@pytest.mark.asyncio
async def test_self_modification_evaluator(tmp_path):
    evaluator = SelfModificationEvaluator(str(tmp_path))
    
    proposal = SelfModificationProposal(
        target_file="backend/config/prompts/coder.txt",
        proposed_change="Change prompt",
        rationale="Optimize"
    )

    mock_runner = MagicMock()
    mock_runner.run_quick_evaluation = AsyncMock(return_value=0.85)
    evaluator.runner = mock_runner

    reward = await evaluator.evaluate_change(proposal, "tests/test_openai_api.py")
    assert reward == 0.85
    mock_runner.run_quick_evaluation.assert_called_once_with("tests/test_openai_api.py")


@pytest.mark.asyncio
async def test_self_modification_merger(tmp_path):
    merger = SelfModificationMerger(str(tmp_path))
    
    proposal = SelfModificationProposal(
        target_file="backend/config/prompts/coder.txt",
        proposed_change="Change prompt",
        rationale="Optimize"
    )

    mock_branch_manager = MagicMock()
    mock_branch_manager.checkout_main_and_merge = AsyncMock(return_value=True)
    mock_branch_manager.rollback_and_cleanup = AsyncMock(return_value=True)
    merger.branch_manager = mock_branch_manager

    # 1. Judge đồng ý + Reward tăng -> Merge
    success, msg = await merger.execute_integration(
        proposal,
        judge_approved=True,
        old_reward=0.50,
        new_reward=0.60,
        branch_name="experiment/prop-123"
    )
    assert success is True
    assert "Tích hợp thành công" in msg
    mock_branch_manager.checkout_main_and_merge.assert_called_once_with("experiment/prop-123")

    # 2. Judge bác bỏ -> Revert ngay lập tức
    success_r, msg_r = await merger.execute_integration(
        proposal,
        judge_approved=False,
        old_reward=0.50,
        new_reward=0.60,
        branch_name="experiment/prop-456"
    )
    assert success_r is False
    assert "Bác bỏ tích hợp" in msg_r
    mock_branch_manager.rollback_and_cleanup.assert_called_once_with("experiment/prop-456")
