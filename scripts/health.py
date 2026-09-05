import argparse, time
import numpy as np
from openpi_client.websocket_client_policy import WebsocketClientPolicy
p=argparse.ArgumentParser()
p.add_argument("--port",type=int,default=8000)
p.add_argument("--infer",action="store_true")
a=p.parse_args()
policy=WebsocketClientPolicy(host="127.0.0.1",port=a.port)
print("METADATA",policy.get_server_metadata(),flush=True)
if a.infer:
    obs={"observation/exterior_image_1_left":np.zeros((224,224,3),dtype=np.uint8),
         "observation/wrist_image_left":np.zeros((224,224,3),dtype=np.uint8),
         "observation/joint_position":np.array([0.,-.5,0.,-2.,0.,1.5,0.]),
         "observation/gripper_position":np.array([0.]),
         "prompt":"Pick up the banana."}
    t=time.monotonic()
    result=policy.infer(obs)
    actions=np.asarray(result["actions"])
    assert actions.ndim==2 and actions.shape[1]==8 and np.isfinite(actions).all()
    print("INFERENCE",actions.shape,"seconds",round(time.monotonic()-t,3),
          "range",float(actions.min()),float(actions.max()),flush=True)
