import os
import pytest
from backend.events.event import Action, Observation
from backend.events.stream import EventStream
from backend.events.storage import TrajectoryStorage
from backend.events.replay import ActionReplay


def test_event_models():
    # 1. Test Action
    action = Action(
        action_name="open_file",
        inputs={"path": "main.py", "start_line": 10}
    )
    assert action.event_type == "action"
    assert action.action_name == "open_file"
    assert action.inputs["path"] == "main.py"

    # 2. Test Observation
    observation = Observation(
        observation_name="file_content",
        outputs={"content": "def run(): pass"}
    )
    assert observation.event_type == "observation"
    assert observation.observation_name == "file_content"
    assert observation.outputs["content"] == "def run(): pass"


def test_event_stream():
    stream = EventStream()
    
    # Thêm Action và Observation
    stream.add_event(Action(action_name="run_test", inputs={"target": "test_api.py"}))
    stream.add_event(Observation(observation_name="test_output", outputs={"exit_code": 0}))

    events = stream.get_events()
    assert len(events) == 2
    assert events[0].event_type == "action"
    assert events[1].event_type == "observation"

    # Test serialization / deserialization
    dict_list = stream.to_dict_list()
    assert len(dict_list) == 2
    assert dict_list[0]["action_name"] == "run_test"

    new_stream = EventStream()
    new_stream.load_from_dict_list(dict_list)
    assert len(new_stream.get_events()) == 2
    assert new_stream.get_events()[0].action_name == "run_test"


def test_trajectory_storage(tmp_path):
    storage = TrajectoryStorage(str(tmp_path))
    stream = EventStream()
    
    stream.add_event(Action(action_name="edit_file", inputs={"path": "app.py"}))
    stream.add_event(Observation(observation_name="edit_status", outputs={"success": True}))

    # Lưu trajectory
    task_id = "task-999"
    saved_path = storage.save_trajectory(task_id, stream)
    assert os.path.exists(saved_path)

    # Nạp lại trajectory vào stream mới
    loaded_stream = EventStream()
    success = storage.load_trajectory(task_id, loaded_stream)
    assert success is True
    
    loaded_events = loaded_stream.get_events()
    assert len(loaded_events) == 2
    assert loaded_events[0].action_name == "edit_file"
    assert loaded_events[1].outputs["success"] is True


def test_action_replay():
    stream = EventStream()
    stream.add_event(Action(action_name="open_file", inputs={"path": "auth.py"}))
    stream.add_event(Observation(observation_name="file_content", outputs={"lines": 10}))
    stream.add_event(Action(action_name="open_file", inputs={"path": "main.py"}))

    # 1. Timeline
    timeline = ActionReplay.print_timeline(stream)
    assert "ACTION: open_file" in timeline
    assert "OBSERVATION: file_content" in timeline

    # 2. Stats Summary
    stats = ActionReplay.get_summary_stats(stream)
    assert stats["total_events"] == 3
    assert stats["total_actions"] == 2
    assert stats["total_observations"] == 1
    assert stats["tool_calls"]["open_file"] == 2
