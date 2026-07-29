import asyncio
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


class GitCheckpointManager:
    def __init__(self, repo_dir: str):
        self.repo_dir = repo_dir

    async def _run_git(self, args: list[str]) -> Tuple[int, str, str]:
        """Thực thi câu lệnh git bằng subprocess."""
        proc = await asyncio.create_subprocess_exec(
            "git", *args,
            cwd=self.repo_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode, stdout.decode().strip(), stderr.decode().strip()

    async def is_git_repo(self) -> bool:
        """Kiểm tra xem thư mục hiện tại có phải repo git không."""
        code, _, _ = await self._run_git(["status"])
        return code == 0

    async def create_checkpoint(self, description: str) -> str:
        """Tạo commit checkpoint lưu trạng thái hiện tại.
        
        Trả về: commit hash của checkpoint vừa tạo.
        """
        if not await self.is_git_repo():
            raise RuntimeError(f"Thư mục {self.repo_dir} không phải là một Git repository.")

        # 1. Stage tất cả các thay đổi
        await self._run_git(["add", "."])

        # 2. Tạo checkpoint commit
        commit_msg = f"Jarvis Checkpoint: {description}"
        code, stdout, stderr = await self._run_git(["commit", "-m", commit_msg])

        if code != 0 and "nothing to commit" not in stdout and "nothing to commit" not in stderr:
            raise RuntimeError(f"Không thể tạo Git checkpoint: {stderr or stdout}")

        # 3. Lấy commit hash mới nhất vừa tạo
        _, head_hash, _ = await self._run_git(["rev-parse", "HEAD"])
        logger.info(f"Đã tạo Git Checkpoint tại commit hash: {head_hash}")
        return head_hash

    async def rollback(self, checkpoint_hash: str) -> bool:
        """Khôi phục toàn bộ mã nguồn về vị trí checkpoint_hash trước đó."""
        logger.warning(f"Đang phục hồi mã nguồn về Checkpoint: {checkpoint_hash}")
        
        # 1. Reset hard về checkpoint commit
        reset_code, _, reset_err = await self._run_git(["reset", "--hard", checkpoint_hash])
        if reset_code != 0:
            logger.error(f"Lỗi reset hard: {reset_err}")
            return False

        # 2. Dọn sạch các file/thư mục rác chưa được track (untracked)
        clean_code, _, clean_err = await self._run_git(["clean", "-fd"])
        if clean_code != 0:
            logger.error(f"Lỗi clean filesystem: {clean_err}")
            return False

        logger.info(f"Đã phục hồi mã nguồn thành công về Checkpoint: {checkpoint_hash}")
        return True

    async def get_diff(self, checkpoint_hash: str) -> str:
        """Lấy toàn bộ nội dung khác biệt kể từ checkpoint_hash."""
        code, stdout, stderr = await self._run_git(["diff", checkpoint_hash])
        if code != 0:
            logger.error(f"Lỗi lấy git diff: {stderr}")
            return ""
        return stdout
