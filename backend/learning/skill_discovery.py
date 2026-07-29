import logging
from typing import List, Dict, Any

from backend.learning.experience import ExperienceStore
from backend.learning.skills.extractor import SkillExtractor
from backend.learning.skills.evaluator import SkillEvaluator
from backend.learning.skills.consolidator import SkillConsolidator
from backend.learning.memory.skill_store import SkillStore

logger = logging.getLogger(__name__)


class SkillDiscoverer:
    def __init__(self, workspace_dir: str, experience_dir: str):
        self.skill_store = SkillStore(workspace_dir)
        self.exp_store = ExperienceStore(experience_dir)

    def discover_new_skills(self) -> List[Dict[str, Any]]:
        """Quét trải nghiệm tốt, trích xuất, gộp và đồng bộ hóa lưu trữ kỹ năng mới."""
        logger.info("SkillDiscoverer: Bắt đầu quét phát hiện kỹ năng mới...")
        
        # 1. Nạp danh sách kỹ năng hiện có
        existing_skills = self.skill_store.load_skills()
        existing_skills_dict = {s["name"]: s for s in existing_skills}

        # 2. Quét experiences tìm các bài học thành công
        import os
        experiences = []
        if os.path.exists(self.exp_store.store_dir):
            for filename in os.listdir(self.exp_store.store_dir):
                if filename.startswith("exp_") and filename.endswith(".json"):
                    task_id = filename[4:-5]
                    exp = self.exp_store.load_experience(task_id)
                    # Chỉ lấy kinh nghiệm có reward cao >= 0.70
                    if exp and (exp.reward or 0.0) >= 0.70:
                        experiences.append(exp)

        # 3. Trích xuất kỹ năng ứng viên
        new_candidates = []
        for exp in experiences:
            candidate = SkillExtractor.extract_skill(exp)
            # Tính độ tin cậy ban đầu
            candidate["confidence"] = SkillEvaluator.calculate_confidence(candidate)
            new_candidates.append(candidate)

        # 4. Gộp các kỹ năng tương đồng
        all_skills = list(existing_skills_dict.values()) + new_candidates
        consolidated = SkillConsolidator.consolidate_skills(all_skills)

        # 5. Lưu trữ và xuất Markdown
        self.skill_store.save_skills(consolidated)
        for skill in consolidated:
            self.skill_store.export_markdown(skill)

        logger.info(f"SkillDiscoverer: Đã hoàn tất phát hiện kỹ năng. Tổng số kỹ năng: {len(consolidated)}")
        return consolidated
