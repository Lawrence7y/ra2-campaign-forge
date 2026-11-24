# W93 ABBA 观测器扰动标定脚本与说明（任务二）

> **卡号与性质**：W93（离线卡，禁止启动 `gamemd.exe`、禁止注入/调试器）
> **交付日期**：2026-11-14
> **依据协议**：`lead/next_re_20261112_r06/OBSERVER_ABBA_PROTOCOL.md`
> **结论级别说明**：
> - 脚本 CLI、`switch_log.ndjson` 格式、崩溃/Ctrl-C 行为与三档判决逻辑均经离线自测 `[本次实测]` 验证；
> - 真机运行中 `gamemd.exe` 连续 12 分钟（3 区组）ABBA 实测尚未执行 `[未证]`（受限于离线卡纪律）。

---

## 1. 脚本清单与用法

### 1.1 `abba_driver.py`（外部启停控制器）

`[本次实测]` 纯标准库脚本，只负责按 **A → B → B → A** 顺序循环启停只读观测器子进程（默认自动定位 `exp_rpm_framebeat.py`）并立即落盘 `switch_log.ndjson`。**不打开/不写目标进程内存、不注入任何 DLL/线程。**

真机典型用法：

```powershell
python lead\next_re_20261112_r06\W93_limiter\abba_driver.py `
  --pid <GAMEMD_PID> `
  --blocks 3 `
  --seg-sec 60 `
  --warm-sec 10 `
  --switch-log out\abba_switch_log.ndjson
```

关键参数（详见 `--help`）：
- `--pid PID`（必填）：透传给只读观测器的目标 PID。
- `--blocks BLOCKS`：ABBA 区组数（默认 `3`，每区组 4 段，共 12 段）。
- `--seg-sec SEG_SEC`：每段墙钟秒数（默认 `60`）。
- `--warm-sec WARM_SEC`：每段起始预热时长秒数，写入 `meta.warm_sec` 供分析阶段丢弃（默认 `10`）。
- `--switch-log PATH`：切换日志路径（默认 `./switch_log.ndjson`）。
- `--obs-out-dir PATH`：各 A 段观测器子进程标准输出及 CSV 输出根目录（默认 `<switch_log 同目录>/observer_segments`）。
- `--observer-script PATH`：相位 A 启动的观测器脚本（默认自动优先选用 `W90_replicates/work/tools/exp_rpm_framebeat.py`，备选 `W86_render_channel/experiment/exp_rpm_framebeat.py`）。
- `--poll-interval FLOAT`：段内轮询观测器存活与中断标志的步长（默认 `0.1` s）。

退出码约定：
- `0`：正常完成全部区组，或收到 `Ctrl-C` / `SIGINT` / `SIGBREAK` / `SIGTERM` 优雅停止并已写入 `finished`（`status="interrupted"`）。
- `2`：参数不合法或观测器脚本不存在。
- `3`：相位 A 观测器在段结束前提前退出（段中崩溃），已写入 `crash` 与 `finished`（`status="aborted_crash"`）并中止后续区组。

> 设计细节：向 `exp_rpm_framebeat.py` 传入的采集时长为 `ceil(seg_sec) + 5` 秒，由 `abba_driver.py` 精确控制段墙钟边界并调用 `terminate()`（超时回退 `kill()`）结束子进程；因此在 `[0, seg_sec)` 内只要子进程提前退出，即可无歧义判定为段中崩溃/异常退出。

---

### 1.2 `abba_analyze.py`（分段分析与三档判决）

`[本次实测]` 纯标准库离线分析脚本，联合读取 `abba_driver.py` 生成的 `switch_log.ndjson` 与被测采集器生成的逐拍 NDJSON（如 `w90_run.py` 产出的 `run.ndjson`，含 `t_perf_ns` / `win_cpu_ms` / `elapsed_ingame_s`）。

真机典型用法：

```powershell
python lead\next_re_20261112_r06\W93_limiter\abba_analyze.py `
  --switch-log out\abba_switch_log.ndjson `
  --run-ndjson out\run.ndjson `
  --budget-pp 0.5 `
  --json-out out\abba_summary.json
```

关键参数（详见 `--help`）：
- `--switch-log PATH`（必填）：`switch_log.ndjson` 路径。
- `--run-ndjson PATH`（必填）：被测逐拍 NDJSON 路径。
- `--warm-sec FLOAT`：覆盖预热丢弃秒数（默认读取 `switch_log` 内 `meta.warm_sec`，缺失时兜底 `10.0`）。
- `--budget-pp FLOAT`：CPU 消耗率差异预算，单位百分点（默认 `0.5`）。
- `--expected-blocks INT`：期望完整区组数（默认读取 `switch_log` 内 `meta.blocks`，缺失时兜底 `3`）。
- `--json-out PATH`：可选导出结构化 JSON 结果。

---

## 2. `OBSERVER_ABBA_PROTOCOL.md` 与实现对应表

| 协议条目 | 协议要求 | 脚本实现定位 | 核验状态 |
|---|---|---|---|
| 切换顺序 | `A -> B -> B -> A` 平衡设计，每区组 4 段 | `abba_driver.py`: `PATTERN = ("A", "B", "B", "A")` | `[本次实测]` |
| 默认规模 | `blocks=3`、`seg_sec=60`、`warm_sec=10` | `abba_driver.py` 默认参数与 `meta` 记录 | `[本次实测]` |
| 相位 A/B 定义 | A 启动 `exp_rpm_framebeat.py` 并记 PID；B 不启动 | `abba_driver.py` 仅对 `phase == "A"` `Popen` 启动并写 `observer_pid` | `[本次实测]` |
| 切换日志 | 每次切换落盘一行 `switch_log.ndjson`（含 `t_perf_ns`、段号、A/B、观测器 pid） | `write_ndjson_line` + `flush()` + `fsync()` | `[本次实测]` |
| 只读安全边界 | 仅启停外部只读进程，不注入、不写目标内存 | 仅调用 `subprocess.Popen` / `terminate` 管理己方子进程 | `[本次实测]` |
| 异常/退出保护 | Ctrl-C 写入 `finished`；段中崩溃记录并停止 | `SIGINT`/`SIGBREAK`/`SIGTERM` 处理 + `active_proc.poll()` 检测 `rc=3` | `[本次实测]` |
| 预热丢弃 | 丢弃每段前 `warm-sec` | `abba_analyze.py` 仅保留 `[t_start_ns + warm_ns, t_end_ns]` 内样本 | `[本次实测]` |
| 样本有效性过滤 | 过滤暂停/读写失败样本 | 校验 `win_cpu_ms is not None`、`read_status == "ok"`、`elapsed_ingame_s is not None` | `[本次实测]` |
| 单段指标 | `CPU 消耗率 = Δwin_cpu_ms / 墙钟` | `(last.win_cpu_ms - first.win_cpu_ms) / ((last.t_perf_ns - first.t_perf_ns)/1e6) * 100` | `[本次实测]` |
| 区组配对与统计量 | `d_block = mean(A) - mean(B)`，输出均值与极差 | 输出 `d_mean_pp`、`d_min_pp`、`d_max_pp`、`d_range_pp` 与方向一致性 | `[本次实测]` |
| 三档判决 | ≤0.5 pp 且同向⇒可接受；>0.5⇒不可接受；方向不一致⇒未分辨 | `[ACCEPTABLE]` / `[UNACCEPTABLE]` / `[UNRESOLVED]` | `[本次实测]` |
| 统计禁忌 | **严禁输出 p 值 / 置信区间（CI）** | 文本报告与 JSON 均不包含任何假设检验量或区间估计 | `[本次实测]` |

---

## 3. 离线自测证据

自测脚本：[test_abba_suite.py](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/EVIDENCE/test_abba_suite.py)
自测输出：[abba_selftest.txt](file:///D:/Project/ra2-campaign-forge/lead/next_re_20261112_r06/W93_limiter/EVIDENCE/abba_selftest.txt)

自测覆盖以下场景并全部通过（无游戏启动）：
1. `abba_driver.py --help` 与 `abba_analyze.py --help`（`rc=0`）；
2. 3 区组完整 `A->B->B->A` 驱动闭环（使用模拟 Python 观测器子进程，实测生成 12 段 `switch`/`seg_end`/`finished`）联动 `abba_analyze.py`；
3. 段中崩溃（模拟观测器运行 `0.15s` 后 `rc=42` 退出）：`abba_driver.py` 在 < 0.5s 内中断等待（不空等剩余段落），记录 `event="crash"` 与 `status="aborted_crash"` 并返回 `rc=3`；
4. `Ctrl-C` / `CTRL_BREAK_EVENT` 中断：捕获信号后终止活动观测器子进程，写入 `event="finished", status="interrupted"` 并返回 `rc=0`；
5. `abba_analyze.py` 三档判决全覆盖（`[ACCEPTABLE]`、`[UNACCEPTABLE]`、`[UNRESOLVED]`），并在每段预热窗内故意注入 `+9999 ms` CPU 尖峰验证其被完全丢弃、同时断言输出中无任何禁忌统计项。

---

## 4. 未覆盖项与风险边界（必读）

以下风险与限制**不得掩盖**，后续真机执行卡必须显式引用：

1. **无独立画面参照（核心限制）**：
   ABBA 协议与 `abba_analyze.py` 仅能度量观测器 `exp_rpm_framebeat.py` 对目标窗口线程 **`win_cpu_ms` 消耗率**的扰动（`d_block`）。**它不具备独立画面参照**——即便最终判决为 `[ACCEPTABLE]`（`<= 0.5 pp`），也**不能证明游戏实际显示帧未卡顿或不存在撕裂/微卡顿**；更不能单独用于判定限帧通道本身“客观不卡”。实际帧呈定性仍需独立外部画面/DX 呈帧时间戳（例如未修改游戏态下的 PresentMon/ETW 采集）。
2. **3 区组降配与统计功效不足**：
   按协议说明，3 区组系为控制单次标定时长（~12 分钟）而从原本裁决要求的 `≥ 5` 区组所作的降配。样本自由度极小，因此严格禁止计算 p 值与置信区间；若真机出现方向不一致（`[UNRESOLVED]`）或极差过大，需用 `--blocks 5` 扩大区组数重采。
3. **未覆盖真机 `gamemd.exe` 实跑**：
   因 W93 纪律禁止启动游戏，当前未在真实 `gamemd.exe` + `cnc-ddraw` 进程上验证 `exp_rpm_framebeat.py` 在 `switch` 边界高频切换下的实测稳态，也未验证 `w90_run.py` 与 `abba_driver.py` 并行采集时的真机文件 IO 竞争（`[未证]`）。
4. **未包含“> 50 ms 主线程卡顿频次”与“非 CPU 阻塞型扰动”**：
   若观测器通过 `ReadProcessMemory` 跨进程高频轮询仅带来极小 CPU% 上升、却偶发干扰调度或引起长尾单拍间隔（`> 50 ms`），平均值口径 `Δwin_cpu_ms / 墙钟` 可能不敏感；如有需要，后续可在不改动本判决主表的前提下附带长尾分位统计。
