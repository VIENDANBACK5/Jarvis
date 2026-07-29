import os
import json
import pytest

from backend.world_model.parser.ast_parser import ASTParser
from backend.world_model.parser.symbol_resolver import SymbolResolver
from backend.world_model.graph.dependency_graph import DependencyGraph
from backend.world_model.graph.call_graph import CallGraph
from backend.world_model.graph.test_graph import CoverageGraph
from backend.world_model.analysis.impact_predictor import ImpactPredictor
from backend.world_model.memory.architecture_store import ArchitectureStore


def test_ast_parser(tmp_path):
    code = (
        "import os\n"
        "from backend.services.llm import get_llm\n\n"
        "class Order:\n"
        "    def create(self):\n"
        "        pay = Payment()\n"
        "        pay.charge()\n"
    )
    filepath = tmp_path / "order.py"
    filepath.write_text(code, encoding="utf-8")

    structure = ASTParser.parse_file(str(filepath))
    
    assert "os" in structure["imports"]
    assert "backend.services.llm" in structure["imports"]
    assert structure["classes"][0]["name"] == "Order"
    assert "create" in structure["classes"][0]["methods"]
    
    # Xác minh trích xuất calls
    call_names = [c["func_name"] for c in structure["calls"]]
    assert "Payment" in call_names
    assert "charge" in call_names


def test_symbol_resolver():
    code = (
        "pay = Payment()\n"
        "pay.charge()\n"
    )
    resolver = SymbolResolver()
    resolver.build_symbol_table(code)
    
    assert resolver.resolve_type("pay") == "Payment"
    assert resolver.resolve_call("pay", "charge") == "Payment.charge"
    assert resolver.resolve_call("unknown_var", "charge") == "Unknown.charge"


def test_dependency_graph():
    graph = DependencyGraph()
    graph.add_dependency("order.py", "payment.py", "IMPORT")
    graph.add_dependency("checkout.py", "payment.py", "IMPORT")

    dependents = graph.get_dependent_files("payment.py")
    assert "order.py" in dependents
    assert "checkout.py" in dependents


def test_call_graph():
    graph = CallGraph()
    graph.add_call("OrderService.create", "PaymentService.charge")
    graph.add_call("CheckoutService.pay", "PaymentService.charge")

    callers = graph.get_callers("PaymentService.charge")
    assert "OrderService.create" in callers
    assert "CheckoutService.pay" in callers


def test_test_graph_and_predictor(tmp_path):
    ws_dir = tmp_path / "app"
    os.makedirs(ws_dir / "backend")
    os.makedirs(ws_dir / "tests")

    # Tạo file nguồn
    payment_code = (
        "class PaymentService:\n"
        "    def charge(self):\n"
        "        pass\n"
    )
    with open(ws_dir / "backend" / "payment.py", "w", encoding="utf-8") as f:
        f.write(payment_code)

    # Tạo file test
    test_code = (
        "from backend.payment import PaymentService\n"
        "def test_payment():\n"
        "    pass\n"
    )
    with open(ws_dir / "tests" / "test_payment.py", "w", encoding="utf-8") as f:
        f.write(test_code)

    # Tạo file core coordinator
    coordinator_code = (
        "class Coordinator:\n"
        "    pass\n"
    )
    with open(ws_dir / "backend" / "coordinator.py", "w", encoding="utf-8") as f:
        f.write(coordinator_code)

    # Khởi tạo ImpactPredictor
    predictor = ImpactPredictor(str(ws_dir))
    
    # 1. Kiểm tra file thông thường -> Risk LOW/MEDIUM
    res_pay = predictor.calculate_impact_score(str(ws_dir / "backend" / "payment.py"))
    assert res_pay["risk_level"] in ["LOW", "MEDIUM"]
    assert "tests/test_payment.py" in res_pay["affected_tests"]

    # 2. Kiểm tra file core coordinator -> Criticality = 2.0 -> Risk tăng lên
    res_core = predictor.calculate_impact_score(str(ws_dir / "backend" / "coordinator.py"))
    assert res_core["impact_score"] >= 0.4  # Đảm bảo cộng điểm criticality
