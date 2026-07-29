import os
import asyncio
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class BranchManager:
    def __init__(self, repo_dir: str):
        self.repo_dir = os.path.abspath(repo_dir)

    async def _run_git(self, *args: str) -> Tuple[int, str, str]:
        """Thực thi lệnh git trong thư mục repo."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", *args,
                cwd=self.repo_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            return proc.returncode, stdout.decode().strip(), stderr.decode().strip()
        except Exception as e:
            return -1, "", str(e)

    async def create_experiment_branch(self, branch_name: str) -> bool:
        """Tạo và chuyển sang nhánh git phụ mới để chạy thử nghiệm."""
        # Chuyển về trạng thái sạch trước khi tách nhánh
        await self._run_git("reset", "--hard", "HEAD")
        await self._run_git("clean", "-fd")
        
        code, out, err = await self._run_git("checkout", "-b", branch_name)
        if code != 0:
            # Nhánh có sẵn, chuyển hướng checkout thẳng
            code, out, err = await self._run_git("checkout", branch_name)
            
        logger.info(f"BranchManager: Checkout sang nhánh thử nghiệm '{branch_name}' (status={code == 0})")
        return code == 0

    async def apply_proposal_change(self, target_file: str, proposed_change: str) -> bool:
        """Ghi nhận thay đổi lên tệp tin chỉ định."""
        full_path = os.path.abspath(os.path.join(self.repo_dir, target_file))
        try:
            # Ghi đè hoặc append đề xuất tối ưu vào file
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(proposed_change)
            logger.info(f"BranchManager: Đã áp dụng đề xuất thay đổi lên {target_file}")
            return True
        except Exception as e:
            logger.error(f"BranchManager: Lỗi khi áp dụng thay đổi lên {target_file}: {str(e)}")
            return False

    async def checkout_main_and_merge(self, branch_name: str) -> bool:
        """Chuyển về nhánh main và merge nhánh thử nghiệm cải tiến vào."""
        # Checkout main
        code, out, err = await self._run_git("checkout", "main")
        if code != 0:
            code, out, err = await self._run_git("checkout", "master")
            if code != 0:
                logger.error("BranchManager: Không thể chuyển về nhánh main/master để merge.")
                return False

        # Merge nhánh thử nghiệm
        code_m, out_m, err_m = await self._run_git("merge", branch_name, "--no-edit")
        logger.info(f"BranchManager: Merge {branch_name} vào main (status={code_m == 0})")
        
        # Xóa nhánh phụ sau khi merge xong
        await self._run_git("branch", "-d", branch_name)
        return code_m == 0

    async def rollback_and_cleanup(self, branch_name: str) -> bool:
        """Hủy bỏ thử nghiệm, chuyển về main và xóa nhánh phụ."""
        code, out, err = await self._run_git("checkout", "main")
        if code != 0:
            await self._run_git("checkout", "master")
            
        await self._run_git("reset", "--hard", "HEAD")
        await self._run_git("clean", "-fd")
        
        # Xóa cứng nhánh thử nghiệm hỏng
        await self._run_git("branch", "-D", branch_name)
        logger.info(f"BranchManager: Đã hoàn nguyên sạch và xóa nhánh hỏng '{branch_name}'")
        return True
