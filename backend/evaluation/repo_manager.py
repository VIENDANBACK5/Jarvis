import os
import subprocess
import logging

logger = logging.getLogger(__name__)


class RepoManager:
    def __init__(self, workspace_dir: str):
        self.workspace_dir = os.path.abspath(workspace_dir)

    def backup_checkpoint(self) -> bool:
        """Đông băng trạng thái repo mã nguồn qua git stash."""
        try:
            subprocess.run(
                ["git", "add", "."],
                cwd=self.workspace_dir,
                capture_output=True,
                check=True
            )
            subprocess.run(
                ["git", "stash", "-u"],
                cwd=self.workspace_dir,
                capture_output=True,
                check=True
            )
            logger.info("RepoManager: Backed up repository state using git stash.")
            return True
        except Exception as e:
            logger.error(f"RepoManager: Lỗi khi backup checkpoint: {str(e)}")
            return False

    def restore_checkpoint(self) -> bool:
        """Khôi phục trạng thái repo sạch ban đầu."""
        try:
            subprocess.run(
                ["git", "reset", "--hard", "HEAD"],
                cwd=self.workspace_dir,
                capture_output=True,
                check=True
            )
            subprocess.run(
                ["git", "clean", "-fd"],
                cwd=self.workspace_dir,
                capture_output=True,
                check=True
            )
            # Khôi phục nếu có stash
            result = subprocess.run(
                ["git", "stash", "pop"],
                cwd=self.workspace_dir,
                capture_output=True
            )
            logger.info(f"RepoManager: Restored repository to checkpoint. pop status={result.returncode}")
            return True
        except Exception as e:
            logger.error(f"RepoManager: Lỗi khi restore checkpoint: {str(e)}")
            return False

    def apply_patch(self, patch_filepath: str) -> bool:
        """Áp dụng bản vá diff file vào repo mã nguồn."""
        if not os.path.exists(patch_filepath):
            return False
        try:
            result = subprocess.run(
                ["git", "apply", patch_filepath],
                cwd=self.workspace_dir,
                capture_output=True
            )
            if result.returncode == 0:
                logger.info("RepoManager: Applied patch successfully.")
                return True
            else:
                logger.warning(f"RepoManager: Failed to apply patch: {result.stderr.decode('utf-8')}")
                return False
        except Exception as e:
            logger.error(f"RepoManager: Lỗi khi áp dụng patch: {str(e)}")
            return False
