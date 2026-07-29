from backend.tools.registry import BaseTool


class ReadTool(BaseTool):
    name = "read_file"
    description = "Read file contents from repository"

    def execute(self, filepath: str = "", **kwargs):
        return {"filepath": filepath, "content": f"# Sample content of {filepath}\ndef auth(): pass"}
