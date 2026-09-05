from types import SimpleNamespace
import numpy as np
import pytest
from vlm_orchestrator.repro_fault import apply_hold_fault

def make():
    events = []
    state = SimpleNamespace(episode_step=0, log=events.append)
    obs = {"observation/joint_position": np.arange(7),
           "observation/gripper_position": np.array([0.3])}
    response = {"actions": np.ones((15, 8)), "orchestrator_instruction": "pick banana"}
    return obs, response, state, events

def test_disabled(monkeypatch):
    monkeypatch.delenv("VOLO_FAULT_HOLD", raising=False)
    obs, response, state, events = make()
    original = response["actions"]
    apply_hold_fault(obs, response, state, True)
    assert response["actions"] is original and not events

def test_real_replan(monkeypatch):
    monkeypatch.setenv("VOLO_FAULT_HOLD", "1")
    obs, response, state, events = make()
    apply_hold_fault(obs, response, state, True)
    np.testing.assert_allclose(response["actions"][0], [0,1,2,3,4,5,6,.3])
    assert response["orchestrator_instruction"] == "pick banana"
    state.episode_step = 80
    state._repro_replan_applied_step = 80
    response = {"actions": np.full((15,8), 2.), "orchestrator_flush_actions": True}
    apply_hold_fault(obs, response, state)
    assert np.all(response["actions"] == 2) and response["orchestrator_flush_actions"]
    assert events[-1]["reason"] == "real_replan_applied"

def test_deadline(monkeypatch):
    monkeypatch.setenv("VOLO_FAULT_HOLD", "1")
    obs, response, state, events = make()
    apply_hold_fault(obs, response, state, True)
    state.episode_step = 240
    response["actions"] = np.ones((15,8))
    apply_hold_fault(obs, response, state)
    assert events[-1]["reason"] == "deadline_no_replan"
    assert np.all(response["actions"] == 1)

def test_bad_schema(monkeypatch):
    monkeypatch.setenv("VOLO_FAULT_HOLD", "1")
    obs, response, state, _ = make()
    response["actions"] = np.zeros((8,7))
    with pytest.raises(ValueError):
        apply_hold_fault(obs, response, state, True)

def test_episode_reset(monkeypatch):
    monkeypatch.setenv("VOLO_FAULT_HOLD", "1")
    obs, response, state, _ = make()
    state._repro_replan_applied_step = 80
    apply_hold_fault(obs, response, state, True)
    state.episode_step = 8
    apply_hold_fault(obs, response, state)
    assert not state._repro_hold["released"]
