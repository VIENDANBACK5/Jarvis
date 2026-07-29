import logging
from typing import Dict, Any

from backend.learning.failure_analysis import FailureAnalyzer

logger = logging.getLogger(__name__)


class CriticAgent:
    def __init__(self):
        self.analyzer = FailureAnalyzer()

    async def analyze_failure(self, error_message: str) -> Dict[str, str]:
        """Chuẩn đoán nguyên nhân gốc (RCA) của lỗi thông qua FailureAnalyzer."""
        logger.info("CriticAgent: Đang chuẩn đoán lỗi...")
        diagnosis = await self.analyzer.analyze(error_message)
        logger.info(f"CriticAgent: Kết quả RCA -> Category: {diagnosis['category']} | Root Cause: {diagnosis['root_cause']}")
        return diagnosis
