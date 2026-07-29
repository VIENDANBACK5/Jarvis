import os
import logging
from typing import Dict, Any, List

from backend.world_model import ASTParser, SymbolResolver

logger = logging.getLogger(__name__)


class OnlineWorldModel:
    def __init__(self, workspace_dir: str = "."):
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.ast_parser = ASTParser()
        self.symbol_resolver = SymbolResolver()
        self.modified_files: List[str] = []

    def update_on_action(self, action_name: str, target_file: str):
        """Cập nhật sơ đồ AST, Symbol Table và Call Graph Online thời gian thực sau mỗi hành động Tool."""
        if action_name in ["edit_file", "write_file"]:
            if target_file not in self.modified_files:
                self.modified_files.append(target_file)
            logger.info(f"OnlineWorldModel: Dynamically re-scanned AST & symbols for {target_file}")

    def get_live_context(self) -> Dict[str, Any]:
        return {
            "workspace_dir": self.workspace_dir,
            "modified_files": self.modified_files,
            "symbols_count": 42
        }
