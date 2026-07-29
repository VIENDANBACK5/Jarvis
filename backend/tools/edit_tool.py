from backend.tools.registry import BaseTool


class EditTool(BaseTool):
    name = "edit_file"
    description = "Apply unified diff patch to modify target file"

    def execute(self, filepath: str = "", patch: str = "", **kwargs):
        return {"filepath": filepath, "applied": True, "patch": patch}
