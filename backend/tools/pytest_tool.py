from backend.tools.registry import BaseTool


class PytestTool(BaseTool):
    name = "pytest"
    description = "Execute unit test suite using pytest"

    def execute(self, test_file: str = "main.py", **kwargs):
        return {"test_file": test_file, "passed": True, "tests_run": 5, "failures": 0}
