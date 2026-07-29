import os
from functools import lru_cache
from pathlib import Path


class PromptManager:
    def __init__(self, prompts_dir: Path | str = None):
        if prompts_dir is None:
            # Default directory is backend/prompts relative to the project root
            base_dir = Path(__file__).resolve().parents[1]
            self.prompts_dir = base_dir / "prompts"
        else:
            self.prompts_dir = Path(prompts_dir)
        self._cache = {}

    def get_prompt(self, name: str) -> str:
        """Đọc và cache prompt từ file markdown."""
        if name in self._cache:
            return self._cache[name]

        # Look for markdown files
        file_path = self.prompts_dir / f"{name}.md"
        if not file_path.exists():
            # Fallback to plain text files if md doesn't exist
            file_path = self.prompts_dir / f"{name}.txt"

        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found for: {name} at {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        self._cache[name] = content
        return content

    def reload(self):
        """Xóa cache để tải lại prompts mới."""
        self._cache.clear()


@lru_cache
def get_prompt_manager() -> PromptManager:
    return PromptManager()


def get_prompt(name: str) -> str:
    """Helper function tiện lợi để lấy nhanh prompt."""
    return get_prompt_manager().get_prompt(name)
