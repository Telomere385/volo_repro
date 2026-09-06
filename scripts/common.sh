#!/bin/bash
set -euo pipefail
export VOLO_ROOT=/workspace/volo_repro
export OPENPI_DATA_HOME="$VOLO_ROOT/cache/openpi"
export HF_HOME="$VOLO_ROOT/cache/huggingface"
export OMNI_KIT_ACCEPT_EULA=Y
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=8
set -a
[[ ! -f "$VOLO_ROOT/config.env" ]] || source "$VOLO_ROOT/config.env"
[[ ! -f "$VOLO_ROOT/active.env" ]] || source "$VOLO_ROOT/active.env"
set +a
