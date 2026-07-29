import os
import pytest
from backend.workspace.index.dependency_graph import DependencyGraph
from backend.workspace.index.symbol_graph import SymbolGraph
from backend.workspace.analyzer.architecture import ImpactAnalyzer


def test_dependency_graph(tmp_path):
    # Dựng cấu trúc codebase giả lập trong tmp_path
    (tmp_path / "config").mkdir()
    (tmp_path / "api").mkdir()
    
    (tmp_path / "config" / "settings.py").write_text("APP_NAME = 'Jarvis'\n", encoding="utf-8")
    (tmp_path / "api" / "routes.py").write_text(
        "from config.settings import APP_NAME\n"
        "def route_chat(): pass\n",
        encoding="utf-8"
    )
    (tmp_path / "main.py").write_text(
        "from api.routes import route_chat\n"
        "print('Running app')\n",
        encoding="utf-8"
    )

    dep_graph = DependencyGraph(str(tmp_path))
    dep_graph.build_graph()

    # 1. Kiểm tra dependencies (main.py -> api/routes.py -> config/settings.py)
    assert "api/routes.py" in dep_graph.get_dependencies("main.py")
    assert "config/settings.py" in dep_graph.get_dependencies("api/routes.py")

    # 2. Kiểm tra dependents ngược (config/settings.py <- api/routes.py <- main.py)
    assert "api/routes.py" in dep_graph.get_dependents("config/settings.py")
    assert "main.py" in dep_graph.get_dependents("api/routes.py")


def test_symbol_graph_definition_and_references(tmp_path):
    (tmp_path / "service.py").write_text(
        "class AuthService:\n"
        "    def login(self):\n"
        "        return True\n",
        encoding="utf-8"
    )
    (tmp_path / "routes.py").write_text(
        "from service import AuthService\n"
        "def handle_login():\n"
        "    auth = AuthService()\n"
        "    auth.login()\n",
        encoding="utf-8"
    )

    sym_graph = SymbolGraph(str(tmp_path))
    sym_graph.build_graph()

    # 1. Test Find Definition
    defs = sym_graph.find_definition("AuthService")
    assert len(defs) == 1
    assert defs[0]["filepath"] == "service.py"
    assert defs[0]["type"] == "class"

    # 2. Test Find References (AuthService được tham chiếu trong routes.py)
    refs = sym_graph.find_references("AuthService")
    assert len(refs) == 2  # line 1 (import) và line 3 (instantiation)
    filepaths = [r["filepath"] for r in refs]
    assert all(path == "routes.py" for path in filepaths)


def test_impact_analysis(tmp_path):
    (tmp_path / "config.py").write_text("DB_URL = 'sqlite://'\n", encoding="utf-8")
    (tmp_path / "db.py").write_text(
        "from config import DB_URL\n"
        "class Database:\n"
        "    def connect(self): pass\n",
        encoding="utf-8"
    )
    (tmp_path / "test_db.py").write_text(
        "from db import Database\n"
        "def test_connection():\n"
        "    db = Database()\n",
        encoding="utf-8"
    )

    analyzer = ImpactAnalyzer(str(tmp_path))
    analyzer.initialize()

    # Phân tích tác động khi sửa đổi file config.py
    report = analyzer.analyze_impact("config.py")
    
    assert report["target_file"] == "config.py"
    # Sửa config.py ảnh hưởng trực tiếp tới db.py
    assert "db.py" in report["direct_dependents"]
    # Sửa config.py ảnh hưởng gián tiếp tới test_db.py qua db.py
    assert "test_db.py" in report["indirect_dependents"]
    # Nhận diện test_db.py là file test chịu ảnh hưởng
    assert "test_db.py" in report["affected_tests"]
    # Nhận diện các symbol trong db.py chịu ảnh hưởng lan truyền
    symbols = [s["name"] for s in report["affected_symbols"]]
    assert "Database" in symbols
