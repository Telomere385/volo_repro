#!/bin/bash
# Scope this layer to the simulator only. It does not replace any driver library.
export VOLO_VULKAN_COMPAT=1
export VK_ADD_IMPLICIT_LAYER_PATH=/root/volo-repro/compat/implicit_layer.d
export VK_KHRONOS_PROFILES_PROFILE_DIRS=/root/volo-repro/compat/profiles
export VK_KHRONOS_PROFILES_PROFILE_NAME=VP_VOLO_driver_compat
export VK_KHRONOS_PROFILES_SIMULATE_CAPABILITIES=SIMULATE_PROPERTIES_BIT
export VK_KHRONOS_PROFILES_DEBUG_REPORTS=DEBUG_REPORT_ERROR_BIT
export XDG_DATA_DIRS="/root/volo-repro/compat/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
