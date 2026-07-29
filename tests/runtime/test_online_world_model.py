import pytest
from backend.runtime.online_world_model import OnlineWorldModel


def test_online_world_model_updates(tmp_path):
    model = OnlineWorldModel(workspace_dir=str(tmp_path))
    model.update_on_action("edit_file", "auth.py")

    ctx = model.get_live_context()
    assert "auth.py" in ctx["modified_files"]
    assert ctx["workspace_dir"] == str(tmp_path)
