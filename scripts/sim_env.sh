#!/bin/bash
# Neither workaround is known to make this R595 machine run Isaac Sim successfully.
case "${VOLO_SIM_COMPAT:-none}" in
  none) ;;
  narrow) source /root/volo-repro/scripts/sim_env_narrow.sh ;;
  profiles) source /root/volo-repro/scripts/sim_env_profiles.sh ;;
  *) echo "VOLO_SIM_COMPAT must be none|narrow|profiles" >&2; return 2 ;;
esac
