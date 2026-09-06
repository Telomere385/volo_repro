# VoLo 复现执行记录

## 目标与授权
- 用户授权直接执行配置、安装和运行，并维护本文件。
- 不训练模型；pretrained pi05_droid_jointpos + 远程 VLM。
- L11 SwapBinReplaceFruitsTask：香蕉移到桌面，再将苹果放入容器。
- 本轮成功标准：真实评测输出 success=true，不额外要求有序子任务审计。
- 不记录 API 密钥。真实 VLM 的 endpoint/model/凭据尚待确认。

## 当前进度（2026-09-06）
- 已读实例指南及四个项目 README、旧 HANDOFF。
- RTX 4090 24GB，驱动 580.173.02；GL/OptiX/Vulkan 可用，尚未验证 Isaac Sim。
- 工作区非持久卷；此前约 111GB 可用空间。
- openpi 已是 xuningy 版本 aa6420561529593114160d05e5ad155792b272f3。
- RoboVoLo 69b5394、VoLoAgent b4e6230 与备份一致，工作区干净。
- 初始仅 base/main 环境，未启动模型服务。

## 问题、尝试与结果
- RoboLab 初始为 v0.3.1，需切换 README 指定的 v0.3.0。
- 旧环境从未跑通真实仿真；旧驱动兼容补丁不直接恢复。
- 旧脚本硬编码 /root/volo-repro，需要适配当前 /workspace 路径。
- 24GB 显存需分阶段验证仿真与模型，再验证同时运行。

## 下一步
1. 对齐 RoboLab，创建 robolab/openpi/vlm-orch 三个独立 Python 3.11 环境。
2. 安装 Isaac Sim 5.1 + Isaac Lab 2.3.2.post1、内容包和资产，执行 L11 smoke。
3. 下载 checkpoint，验证推理与 passthrough episode。
4. 验证远程 VLM，运行 subgoal + vlm monitor + replan 的完整 episode。
5. 记录真实结果与未解决问题。

## 执行更新
- RoboLab 已切换到 v0.3.0 / f72d394，复用备份 uv.lock 进行 frozen 安装。
- 已创建 /workspace/envs/{robolab,openpi,vlm-orch}，均 Python 3.11.15；使用 uv venv 隔离，不修改 main。
- VoLoAgent editable 安装完成；USD 下载工具依赖安装于 vlm-orch。
- RoboLab isaac51 和 openpi frozen 依赖安装进行中；日志位于 logs/current/。
- 已启动 LFS 补全和官方 SimReady 下载程序。
- L11 场景直接依赖 RoboLab 自带 vomp/container_b03、ycb/banana、objaverse/apple_01，不使用 avocado。
- smoke_l11.py 输出路径改为相对于当前备份仓库定位。
- 已询问 VLM endpoint/model，凭据要求保存在本地 config.env，不在聊天中传递。

## 已验证里程碑
- 三个环境安装完成；JAX 返回 CudaDevice(id=0)，VoLoAgent import 成功。
- RoboVoLo 安装完成：126 tasks、123 scenes、3 个自定义资产族。
- SimReady 33/34 下载成功；avocado 缺失，官方程序因此在下载阶段返回失败。随后使用 --skip-download 为已有资产完成 wrapper、物理和材质补丁。完整资产集仍不齐，但 L11 不依赖缺失项。
- **L11 smoke 通过**：Isaac Sim 5.1 原生运行，无 Vulkan 兼容层；8 个物理步，3 个有效 RGB 相机，前视/侧视包含 depth 输出。退出码 0。
- 结果：results/l11-smoke/result.json 和相机 PNG；日志 logs/current/l11-smoke.log。已目视确认香蕉在容器内、苹果在桌面。
- 日志出现容器碰撞网格回退 CPU 和 physics scene stepping 提示，但本次实际步进与相机输出完成。
- 模型/代理启动脚本已适配 /workspace 路径；openpi 应用 --host 参数补丁，模型绑定 127.0.0.1。
- supervisor 已注册 volo_pi05 / volo_orch，autostart=false，尚未启动；未开放公共端口。
- π0.5 权重正在下载。正常 VLM 实验先配置为 1 episode，成功以 success=true 为准。

### π0.5 下载与服务
- 权重下载完成，公开 GCS 对象大小核验通过：26 files / 12,435,136,033 bytes；未做密码学哈希校验。记录 results/checkpoint-integrity-current.json。
- tokenizer 已由 openpi 自动下载，checkpoint 内 droid norm stats 已加载。
- volo_pi05 已启动并监听 127.0.0.1:8000，JAX pool fraction=0.4；实际推理/JIT 检查进行中。
- run_experiment.sh 当前仅提供 baseline/normal 各 1 episode；禁用未安装补丁的 fault 入口，避免产生误标实验。

### 推理与 baseline
- 真实 π0.5 推理通过：动作 shape=(15,8)，有限值；首次 JIT 请求 18.091s，模型显存约 10GB。
- baseline 已启动：l11_baseline_20260906T100957Z，seed=0，1 episode，完整原始指令，passthrough。
- 仿真+模型并行显存约 15GB；已连接代理并进入动作循环。
- 用户已填 config.env，权限已设为 600；首次真实图片 API 请求返回 HTTP 401 / invalid_api_key。已请用户核对 key 与 endpoint 地域/服务。尚未验证 VLM 成功调用，不启动 normal 以免把认证失败误判为策略结果。

## 当前停止点 / 下一步（本轮最终状态）
- **baseline 完整运行结束，进程退出码 0，但任务 success=false**，score=0.5；900 步 / 60s 仿真时间，动作循环墙钟约 145s。结果原因：object_grabbed(object=apple_01) 条件未满足。
- 真实结果文件：/workspace/RoboLab/output/l11_baseline_20260906T100957Z/episode_results.jsonl（实际为实验根目录 JSONL，并非 README 示例中的任务目录 JSON）。
- 视频和逐步日志在上述目录的 SwapBinReplaceFruitsTask/ 下；代理事件在 results/l11_baseline_20260906T100957Z/。
- 已完成流程 1–4；流程 5 的真实图像 API 验证因 401 失败，未运行 VLM normal episode，未达成最终 success=true 目标。
- 等待用户修正本地 VLM 配置；修正后先运行 scripts/check_vlm.py 验证场景识别，再 bash scripts/run_experiment.sh normal，核对 episode_results.jsonl 的 success。
- volo_pi05 和 volo_orch 保持 RUNNING，仅本机 8000/8001；代理当前 passthrough，仿真已退出。main 环境及桌面管理服务未修改。
- 用户似乎将 config.env.example 重命名为 config.env（Git 显示 example 删除）；未覆盖用户配置。密钥文件被 Git 忽略且权限 600。
