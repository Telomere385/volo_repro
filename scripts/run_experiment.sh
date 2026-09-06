#!/bin/bash
set -euo pipefail
source /workspace/volo_repro/scripts/common.sh
kind="${1:-baseline}"
case "$kind" in
  baseline) mode=passthrough; fault=0; runs=1 ;;
  normal) mode=subgoal; fault=0; runs=1 ;;
  *) echo "Usage: $0 baseline|normal (fault injection is not installed)" >&2; exit 2 ;;
esac
if [[ "$mode" == subgoal ]]; then
  : "${VLM_BASE_URL:?Set config.env first}"
  : "${VLM_MODEL:?Set config.env first}"
  : "${VLM_API_KEY:?Set config.env first}"
fi
exec 9>"$VOLO_ROOT/.experiment.lock"
flock -n 9 || { echo "Another experiment is running" >&2; exit 1; }
run_id="l11_${kind}_$(date -u +%Y%m%dT%H%M%SZ)"
printf 'VOLO_MODE=%q\nVOLO_FAULT_HOLD=%q\nVOLO_RUN_ID=%q\n' "$mode" "$fault" "$run_id" > "$VOLO_ROOT/active.env"
supervisorctl start volo_pi05 || supervisorctl status volo_pi05
supervisorctl restart volo_orch
timeout 600 "/workspace/envs/openpi/bin/python" "$VOLO_ROOT/scripts/health.py" --port 8001
source "$VOLO_ROOT/scripts/sim_env.sh"
cd "/workspace/RoboLab"
timeout 3600 "/workspace/envs/robolab/bin/python" -u policies/volo/run.py \
  --policy pi05 --remote-host 127.0.0.1 --remote-port 8001 \
  --task SwapBinReplaceFruitsTask --num-envs 1 --num-runs "$runs" \
  --enable-subtask --video-mode all --headless --output-folder-name "$run_id" \
  > "$VOLO_ROOT/logs/${run_id}.log" 2>&1
echo "Run finished: $run_id"
echo "RoboLab results: /workspace/RoboLab/output/$run_id"
