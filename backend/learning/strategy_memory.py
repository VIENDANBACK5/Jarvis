import os
import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class StrategyMemory:
    def __init__(self, db_path: str):
        self.db_path = os.path.abspath(db_path)
        self.weights: Dict[str, float] = {}
        self.load_weights()

    def load_weights(self):
        """Nạp trọng số các chiến lược từ file json."""
        if not os.path.exists(self.db_path):
            self.weights = self._get_default_weights()
            self.save_weights()
            return

        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                self.weights = json.load(f)
        except Exception as e:
            logger.error(f"Lỗi khi đọc file trọng số chiến lược: {str(e)}")
            self.weights = self._get_default_weights()

    def save_weights(self):
        """Ghi lưu trọng số chiến lược xuống ổ đĩa."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.weights, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Lỗi khi lưu file trọng số chiến lược: {str(e)}")

    def get_best_strategy(self) -> str:
        """Lấy ra chiến lược có trọng số cao nhất hiện tại."""
        if not self.weights:
            return "modify_logic"
        return max(self.weights, key=self.weights.get)

    def update_weights(self, strategy_name: str, reward: float, learning_rate: float = 0.1):
        """Cập nhật trọng số của một chiến lược dựa trên phần thưởng thực tế nhận được.
        
        Công thức: weight = weight + learning_rate * (reward - weight)
        """
        if strategy_name not in self.weights:
            self.weights[strategy_name] = 0.5

        old_weight = self.weights[strategy_name]
        new_weight = old_weight + learning_rate * (reward - old_weight)
        
        # Bó chặt trọng số trong khoảng 0.0 đến 1.0
        self.weights[strategy_name] = round(max(0.0, min(1.0, new_weight)), 3)
        
        logger.info(
            f"StrategyMemory: Updated {strategy_name} | "
            f"Old Weight: {old_weight:.3f} -> New Weight: {self.weights[strategy_name]:.3f}"
        )
        self.save_weights()

    def _get_default_weights(self) -> Dict[str, float]:
        """Thiết lập trọng số chiến lược ban đầu mặc định."""
        return {
            "modify_logic": 0.6,
            "modify_tests": 0.3,
            "modify_config": 0.1
        }
