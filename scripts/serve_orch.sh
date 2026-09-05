#!/bin/bash
source /opt/supervisor-scripts/utils/logging.sh
source /opt/supervisor-scripts/utils/environment.sh
source /root/volo-repro/scripts/common.sh
cd "$VOLO_ROOT/repos/VoLoAgent"
args=(--host 127.0.0.1 --vla-host 127.0.0.1 --vla-port 8000 --port 8001
      --mode "${VOLO_MODE:-passthrough}" --log-dir "$VOLO_ROOT/results/${VOLO_RUN_ID:-baseline}" --verbose)
if [[ "${VOLO_MODE:-passthrough}" == subgoal ]]; then
  : "${VLM_BASE_URL:?Set VLM_BASE_URL in config.env}"
  : "${VLM_MODEL:?Set VLM_MODEL in config.env}"
  : "${VLM_API_KEY:?Set VLM_API_KEY in config.env}"
  args+=(--failure-monitor vlm --recovery-mode replan --use-front-camera --check-interval 80
         --vlm-base-url "$VLM_BASE_URL" --vlm-model "$VLM_MODEL")
fi
pty "$VOLO_ROOT/envs/vlm-orch/bin/vlm-orchestrator" "${args[@]}" 2>&1
