import os
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class SkillStore:
    def __init__(self, workspace_dir: str):
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.skills_json_path = os.path.join(self.workspace_dir, "skills.json")
        self.markdown_dir = os.path.join(self.workspace_dir, "skills", "markdown")

    def load_skills(self) -> List[Dict[str, Any]]:
        """Nạp danh sách kỹ năng từ tệp skills.json."""
        if not os.path.exists(self.skills_json_path):
            return []
        try:
            with open(self.skills_json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Lỗi khi đọc file skills.json: {str(e)}")
            return []

    def save_skills(self, skills: List[Dict[str, Any]]):
        """Lưu trữ danh sách kỹ năng cấu trúc vào tệp skills.json."""
        try:
            with open(self.skills_json_path, "w", encoding="utf-8") as f:
                json.dump(skills, f, indent=2)
            logger.info(f"SkillStore: Saved {len(skills)} skills to skills.json")
        except Exception as e:
            logger.error(f"Lỗi khi ghi file skills.json: {str(e)}")

    def export_markdown(self, skill: Dict[str, Any]) -> bool:
        """Đồng bộ xuất tệp cẩm nang kỹ năng Markdown phục vụ khả năng quan sát."""
        skill_name = skill.get("name", "unknown_skill")
        os.makedirs(self.markdown_dir, exist_ok=True)
        file_path = os.path.join(self.markdown_dir, f"{skill_name}.md")
        
        try:
            procedure_str = "\n".join(f"{i+1}. **{step}**" for i, step in enumerate(skill.get("procedure", [])))
            content = (
                f"# Skill: {skill_name}\n\n"
                f"### Trigger Tags:\n"
                f"- {', '.join(skill.get('trigger_tags', []))}\n\n"
                f"### Stats:\n"
                f"- **Success Rate**: {skill.get('success_rate', 1.0) * 100}%\n"
                f"- **Usage Count**: {skill.get('usage_count', 1)}\n"
                f"- **Avg Reward**: {skill.get('reward', 0.8)}\n\n"
                f"### Procedure:\n"
                f"{procedure_str}\n"
            )
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"SkillStore: Exported cẩm nang Markdown {file_path}")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi xuất markdown cho skill {skill_name}: {str(e)}")
            return False
