import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ResourceMonitor:
    def __init__(self, memory_limit_mb: int = 512, cpu_limit_cores: float = 1.0):
        self.memory_limit_mb = memory_limit_mb
        self.cpu_limit_cores = cpu_limit_cores

    def check_resource_limits(self, memory_used_mb: float, cpu_used_pct: float) -> Dict[str, Any]:
        """Giám sát mức tiêu thụ tài nguyên RAM/CPU của Sandbox."""
        is_safe = memory_used_mb <= self.memory_limit_mb
        return {
            "memory_used_mb": memory_used_mb,
            "memory_limit_mb": self.memory_limit_mb,
            "cpu_used_pct": cpu_used_pct,
            "is_safe": is_safe
        }
