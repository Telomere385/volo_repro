"""Finite L11 smoke test using the same depth-camera registration as VoLo."""
import argparse, json, sys
from pathlib import Path
import cv2
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser()
p.add_argument("--steps",type=int,default=8)
AppLauncher.add_app_launcher_args(p)
args,_=p.parse_known_args()
args.enable_cameras=True
app=AppLauncher(args).app
from policies.volo.registration import register_volo_envs
from robolab.core.environments.factory import get_envs
from robolab.core.environments.runtime import create_env
import torch
root=Path("/root/volo-repro/results/l11-smoke")
root.mkdir(parents=True,exist_ok=True)
env=None
try:
    register_volo_envs(task=["SwapBinReplaceFruitsTask"])
    names=get_envs(task="SwapBinReplaceFruitsTask")
    assert names, "L11 not registered"
    env,cfg=create_env(names[0],num_envs=1,seed=0,use_fabric=True)
    obs,_=env.reset()
    actions=torch.zeros((1,env.action_manager.total_action_dim),device=env.device)
    for _ in range(args.steps):
        obs,*_=env.step(actions)
    report={"task":"SwapBinReplaceFruitsTask","env":names[0],"seed":0,
            "steps":args.steps,"action_dim":env.action_manager.total_action_dim,"cameras":{}}
    for name,sensor in env.scene.sensors.items():
        output=getattr(sensor.data,"output",{})
        if "rgb" not in output: continue
        rgb=output["rgb"][0,:,:,:3].detach().cpu().numpy()
        assert rgb.size and rgb.std()>0, f"Empty/constant RGB: {name}"
        cv2.imwrite(str(root/(name+".png")),cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR))
        report["cameras"][name]={"shape":list(rgb.shape),"std":float(rgb.std()),
                                 "output_keys":list(output)}
    assert report["cameras"],"No RGB cameras"
    (root/"result.json").write_text(json.dumps(report,indent=2))
    print("L11_SMOKE_OK",json.dumps(report),flush=True)
finally:
    if env is not None: env.close()
    app.close()
