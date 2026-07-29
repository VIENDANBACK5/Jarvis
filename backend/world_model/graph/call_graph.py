import logging
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


class CallGraph:
    def __init__(self):
        # Caller -> Callees
        self.forward_calls: Dict[str, Set[str]] = {}
        # Callee -> Callers (tra cứu ngược)
        self.reverse_calls: Dict[str, Set[str]] = {}

    def add_call(self, caller: str, callee: str):
        """Thêm cạnh gọi hàm: caller gọi đến callee (ví dụ: 'OrderService.create' gọi 'PaymentService.charge')."""
        if caller not in self.forward_calls:
            self.forward_calls[caller] = set()
        self.forward_calls[caller].add(callee)

        if callee not in self.reverse_calls:
            self.reverse_calls[callee] = set()
        self.reverse_calls[callee].add(caller)

    def get_callers(self, callee: str) -> List[str]:
        """Trả về danh sách các method/hàm gọi đến method/hàm chỉ định."""
        return list(self.reverse_calls.get(callee, []))
