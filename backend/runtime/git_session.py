import subprocess
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class GitSession:
    def __init__(self, workspace_dir: str = "."):
        self.workspace_dir = workspace_dir

    def create_commit(self, message: str) -> bool:
        """Tạo git commit tự động cho từng bước cập nhật thành công (Aider Style)."""
        try:
            subprocess.run(["git", "add", "."], cwd=self.workspace_dir, check=True, capture_output=True)
            res = subprocess.run(
                ["git", "commit", "-m", f"[Jarvis Auto-Commit] {message}"],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True
            )
            if res.returncode == 0:
                logger.info(f"GitSession: Created auto-commit -> {message}")
                return True
            return False
        except Exception as e:
            logger.warning(f"GitSession: Auto-commit skipped: {str(e)}")
            return False

    def create_worktree(self, task_id: str) -> str:
        """Tạo nhánh Git Worktree cô lập cho tác vụ để không làm bẩn làm nhánh hiện tại."""
        worktree_path = f".worktrees/{task_id}"
        branch_name = f"jarvis/{task_id}"
        try:
            subprocess.run(
                ["git", "worktree", "add", "-b", branch_name, worktree_path],
                cwd=self.workspace_dir,
                capture_output=True,
                check=True
            )
            logger.info(f"GitSession: Created isolated git worktree at {worktree_path}")
            return worktree_path
        except Exception as e:
            logger.warning(f"GitSession: Worktree creation fallback: {str(e)}")
            return self.workspace_dir

    def remove_worktree(self, task_id: str) -> bool:
        """Xóa bỏ Git Worktree sau khi tác vụ hoàn tất."""
        worktree_path = f".worktrees/{task_id}"
        try:
            subprocess.run(
                ["git", "worktree", "remove", "--force", worktree_path],
                cwd=self.workspace_dir,
                capture_output=True,
                check=True
            )
            logger.info(f"GitSession: Removed worktree {worktree_path}")
            return True
        except Exception as e:
            logger.warning(f"GitSession: Worktree removal fallback: {str(e)}")
            return False
