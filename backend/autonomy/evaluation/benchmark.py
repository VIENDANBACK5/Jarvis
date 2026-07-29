import time
import asyncio
import logging
from typing import Dict, Any

from backend.evaluation.reward import calculate_reward

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    def __init__(self, workspace_dir: str):
        self.workspace_dir = os.path.abspath(workspace_dir)

    async def run_quick_evaluation(self, test_target: str = "tests/test_learning.py") -> float:
        """Chạy đánh giá nhanh (Quick Evaluation) để tính toán điểm reward trung bình."""
        logger.info(f"BenchmarkRunner: Đang chạy Quick Evaluation trên target: {test_target}...")
        start_time = time.time()
        
        try:
            # Chạy tập hợp các test case kiểm định
            proc = await asyncio.create_subprocess_exec(
                "pytest", test_target,
                cwd=self.workspace_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            elapsed = time.time() - start_time
            
            # Tỷ lệ test case pass
            success_rate = 1.0 if proc.returncode == 0 else 0.0
            
            # Tính toán phần thưởng cải tiến
            reward = calculate_reward(
                test_success=success_rate,
                code_quality=1.0 if success_rate == 1.0 else 0.2,
                token_cost_usd=0.005,  # Chi phí token giả lập
                execution_time_sec=elapsed
            )
            
            logger.info(f"BenchmarkRunner: Hoàn thành đánh giá. Success: {success_rate} | Latency: {elapsed:.3f}s | Reward: {reward:.4f}")
            return reward
        except Exception as e:
            logger.error(f"BenchmarkRunner: Lỗi khi chạy Quick Evaluation: {str(e)}")
            return -1.0
            
import os
