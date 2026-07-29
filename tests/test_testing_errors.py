import pytest
from backend.testing.test_selector import TestSelector
from backend.errors.classifier import ErrorClassifier


def test_test_selector(tmp_path):
    # Dựng cấu trúc codebase giả lập trong tmp_path
    (tmp_path / "config").mkdir()
    (tmp_path / "api").mkdir()
    (tmp_path / "tests").mkdir()
    
    (tmp_path / "config" / "settings.py").write_text("APP_NAME = 'Jarvis'\n", encoding="utf-8")
    (tmp_path / "api" / "routes.py").write_text(
        "from config.settings import APP_NAME\n"
        "def route_chat(): pass\n",
        encoding="utf-8"
    )
    (tmp_path / "tests" / "test_routes.py").write_text(
        "from api.routes import route_chat\n"
        "def test_chat(): assert True\n",
        encoding="utf-8"
    )

    selector = TestSelector(str(tmp_path))

    # 1. Thay đổi cục bộ (api/routes.py) -> Chỉ chạy test liên quan (tests/test_routes.py)
    res_local = selector.select_tests(["api/routes.py"])
    assert res_local["run_all"] is False
    assert "tests/test_routes.py" in res_local["affected_tests"]
    assert "pytest" in res_local["command"]
    assert "tests/test_routes.py" in res_local["command"]

    # 2. Thay đổi toàn cục (config/settings.py) -> Chạy toàn bộ test suite
    res_global = selector.select_tests(["config/settings.py"])
    assert res_global["run_all"] is True
    assert res_global["command"] == "pytest"


def test_error_classifier_dependency():
    stderr = "Traceback (most recent call): ... \nModuleNotFoundError: No module named 'numpy'"
    stdout = ""
    
    res = ErrorClassifier.classify_error(stderr, stdout)
    assert res["category"] == "DEPENDENCY_ERROR"
    assert res["repair_strategy"] == "INSTALL_PACKAGE"
    assert res["target_package"] == "numpy"


def test_error_classifier_syntax():
    stderr = "  File \"main.py\", line 15\n    def run()\n             ^\nSyntaxError: invalid syntax"
    stdout = ""
    
    res = ErrorClassifier.classify_error(stderr, stdout)
    assert res["category"] == "SYNTAX_ERROR"
    assert res["repair_strategy"] == "FIX_SYNTAX"
    assert res["error_line"] == "15"


def test_error_classifier_logic():
    stderr = "AssertionError: assert 1 == 2"
    stdout = "FAILED tests/test_api.py::test_chat"
    
    res = ErrorClassifier.classify_error(stderr, stdout)
    assert res["category"] == "LOGIC_ERROR"
    assert res["repair_strategy"] == "MODIFY_LOGIC"
