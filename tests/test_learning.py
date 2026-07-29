import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from backend.evaluation.reward import calculate_reward
from backend.self_modify.policy import SelfModificationPolicy
from backend.learning.experience import Experience, ExperienceStore
from backend.learning.failure_analysis import FailureAnalyzer
from backend.learning.skill_memory import SkillMemory


def test_reward_system():
    # 1. Điểm số tuyệt vời (tất cả pass, chất lượng tốt, chi phí cực nhỏ)
    reward_high = calculate_reward(
        test_success=1.0,
        code_quality=1.0,
        token_cost_usd=0.001,
        execution_time_sec=10.0
    )
    # Kỳ vọng điểm số dương và cao
    assert reward_high > 0.4
    assert reward_high <= 1.0

    # 2. Điểm số rất tệ (test hỏng, chạy lâu, tốn nhiều token)
    reward_low = calculate_reward(
        test_success=0.0,
        code_quality=0.0,
        token_cost_usd=0.5,  # Penalty = 0.1 * 50 = 5.0
        execution_time_sec=600.0  # Penalty = 0.2 * 10 = 2.0
    )
    # Bị cận biên dưới -1.0 chặn lại
    assert reward_low == -1.0


def test_self_modification_policy():
    # 1. Cho phép sửa Prompt
    allowed_path = "backend/config/prompts/coder.txt"
    allowed, _ = SelfModificationPolicy.is_modification_allowed(allowed_path)
    assert allowed is True

    # 2. Cấm sửa chính sách bảo mật
    blocked_path = "backend/self_modify/policy.py"
    allowed_blocked, reason = SelfModificationPolicy.is_modification_allowed(blocked_path)
    assert allowed_blocked is False
    assert "Cấm tự động sửa đổi" in reason

    # 3. Mặc định cấm các file chung
    general_path = "backend/main.py"
    allowed_gen, reason_gen = SelfModificationPolicy.is_modification_allowed(general_path)
    assert allowed_gen is False
    assert "không nằm trong danh sách cho phép" in reason_gen


def test_experience_store(tmp_path):
    store = ExperienceStore(str(tmp_path))
    
    exp = Experience(
        task_id="task-007",
        goal="Sửa lỗi tràn bộ nhớ cache",
        environment={"language": "python", "framework": "fastapi"},
        trajectory=[
            {"action": "search_code", "input": "cache", "result": "found cache.py"},
            {"action": "edit_file", "file": "cache.py"},
            {"action": "run_test", "result": "passed"}
        ],
        failure={"category": "logic_error", "root_cause": "cache keys duplicate"},
        final_solution={"patch": "@@ ..."},
        reward=0.75
    )

    # Lưu kinh nghiệm
    saved_path = store.save_experience(exp)
    assert os.path.exists(saved_path)

    # Nạp lại kinh nghiệm
    loaded_exp = store.load_experience("task-007")
    assert loaded_exp is not None
    assert loaded_exp.goal == "Sửa lỗi tràn bộ nhớ cache"
    assert loaded_exp.trajectory[0]["action"] == "search_code"
    assert loaded_exp.reward == 0.75


@pytest.mark.asyncio
async def test_failure_analyzer_tier1():
    analyzer = FailureAnalyzer()

    # Khớp tầng 1: ModuleNotFoundError tĩnh
    res = await analyzer.analyze("Traceback: ModuleNotFoundError: No module named 'pytest'")
    assert res["category"] == "dependency_error"
    assert "cài đặt" in res["recommendation"].lower()

    # Khớp tầng 1: PermissionError tĩnh
    res_perm = await analyzer.analyze("PermissionError: [Errno 13] Permission denied: 'test.py'")
    assert res_perm["category"] == "permission_error"


@pytest.mark.asyncio
async def test_failure_analyzer_tier2_llm_rca():
    analyzer = FailureAnalyzer()

    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = (
        "```json\n"
        "{\n"
        "  \"category\": \"logic_error\",\n"
        "  \"root_cause\": \"Hàm tính toán chia cho 0.\",\n"
        "  \"recommendation\": \"Thêm kiểm tra điều kiện mẫu số khác 0 trước khi chia.\"\n"
        "}\n"
        "```"
    )
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)

    with patch("backend.learning.failure_analysis.get_llm", return_value=mock_llm):
        # Trích xuất lỗi lạ để kích hoạt tầng 2 gọi LLM
        res = await analyzer.analyze("ZeroDivisionError: division by zero in utils.py line 40")
        assert res["category"] == "logic_error"
        assert "chia cho 0" in res["root_cause"]
        assert "khác 0" in res["recommendation"]


def test_skill_memory(tmp_path):
    db_file = tmp_path / "skills.json"
    memory = SkillMemory(str(db_file))

    # 1. Truy hồi kỹ năng phù hợp
    skills = memory.retrieve_skills("ModuleNotFoundError: No module named 'httpx'")
    assert len(skills) >= 1
    assert skills[0]["name"] == "dependency_resolver"

    # 2. Cập nhật chỉ số sử dụng
    original_rate = skills[0]["success_rate"]
    original_usage = skills[0]["usage_count"]

    memory.update_skill_stats("dependency_resolver", success=True)
    
    # Nạp lại bộ nhớ kiểm tra chỉ số mới
    new_memory = SkillMemory(str(db_file))
    updated_skill = [s for s in new_memory.skills if s["name"] == "dependency_resolver"][0]
    assert updated_skill["usage_count"] == original_usage + 1
