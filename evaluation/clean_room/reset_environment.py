import os
import json
import logging

logger = logging.getLogger(__name__)


def reset_environment(workspace_dir: str = "."):
    """Reset sạch sẽ toàn bộ trạng thái bộ nhớ, skill, principle và experiment về trạng thái Cold Start."""
    base_dir = os.path.abspath(workspace_dir)
    
    files_to_reset = [
        os.path.join(base_dir, "skills.json"),
        os.path.join(base_dir, "principles.json"),
        os.path.join(base_dir, "experiments.json"),
        os.path.join(base_dir, "failed_hypothesis.json"),
        os.path.join(base_dir, "experience.json"),
        os.path.join(base_dir, "backend", "autonomy", "research", "papers.json")
    ]
    
    for file_path in files_to_reset:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        print(f"Clean Room: Reset {file_path} -> []")

    print("Clean Room Environment Reset: SUCCESSFUL (Cold Start Ready)")


if __name__ == "__main__":
    reset_environment()
