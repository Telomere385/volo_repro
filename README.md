# VoLo reproduction recovery snapshot

Goal: no training; pretrained pi05_droid_jointpos + remote VLM; RoboVoLo L11 SwapBinReplaceFruitsTask, with planning/execution/monitoring/replanning.

**Status: model/proxy inference and 71 unit tests passed; real simulator loop has NOT passed.** Isaac Sim 5.1 crashes in the NVIDIA 595.71.05 shader compiler on the source RTX 5090. User selected migration to an RTX host running Linux driver 580.65.06, retaining official RoboLab. No destination has been provisioned or validated.

Read HANDOFF.md first. Exact source commits are in manifests/repos.json. Local tracked changes are in manifests/*-tracked.patch; new source files and the RoboLab lockfile are in overlays/. Scripts, simulator diagnostics and supervisor configuration are preserved.

## Restore

1. Clone this backup to /root/volo-repro (scripts expect that absolute path).
2. Run `python3 restore_sources.py`. It downloads pinned upstream source repositories, applies patches and overlays, then initializes openpi submodules. Requires git and network; it intentionally refuses an existing repos directory. Git LFS files are downloaded separately.
3. Install git-lfs, conda and uv. Pull Git LFS objects in RoboLab and RoboVoLo. Recreate Python 3.11 environments as described in HANDOFF.md; install RoboLab with the isaac51 extra, openpi with its frozen lock, and the orchestration package. The RoboLab uv.lock is preserved in overlays.
4. Run the official RoboVoLo install.py into RoboLab and SimReady download/patch procedure described in HANDOFF.md. Previously missing avocado is unrelated to L11.
5. Re-download gs://openpi-assets-simeval/pi05_droid_jointpos into cache/openpi/openpi-assets-simeval/pi05_droid_jointpos; obtain the tokenizer using openpi. The integrity record is in results/.
6. Verify the actual host driver and RTX rendering. Run L11 smoke with VOLO_SIM_COMPAT=none before starting model services. Keep experimental Vulkan layers disabled on the new host.
7. Supply VLM credentials separately in config.env, chmod 600. Run baseline, normal and controlled-fault experiments as described in HANDOFF.md.

This backup excludes ~27 GB of Python environments, ~12 GB of model cache, upstream repository contents and large simulation assets. It preserves local code changes and recovery instructions, not an offline runnable installation. Credentials are excluded. If avoiding downloads matters, separately transfer cache/ and repos/ to durable storage before destroying the source.

Upstream software and copied code retain their original licenses; this snapshot does not replace those licenses. Prefer a private GitHub repository for this operational backup.
