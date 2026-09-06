#!/bin/bash
source /opt/supervisor-scripts/utils/logging.sh
source /opt/supervisor-scripts/utils/environment.sh
source /workspace/volo_repro/scripts/common.sh
export XLA_PYTHON_CLIENT_MEM_FRACTION=0.4
cd "/workspace/openpi"
pty "/workspace/envs/openpi/bin/python" -u scripts/serve_policy.py --host 127.0.0.1 --port 8000 policy:checkpoint --policy.config=pi05_droid_jointpos --policy.dir="$OPENPI_DATA_HOME/openpi-assets-simeval/pi05_droid_jointpos" 2>&1
