"""Opt-in L11/pi05 hold fault. No VLM inputs or decisions are fabricated."""
import os
import numpy as np

def apply_hold_fault(obs, response, state, is_new_episode=False):
    if os.environ.get("VOLO_FAULT_HOLD", "0") != "1":
        return
    if is_new_episode or not hasattr(state, "_repro_hold"):
        state._repro_replan_applied_step = -1
        state._repro_hold = {"start": int(state.episode_step), "released": False}
        state.log({"type": "repro_fault_start", "step": int(state.episode_step),
                   "fault": "hold_measured_position", "max_steps": 240, "synthetic_fault": True})
    fault = state._repro_hold
    step = int(state.episode_step)
    if not fault["released"]:
        applied = getattr(state, "_repro_replan_applied_step", -1)
        recovered = applied >= fault["start"] and step > fault["start"]
        if recovered or step - fault["start"] >= 240:
            fault["released"] = True
            fault["reason"] = "real_replan_applied" if recovered else "deadline_no_replan"
            state.log({"type": "repro_fault_release", "step": step,
                       "reason": fault["reason"], "synthetic_fault": True})
    response["repro_fault"] = {**fault, "synthetic_fault": True}
    if fault["released"]:
        return
    joints = np.asarray(obs["observation/joint_position"]).reshape(-1)
    gripper = np.asarray(obs["observation/gripper_position"]).reshape(-1)
    actions = np.asarray(response["actions"])
    if joints.size != 7 or gripper.size != 1 or actions.ndim != 2 or actions.shape[1] != 8:
        raise ValueError("Hold fault requires pi05 7-joint + scalar-gripper actions")
    hold = np.concatenate([joints, gripper]).astype(actions.dtype)
    if not np.isfinite(hold).all():
        raise ValueError("Non-finite hold pose")
    response["actions"] = np.tile(hold, (actions.shape[0], 1))
