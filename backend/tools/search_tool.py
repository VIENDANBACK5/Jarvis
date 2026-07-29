from backend.tools.registry import BaseTool


class SearchTool(BaseTool):
    name = "search"
    description = "Search symbols or keywords in repository files"

    def execute(self, query: str = "", **kwargs):
        return {"query": query, "matches_found": 3, "files": ["auth.py", "config.py"]}
