import pytest
from backend.runtime.session import InteractiveSession
from backend.runtime.git_session import GitSession


def test_session_persistence(tmp_path):
    session = InteractiveSession(workspace_dir=str(tmp_path))
    session.start_task("Fix token timeout", target_file="auth.py")

    save_path = session.save_session(storage_dir=str(tmp_path))
    assert save_path.endswith(".json")

    loaded_session = InteractiveSession.load_session(save_path)
    assert loaded_session.session_id == session.session_id
    assert loaded_session.state == session.state


def test_git_worktree_session(tmp_path):
    git_session = GitSession(workspace_dir=str(tmp_path))
    worktree_path = git_session.create_worktree("TASK-TEST")

    assert worktree_path is not None
    removed = git_session.remove_worktree("TASK-TEST")
    assert isinstance(removed, bool)
