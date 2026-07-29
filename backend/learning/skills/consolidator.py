import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class SkillConsolidator:
    @staticmethod
    def consolidate_skills(skills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Gộp và tổng quát hóa các kỹ năng trùng lặp hoặc tương đồng (Consolidation)."""
        consolidated: List[Dict[str, Any]] = []

        for skill in skills:
            merged = False
            for existing in consolidated:
                # Tính độ tương đồng giữa các trigger tags
                set_a = set(skill.get("trigger_tags", []))
                set_b = set(existing.get("trigger_tags", []))
                intersection = set_a.intersection(set_b)
                union = set_a.union(set_b)
                similarity = len(intersection) / len(union) if union else 0.0

                # Nếu độ tương đồng >= 0.40, tiến hành gộp
                if similarity >= 0.40:
                    existing["trigger_tags"] = list(union)
                    existing["usage_count"] += skill.get("usage_count", 1)
                    
                    # Tính trung bình success rate và reward
                    existing["success_rate"] = round((existing["success_rate"] + skill.get("success_rate", 1.0)) / 2, 2)
                    existing["reward"] = round((existing["reward"] + skill.get("reward", 0.8)) / 2, 2)
                    
                    # Gộp quy trình thao tác
                    p_a = existing.get("procedure", [])
                    p_b = skill.get("procedure", [])
                    # Lấy hợp các bước theo thứ tự xuất hiện độc nhất
                    new_procedure = []
                    for step in p_a + p_b:
                        if step not in new_procedure:
                            new_procedure.append(step)
                    existing["procedure"] = new_procedure
                    
                    logger.info(f"SkillConsolidator: Merged skill '{skill['name']}' into '{existing['name']}'.")
                    merged = True
                    break
            
            if not merged:
                consolidated.append(skill.copy())
                
        return consolidated
