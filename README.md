# VoLo 复现：pretrained π0.5 + VLM + RoboVoLo

不训练、不微调模型，目标是在 RoboVoLo **L11 `SwapBinReplaceFruitsTask`** 中完成：先将香蕉从容器移到桌面，再将苹果放进容器。本轮以真实评测输出 **`success=true`** 为成功标准。

**截至 2026-09-06：pretrained π0.5 + 远程 VLM 的 L11 完整任务已成功，`success=true`、score=1.0。** baseline 失败，normal 成功；本次验证了目标分解、执行与 VLM 进度监控，未触发重规划，不据此宣称故障恢复已验证。

本仓库保存复现说明、补丁、脚本和选定结果，**不是离线可运行的完整安装包**。四个上游仓库、Python 环境和大型资产分布在 `/workspace` 下。持续执行记录见 [codex.md](codex.md)。[HANDOFF.md](HANDOFF.md) 是旧 RTX 5090 机器的历史交接，不能用其中的状态和路径覆盖本页的新配置。

## 当前结果

### L11 场景与相机

下图是 **smoke 的初始场景**，不是任务成功后的画面：香蕉在容器里，苹果在桌面。

![L11 初始场景：容器内的香蕉与桌上的苹果](results/l11-smoke/egocentric_mirrored_camera.png)

原生 Isaac Sim 5.1 完成了 8 个物理步，退出码 0；三个相机均输出非空、非恒定 RGB。前视和侧视输出含 depth，smoke 未保存深度数值文件。

| 相机 | RGB 分辨率（宽 × 高） | 输出 |
|---|---|---|
| 前视 `egocentric_mirrored_camera` | 864 × 480 | RGB + depth |
| 侧视 `over_shoulder_left_camera` | 1280 × 720 | RGB + depth |
| 腕部 `wrist_cam` | 1280 × 720 | RGB |

结果文件：[smoke JSON](results/l11-smoke/result.json)、[侧视图片](results/l11-smoke/over_shoulder_left_camera.png)、[腕部图片](results/l11-smoke/wrist_cam.png)、[smoke 日志](logs/current/l11-smoke.log)。VLM 使用前视图，π0.5 仍使用其训练对应的侧视和腕部图。

### 模型与 baseline

| 检查 | 实测结果 |
|---|---|
| checkpoint | 26 个对象，12,435,136,033 bytes；与公开 GCS 对象大小一致，未做密码学哈希校验 |
| π0.5 真实推理 | 有限数值的 `(15, 8)` 动作；首次 JIT 请求 18.091s |
| 显存 | 模型约 10GB；模型与单环境仿真同时运行约 15GB（观测值，非峰值保证） |
| baseline | `l11_baseline_20260906T100957Z`；seed 0；1 episode；passthrough |
| 任务结果 | **`success=false`，score=0.5** |
| 运行长度 | 900 步，60s 仿真时间；动作循环墙钟 145.452s |
| 未完成原因 | `object_grabbed(object=apple_01)` 条件未满足 |
| VLM | 图片检查通过；normal episode 成功，见下文 |

baseline 验证了“仿真观测 → 代理 → π0.5 → 仿真动作 → 结果/视频”的链路，**不代表任务成功或 VoLo 效果已复现**。这里只运行了一个 baseline episode。

数据入口：

- [baseline 原始评测 JSONL 副本](results/l11_baseline_20260906T100957Z/episode_results.jsonl)
- [checkpoint 核验](results/checkpoint-integrity-current.json)
- [π0.5 推理日志](logs/current/pi05-inference.log)
- [baseline 仿真日志](logs/l11_baseline_20260906T100957Z.log)
- [代理事件与 metadata](results/l11_baseline_20260906T100957Z/)

完整视频、逐步状态和环境配置留在仓库外：

```text
/workspace/RoboLab/output/l11_baseline_20260906T100957Z/
├── episode_results.jsonl
└── SwapBinReplaceFruitsTask/
    ├── env_cfg.json
    ├── log_0_env0.json
    ├── <instruction>_0.mp4
    └── <instruction>_0_viewport.mp4
```

实际结果是实验根目录的 `episode_results.jsonl`，不是上游 README 示例中的任务目录 `episode_results.json`。大视频未复制进本备份仓库，迁移时需另行传输上述目录。

### VLM normal 成功结果

运行 `l11_normal_20260906T112758Z`，seed=0，1 episode；策略为 subgoal + VLM monitor + replan（允许重规划，但本次未触发）。

| 指标 | 结果 |
|---|---|
| success / score | **true / 1.0** |
| 仿真步数 / 时间 | 853 / 56.867s |
| 动作循环墙钟 | 165.404s |
| 最终原因 | `Completed subtask 'pick_and_place' 2/2` |
| 代理推理请求数 | 57 |
| VLM 记录 | 1 次分解 + 5 次进度检查；3 次 next，2 次 continue |

VLM 分解为：拿起容器中的香蕉 → 放到桌上 → 拿起桌上的苹果 → 放入容器。任务由仿真成功条件结束，最后一次 VLM 检查并非最终成功判据。本次没有 replan 事件，不是故障恢复实验。baseline 与 normal 各仅 1 次，不代表统计成功率。

- [normal 原始评测结果](results/l11_normal_20260906T112758Z/episode_results.jsonl)
- [normal 代理事件与 metadata](results/l11_normal_20260906T112758Z/)
- [normal 仿真日志](logs/l11_normal_20260906T112758Z.log)
- 完整视频与逐步日志：`/workspace/RoboLab/output/l11_normal_20260906T112758Z/SwapBinReplaceFruitsTask/`（仓库外）。

## 已验证机器与环境划分

本次机器：Ubuntu 24.04 x86_64 容器，RTX 4090 24GB，宿主驱动 **580.173.02**，GL/OptiX/Vulkan 可用。使用 **Isaac Sim 5.1.0 + Isaac Lab 2.3.2.post1**，未启用旧 Vulkan 兼容层。该组合在本机通过 smoke；其他主机仍需先验证。

三个环境均为 **uv venv / Python 3.11.15**，没有使用旧备份中的 conda prefixes，也不向实例的 `(main)` 环境安装项目依赖。

| 环境路径 | 安装内容 | 用途 |
|---|---|---|
| `/workspace/envs/robolab` | RoboLab、Isaac Sim/Lab、`openpi-client` | 仿真、观测、动作执行、评测 |
| `/workspace/envs/openpi` | xuningy/openpi，使用其 uv.lock | π0.5 服务，127.0.0.1:8000 |
| `/workspace/envs/vlm-orch` | VoLoAgent、`usd-core` 工具依赖 | VLM 代理，127.0.0.1:8001；资产下载/补丁工具 |

```text
RoboLab + RoboVoLo ── WebSocket ──> VoLoAgent :8001 ──> openpi π0.5 :8000
                                      │
                                      └── HTTPS ──> 远程视觉 VLM
```

RoboVoLo 是内容包，不需要第四个运行环境。本轮使用 `subgoal + failure-monitor=vlm + recovery-mode=replan`，不部署 GraspGen、SAM 或本地 VLM，也不需要训练数据集。

## 源码、资产和目录配置

| 仓库 | 来源 | 固定版本 |
|---|---|---|
| `/workspace/openpi` | [xuningy/openpi](https://github.com/xuningy/openpi) | `aa6420561529593114160d05e5ad155792b272f3` |
| `/workspace/RoboLab` | [NVlabs/RoboLab](https://github.com/NVlabs/RoboLab) | v0.3.0 / `f72d39445ab699c9cfd9bf551e8d21b6075293b9` |
| `/workspace/RoboVoLo` | [NVlabs/RoboVoLo](https://github.com/NVlabs/RoboVoLo) | `69b53943ee9213720ee68dcbdea285b2c1289982` |
| `/workspace/VoLoAgent` | [NVlabs/VoLoAgent](https://github.com/NVlabs/VoLoAgent) | `b4e623079ca8498a16bcd5016920d71f76c44d30` |

**不要用 Physical-Intelligence/openpi 替代上述 fork**：这条 RoboLab 路径需要 `pi05_droid_jointpos` 配置。不要直接跟随 RoboLab main；本轮按 VoLoAgent README 固定 v0.3.0。

```text
/workspace/
├── volo_repro/                     # 本备份仓库
│   ├── README.md / codex.md        # 复现入口 / 执行记录
│   ├── scripts/                   # smoke、启动、实验、核验
│   ├── supervisor/                # Vast supervisor 配置模板
│   ├── manifests/                 # 旧 commit、freeze、补丁
│   ├── overlays/RoboLab/uv.lock   # 本轮使用的 RoboLab 锁文件
│   ├── logs/current/              # 本机日志及实际依赖 freeze
│   ├── results/                   # 选定图像、JSON、代理事件
│   ├── config.env                 # 私有 VLM 配置，Git 忽略
│   ├── active.env                 # 当前实验设置，Git 忽略
│   └── cache/openpi/              # 权重/tokenizer，不进 Git
│       ├── openpi-assets-simeval/pi05_droid_jointpos/
│       └── big_vision/paligemma_tokenizer.model
├── envs/{robolab,openpi,vlm-orch}/ # 不在本仓库内
├── openpi/
├── VoLoAgent/
├── RoboVoLo/
└── RoboLab/
    ├── assets/                    # LFS 原有资产 + 内容包 + SimReady
    ├── robolab/tasks/robovolo/     # 内容包安装位置
    └── output/                    # 完整评测数据与视频
```

本次安装了 126 个任务、123 个场景、3 类自定义对象。SimReady 外部资源完成 **33/34** 类，`avocado` 在下载索引中缺失，因此不能声称全任务资产齐全。L11 直接引用 RoboLab 的 `vomp/container_b03`、`ycb/banana`、`objaverse/apple_01` 和桌面资产，不依赖 avocado。

本机目录占用约：robolab 环境 18GiB、openpi 环境 7.8GiB、vlm-orch 606MiB；RoboLab 12GiB、模型缓存 12GiB。`du` 数值可能包含共享/硬链接，不能简单相加作为磁盘用量。安装前本机约有 111GB 可用空间，下载/解包还需要临时空间。

## 新机器复现步骤

下面针对**新的 `/workspace` 布局**。已有目录时先检查版本和本地修改，不覆盖环境或重复应用补丁。需预先提供 git、git-lfs、uv、ffmpeg；GPU 驱动由宿主管理，不在容器里安装/替换驱动。依赖通过框架 wheels 携带运行库，不要求系统 CUDA toolkit 与 wheel 完全同版本。

### 1. 获取固定源码

```bash
cd /workspace
git clone https://github.com/Telomere385/volo_repro.git
git clone https://github.com/xuningy/openpi.git
git -C openpi switch --detach aa6420561529593114160d05e5ad155792b272f3
git -C openpi submodule update --init --recursive
git clone --branch v0.3.0 https://github.com/NVlabs/RoboLab.git
git clone https://github.com/NVlabs/RoboVoLo.git
git -C RoboVoLo switch --detach 69b53943ee9213720ee68dcbdea285b2c1289982
git clone https://github.com/NVlabs/VoLoAgent.git
git -C VoLoAgent switch --detach b4e623079ca8498a16bcd5016920d71f76c44d30
git -C RoboLab lfs pull
git -C RoboVoLo lfs pull
git -C openpi apply /workspace/volo_repro/manifests/openpi-tracked.patch
```

openpi 补丁仅增加可配置 `--host`，让服务绑定 localhost。本轮**没有应用** VoLoAgent 故障注入补丁和 `compat/` 下的 Vulkan 实验层。

### 2. 创建并安装三个环境

```bash
uv venv --python 3.11.15 /workspace/envs/robolab
uv venv --python 3.11.15 /workspace/envs/openpi
uv venv --python 3.11.15 /workspace/envs/vlm-orch

cp /workspace/volo_repro/overlays/RoboLab/uv.lock /workspace/RoboLab/uv.lock
cd /workspace/RoboLab
UV_PROJECT_ENVIRONMENT=/workspace/envs/robolab uv sync --frozen --extra isaac51
uv pip install --python /workspace/envs/robolab/bin/python -e /workspace/openpi/packages/openpi-client

cd /workspace/openpi
UV_PROJECT_ENVIRONMENT=/workspace/envs/openpi GIT_LFS_SKIP_SMUDGE=1 uv sync --frozen

uv pip install --python /workspace/envs/vlm-orch/bin/python -e /workspace/VoLoAgent usd-core
```

RoboLab 和 openpi 使用锁文件；VoLoAgent 及后装客户端/工具的传递依赖并未完全锁定，以上重建不是逐字节环境镜像。本次实际版本保存在 [robolab freeze](logs/current/robolab-freeze.txt)、[openpi freeze](logs/current/openpi-freeze.txt)、[vlm-orch freeze](logs/current/vlm-orch-freeze.txt)，供差异排查。不要向同一环境安装三个依赖集合。之后若再次 `uv sync` RoboLab，可能移除后装的 `openpi-client`，需重新安装。

### 3. 安装内容包和外部资源，先验证仿真

```bash
/workspace/envs/vlm-orch/bin/python /workspace/RoboVoLo/install.py /workspace/RoboLab
```

内容包安装器要求目标尚未安装，不应盲目重复执行。阅读 RoboVoLo 的外部资产许可说明后，下载并打补丁：

```bash
/workspace/envs/vlm-orch/bin/python /workspace/RoboVoLo/download_simready_assets.py --agree-external-terms /workspace/RoboLab
```

如果与本机一样仅 avocado 缺失，程序会在下载阶段返回非零、跳过后续补丁。确认日志后，为已下载的资源补做：

```bash
/workspace/envs/vlm-orch/bin/python /workspace/RoboVoLo/download_simready_assets.py --agree-external-terms /workspace/RoboLab --skip-download
```

即使 33 类补丁完成，仍会报告资产集不完整；不要忽略其他新增下载错误。然后运行 L11 smoke（`OMNI_KIT_ACCEPT_EULA=Y` 表示接受 Isaac Sim EULA）：

```bash
cd /workspace/RoboLab
OMNI_KIT_ACCEPT_EULA=Y PYTHONPATH=/workspace/RoboLab OMP_NUM_THREADS=8 \
  /workspace/envs/robolab/bin/python -u /workspace/volo_repro/scripts/smoke_l11.py --headless
```

以 `L11_SMOKE_OK`、进程正常退出、`results/l11-smoke/` 内真实图像为通过证据。新运行会覆盖该 smoke 目录，保留历史结果时先另存。首次 shader 编译较慢，本机首次 smoke 约 147s。部分日志警告不妨碍本次通过，不能仅凭出现 warning 判断失败。

### 4. 获取 pretrained π0.5

```bash
source /workspace/volo_repro/scripts/common.sh
/workspace/envs/openpi/bin/python -c 'from openpi.shared.download import maybe_download; print(maybe_download("gs://openpi-assets-simeval/pi05_droid_jointpos"))'
/workspace/envs/openpi/bin/python /workspace/volo_repro/scripts/verify_checkpoint.py
```

模型必须使用 **`pi05_droid_jointpos`**，不是通用 `pi05_base`。tokenizer 首次启动时自动下载；归一化统计从 checkpoint 的 `assets/droid` 加载。

### 5. 启动模型/代理并运行 baseline（Vast 实例）

现有 wrappers 依赖 Vast 的 `/opt/supervisor-scripts/utils/{logging,environment}.sh` 和 `pty`。在带相同基础镜像的新实例上：

```bash
cp /workspace/volo_repro/supervisor/volo-repro.conf /etc/supervisor/conf.d/volo-repro.conf
chmod +x /workspace/volo_repro/scripts/serve_pi05.sh /workspace/volo_repro/scripts/serve_orch.sh
supervisorctl reread
supervisorctl update
supervisorctl start volo_pi05
/workspace/envs/openpi/bin/python /workspace/volo_repro/scripts/health.py --port 8000 --infer
bash /workspace/volo_repro/scripts/run_experiment.sh baseline
```

两个服务 `autostart=false`，只监听 127.0.0.1，不需要公开端口。日志在 `/var/log/portal/volo_pi05.log`、`volo_orch.log`。脚本设置 JAX `XLA_PYTHON_CLIENT_MEM_FRACTION=0.4`；通过 WebSocket 做真实健康检查，不使用旧示例的 `/health`。

`run_experiment.sh` 生成唯一 run ID、使用实验锁，baseline/normal 各跑 1 episode。仿真日志写入 `logs/l11_<mode>_<timestamp>.log`，结果写入 `/workspace/RoboLab/output/<run_id>/`。需要停止服务时使用 `supervisorctl stop volo_orch volo_pi05`。

非 Vast 主机需用本机的 supervisor/systemd 配置包装这两个脚本里的前台命令，并提供相同环境变量；不要直接假设 Vast 的工具路径存在。当前自动运行脚本还固定了 `/workspace`，改变目录时需同步修改 `common.sh`、两个 serve 脚本、`run_experiment.sh` 和 supervisor 配置。

### 6. 配置并验证 VLM，再运行 normal

手动创建 `/workspace/volo_repro/config.env`，填写实际的视觉模型 API 配置：

```dotenv
VLM_BASE_URL="https://YOUR_ENDPOINT/v1"
VLM_MODEL="YOUR_VISION_MODEL"
VLM_API_KEY="YOUR_PRIVATE_KEY"
```

这是 shell 环境文件；含特殊字符的值应正确引用。需要支持图片输入的 Chat Completions 兼容接口，base URL 按服务商实际路径配置。不要提交密钥，也不要把它贴进日志或聊天。

```bash
chmod 600 /workspace/volo_repro/config.env
source /workspace/volo_repro/scripts/common.sh
/workspace/envs/vlm-orch/bin/python /workspace/volo_repro/scripts/check_vlm.py \
  /workspace/volo_repro/results/l11-smoke/egocentric_mirrored_camera.png
```

要求返回场景 JSON 并打印 `VISION_API_OK`。本机更新 API 后已通过此检查。旧 256-token 上限曾截断 JSON，检查脚本现使用 1024 tokens、简短输出提示及 finish_reason 检查。验证日志见 [VLM recheck](logs/current/vlm-recheck-fixed.log)。

通过之后再执行：

```bash
bash /workspace/volo_repro/scripts/run_experiment.sh normal
```

normal 对应 `--mode subgoal --failure-monitor vlm --recovery-mode replan --use-front-camera --check-interval 80`（subgoal 模式中为仿真步间隔）。读取该次 `episode_results.jsonl` 的 `success` 判断任务是否成功，并保留代理事件和视频。进程退出码 0 只表示程序正常结束，不代表 `success=true`。

## 迁移与历史记录

- 本机 `/workspace` **不是持久卷**。stop/start 保留容器文件，但 recycle/destroy 会丢失；需要在离开机器前把更改提交/推送或另行备份。本次文档更新本身不会自动上传 GitHub。
- Git 中应保留 README、脚本、补丁/锁文件、选定 PNG/JSON/JSONL 和诊断记录。权重、tokenizer、完整上游资产、环境及视频需重新下载或单独迁移。
- 最有价值的免下载迁移目录：`volo_repro/cache/`、`RoboLab/assets/`、`RoboVoLo/` 和 `RoboLab/output/`。Python 环境优先按固定源码/锁文件重建。
- `restore_sources.py`、`HANDOFF.md`、旧 `manifests/*-freeze.txt` 和故障注入 overlays 属于上一台机器的恢复方案；**当前布局不要直接运行旧 restore 流程**，它会创建另一套 repos 并应用本轮不需要的补丁。
- 旧 RTX 5090 / 595.71.05 在 Isaac Sim 初始化时崩溃，71 个单元测试通过也未证明真实仿真可运行。本机 4090 / 580.173.02 已通过真实 smoke 和 baseline，不需要旧 `compat/` 工作区中的 Vulkan workaround。

上游代码和资产保留各自许可证；本备份不替代 RoboLab、RoboVoLo、VoLoAgent、openpi 和外部 NVIDIA 资产的许可条款。
