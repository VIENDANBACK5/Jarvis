import os
import pytest
from backend.workspace.scanner import WorkspaceScanner
from backend.workspace.parser.python import PythonSymbolParser
from backend.workspace.parser.javascript import JavaScriptSymbolParser
from backend.workspace.index.symbol_store import SymbolStore


def test_python_symbol_parser():
    parser = PythonSymbolParser()
    code = """
class MyCalculator:
    \"\"\"Docstring class.\"\"\"
    async def add(self, a, b):
        \"\"\"Add method.\"\"\"
        return a + b

def global_helper():
    pass
"""
    symbols = parser.parse_code(code)
    
    # Check Class
    classes = [s for s in symbols if s["type"] == "class"]
    assert len(classes) == 1
    assert classes[0]["name"] == "MyCalculator"
    assert classes[0]["docstring"] == "Docstring class."

    # Check Method
    methods = [s for s in symbols if s["type"] == "method"]
    assert len(methods) == 1
    assert methods[0]["name"] == "add"
    assert methods[0]["parent"] == "MyCalculator"
    assert methods[0]["docstring"] == "Add method."

    # Check Function
    funcs = [s for s in symbols if s["type"] == "function"]
    assert len(funcs) == 1
    assert funcs[0]["name"] == "global_helper"


def test_js_symbol_parser():
    parser = JavaScriptSymbolParser()
    code = """
class UserService {
    getUser() {}
}

async function fetchProducts() {}

const calculateSum = (x, y) => x + y;
"""
    symbols = parser.parse_code(code)
    
    names = [s["name"] for s in symbols]
    assert "UserService" in names
    assert "fetchProducts" in names
    assert "calculateSum" in names
    
    types = {s["name"]: s["type"] for s in symbols}
    assert types["UserService"] == "class"
    assert types["fetchProducts"] == "function"
    assert types["calculateSum"] == "function"


def test_workspace_scanner_and_store(tmp_path):
    # Tạo dự án giả lập trong tmp_path
    d = tmp_path / "sub"
    d.mkdir()
    (d / "hello.py").write_text("class Hello:\n    pass\n", encoding="utf-8")
    (d / "script.js").write_text("function run() {}", encoding="utf-8")
    (d / "ignored.txt").write_text("some text", encoding="utf-8")
    
    # Test Scanner
    scanner = WorkspaceScanner(str(tmp_path))
    files = scanner.scan()
    paths = [f["path"] for f in files]
    assert "sub/hello.py" in paths
    assert "sub/script.js" in paths
    assert "sub/ignored.txt" in paths

    # Test Store
    store = SymbolStore(str(tmp_path))
    store.index_workspace()
    
    symbols = store.query_symbol("Hello")
    assert len(symbols) == 1
    assert symbols[0]["filepath"] == "sub/hello.py"
    
    symbols_js = store.query_symbol("run")
    assert len(symbols_js) == 1
    assert symbols_js[0]["filepath"] == "sub/script.js"
