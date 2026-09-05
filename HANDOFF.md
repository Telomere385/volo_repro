# VoLo reproduction handoff — 2026-09-05

## Status
NOT complete: no RoboVoLo episode has run successfully, and no real VLM loop has run.
Working: installed environments, checkpoint restore, real pi05 inference through the proxy, 71 selected orchestrator tests.
Blocking: Isaac Sim 5.1 RTX shader compilation crashes inside libnvidia-gpucomp.so.595.71.05.
This is independent of the task: it happens during SimulationApp initialization.
Remote VLM URL/model/key are still required. Never put keys in a chat or this file.

## Agreed scope
No training or fine-tuning. Remote vision API + pretrained pi05_droid_jointpos.
RoboVoLo L11 SwapBinReplaceFruitsTask: banana out of container onto table, then apple into container.
subgoal + failure-monitor=vlm + recovery-mode=replan, front camera, check interval 80 sim steps.
Single environment. Baseline 1 episode; normal 3; separately labelled injected fault 1.
Fault: hold measured joints and gripper, release on real applied replan or after 240 simulator steps.
A timeout is NOT evidence of successful recovery.
Final success must verify BOTH subtasks in order. The task's global success only checks apple in container and detached gripper.

## Paths and installed runtime
Root /root/volo-repro
repos/{VoLoAgent,RoboLab,RoboVoLo,openpi}
RoboLab tag v0.3.0 (f72d39445ab699c9cfd9bf551e8d21b6075293b9).
openpi is xuningy/openpi, NOT plain upstream Physical-Intelligence/openpi.
Conda prefixes envs/{vlm-orch,openpi,robolab}; all Python 3.11.
Actual RoboLab stack: Isaac Sim 5.1.0, Isaac Lab 2.3.2.post1.
Isaac50 (5.0 + Lab 2.2.0) was tried first and crashed; former freeze is in logs/robolab-isaac50-freeze.txt.
Use envs/.../bin/python or conda activate /root/volo-repro/envs/<name>.
Do not combine the three dependency sets, or run uv sync blindly (it removes manually installed openpi-client from RoboLab).

Checkpoint:
cache/openpi/openpi-assets-simeval/pi05_droid_jointpos
Origin gs://openpi-assets-simeval/pi05_droid_jointpos
26 objects, 12,435,136,033 bytes, checked against public object sizes (not cryptographic hashes).
See results/checkpoint-integrity.json.
Tokenizer also cached under cache/openpi/big_vision.

RoboVoLo pack installed: 126 tasks, 123 scenes, three custom asset families.
RoboLab and RoboVoLo git-lfs pulls completed.
33/34 SimReady asset families downloaded/patched. Avocado is missing from NVIDIA's public workspace index.
L11 does NOT use avocado. Full-pack completeness is NOT claimed.
results/l11-assets.json was produced by plain USD bindings: unresolved MDLs include
Isaac Sim builtins (OmniPBR/gltf) and remote materials. This is not a completed renderer asset check.

## Current machine
RTX 5090 32GB, driver 595.71.05, Ubuntu 24.04 container.
No host volume. Stop/start preserves files; recycle/destroy loses them.
Driver is host-managed: do NOT install/replace NVIDIA drivers inside this container.
Last disk check: approximately 78 GiB free.

## What is implemented
scripts/common.sh: project paths and optional config.env/active.env.
scripts/serve_pi05.sh and serve_orch.sh: supervisor wrappers.
scripts/health.py: WebSocket metadata and optional real dummy-image pi05 inference.
scripts/check_vlm.py: real image API smoke request and JSON parsing, not yet run.
scripts/run_experiment.sh: baseline|normal|fault, unique run IDs and an experiment lock.
scripts/smoke_l11.py: correct VoLo task/depth-camera registration; writes camera PNGs/result.json on success.
smoke_l11.py has not reached task initialization because SimulationApp crashes first.
config.env.example: URL/model/key template; copy to config.env and chmod 600, do not commit key.
active.env: current proxy experiment settings.

Source modifications (uncommitted; preserve them):
VoLoAgent/vlm_orchestrator/repro_fault.py (new): opt-in VOLO_FAULT_HOLD=1 injection.
VoLoAgent/tests/test_repro_fault.py (new): five tests.
VoLoAgent/vlm_orchestrator/proxy.py: invoke injection before action send/trajectory logging.
VoLoAgent/vlm_orchestrator/strategies/subgoal_base.py: log repro_replan_applied after successful real replan.
openpi/scripts/serve_policy.py: configurable --host, used as 127.0.0.1 in wrapper.
A replan may select the same original subgoal text; verify applied replan + flushed actions + resumed physical progress, not just text inequality.

Supervisor configuration: /etc/supervisor/conf.d/volo-repro.conf
Names: volo_pi05 (127.0.0.1:8000), volo_orch (127.0.0.1:8001).
autostart=false; autorestart=unexpected; process groups stopped together.
Portal service logs: /var/log/portal/volo_pi05.log and volo_orch.log.
No public port was opened.
At this checkpoint pi05 was stopped for isolation and remains stopped; check status before resuming.
The proxy may be running without its VLA backend; check status. These stops do not halt Vast GPU billing.

## Diagnostic findings — do not repeat blindly
1. Torch CUDA and JAX GPU compilation passed on 5090.
2. Real pi05 checkpoint restored and returned finite (15,8) actions through port 8001.
   First JIT request ~31 sec; logs/pi05-proxy-inference.log.
3. 71 selected tests passed; logs/test-orchestrator.log.
4. Native Isaac Sim 5.0/5.1 crash in librtx.scenedb.plugin.so.
   Vulkan maintenance3 maxMemoryAllocationSize reports UINT64_MAX (0xffffffffffffffff).
5. Built Khronos Vulkan-Profiles from SDK tag vulkan-sdk-1.4.341.0,
   commit a400d0b10059b2cc3cd285475593eee79975a5c4.
   Generic profile caps allocation at 4GiB-2MiB, but ALSO changes UUID and some other properties.
   Retained as an experimental diagnostic, NOT a proven working launch configuration.
6. Added compat/allocation_limit.cpp and built libVkLayer_volo_allocation_limit.so.
   It uses the Vulkan loader chain and changes ONLY NVIDIA's UINT64_MAX allocation cap to 4292870144.
   Verified full vulkaninfo diff: only target cap, layer listing and dynamic memory usage differ.
   It preserves UUIDs, extension set and non-NVIDIA properties.
   Build: g++ -std=c++17 -shared -fPIC -O2 -Wl,-Bsymbolic -o compat/libVkLayer_volo_allocation_limit.so compat/allocation_limit.cpp -pthread
   Enable only for simulator: source scripts/sim_env_narrow.sh.
7. Both allocation workarounds get past the scenedb failure but expose shader compiler SIGILL.
   gdb confirmed actual instruction ud2 in libnvidia-gpucomp.so.595.71.05.
   No evidence of fiber stack overflow; do not keep guessing stack-size settings.
8. Stopping pi05 (freeing all GPU memory), disabling NGX and setting renderer.asyncInit=false
   still produces the same compiler crash.
   This does NOT prove the exact internal driver defect, but rules out pi05 residency as required trigger.
   No driver, firmware, kernel or cgroup modifications were made.

Key logs:
logs/sim-gdb.log — SIGILL / ud2 diagnosis
logs/vulkan-native.txt, vulkan-profile.txt, vulkan-narrow.txt — property evidence
logs/sim51-narrow-smoke.log — narrow layer still crashes
logs/sim51-isolated-no-ngx.log — isolated GPU + NGX off still crashes
logs/sim-smoke.log, sim51-smoke.log — native 5.0 and 5.1 failures
logs/sim51-compat-l11-smoke-v2.log — generic profile shader crash
logs/vulkan-build.log — Khronos build
logs/simready-assets.log, simready-patches.log — incomplete avocado asset set
No successful result exists under results/l11-smoke yet.

## Next decision
Prefer a compatible RTX instance with a Linux driver validated for Isaac Sim 5.1
(e.g. 580.65.06, subject to actual hardware requirements), preserving RoboLab's supported simulator combination.
Alternative: explicitly choose an ISOLATED Isaac Sim 6.x environment; do not overwrite working VLA/orchestrator environments.
That alternative requires checking Python/IsaacLab/RoboLab compatibility and changes the simulator baseline.
Do not silently claim the original benchmark reproduction if migrating versions.

References:
https://github.com/NVlabs/RoboLab/blob/v0.3.0/policies/pi0_family/README.md
https://github.com/isaac-sim/IsaacSim/issues/568#issuecomment-4415180467
https://forums.developer.nvidia.com/t/isaacsim-crash-when-update-gpu-driver/371975/2
https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html

## Resume sequence
1. Read this file, inspect manifests and supervisorctl status volo_pi05 volo_orch.
2. Resolve machine/runtime decision; do not repeat already-failed compiler workarounds.
3. Run scripts/smoke_l11.py in the robolab environment from repos/RoboLab with --headless.
   Require real camera PNGs, depth outputs and completed physics steps.
   Normal run_empty.py does not by default register the robovolo content pack.
4. Restart pi05, validate scripts/health.py --port 8000 --infer, then run_experiment.sh baseline.
5. Configure remote VLM in config.env; send a scene PNG through check_vlm.py.
6. Run normal and fault experiments. Require both ordered subtasks for normal success,
   and real monitor -> applied replan -> resumed motion/progress for recovery.
7. Add final event/video/result audit and report honestly. Existing tests use mocks and are not real VLM-loop evidence.


## Latest decision / destruction backup
User selected migration to RTX with Linux driver 580.65.06 and official Isaac Sim 5.1. No transfer has occurred. This GitHub backup excludes secrets, environments, large assets and weights; see README.md.
