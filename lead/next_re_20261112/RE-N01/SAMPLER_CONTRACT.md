# SAMPLER_CONTRACT.md — 采样器契约（字段 / 状态 / 成本 / 精度 / 能力边界）

run_id = `NEXT_RE_20261112_R01`。
本契约约束 `candidate/re_n01_monitor.py`、`candidate/e3_stack_sampler_candidate_r2.py`、
`replay_re_n01.py` 与 `raw/*.ndjson`。**零真机**：本契约描述的是「测量工具应当记录什么」，
不是「游戏里发生了什么」。

---

## 1. NDJSON 每行公共字段（P5）

逐条写、每行 `flush()`（可选 `fsync`）。每行都是独立 JSON 对象；
`kind` ∈ `meta | frame_read | event`。**每一行**都带下列字段（meta 行也带，值可为 `null`）：

| 字段 | 类型 | 单位 / 语义 |
|---|---|---|
| `seq` | int | 单调递增记录号，从 0 起；`start_seq`/`end_seq` 引用它 |
| `t_mono_ns` | int | **单调时钟纳秒**（生产为 `time.perf_counter_ns()`；离线为注入的假时钟）。起点任意，只用差值 |
| `t_utc` | str | ISO-8601 UTC 墙钟字符串，仅用于对账/阅读，**不参与任何计算** |
| `gap_ns` | int | 本行 `t_mono_ns` − 上一行 `t_mono_ns`（首行 0）。**读失败区间原样保留，不压缩、不过滤** |
| `kind` | str | 记录类型 |
| `read_status` | str | `ok` / `read_failed` / `meta` / `event`。**禁止用 `null` 兼表状态** |
| `frame` | int \| null | 帧值；`read_failed` 行为 `null`（不是「帧没变」的证据） |
| `state_label` | str | 状态标签：`OK_FIRST` / `OK_SAME` / `OK_ADVANCING` / `MISSING_GAP` / `RESUME_AFTER_GAP` / `BOUNDARY_<marker>` / `EVENT_<state>` / `META` |
| `sample_flag` | bool | 该读数是否触发了采样事件（`frame_read` 行）；event 行恒 `true` |
| `segment` | int | 段号，从 0 起；边界处 +1 |
| `segment_reason` | str | `run_start` / `read_failed_gap` / `resume_after_gap` / `frame_regression` / `new_game` / `load_game` / `pid_change` |
| `marker` | str \| null | 仅边界读数带：`frame_regression` / `new_game` / `load_game` / `pid_change` / `read_failed_gap` |
| `pid` | int | 目标进程 id（用于 PID 变化分段） |
| `run_id` | str | 本轮 `NEXT_RE_20261112_R01` |
| `provenance` | str | `synthetic_fixture` / `derived_from_recorded_event` / `live_run_not_executed_this_round` |

### `meta` 行额外字段
`schema=re_n01_summary_v1`、`min_obs`（默认 6）、`stall_n_ns`（默认 1e9）、
`nominal_interval_ns`（默认 2e8 = 0.2 s）、`gap_max_ns`（默认 6e8 = 3×0.2 s）、
`note`。重算器从 meta 读配置，不硬编码。

### `frame_read` 行额外字段
`note`（可选说明）。**读失败行仍有独立 `seq` / `t_mono_ns` / `gap_ns`**，
这是 P6 的基石：过滤掉它们就会把两端同值拼成连续冻结。

### `event` 行额外字段（P3）
| 字段 | 语义 |
|---|---|
| `event_id` | `E0001` 形式，单调 |
| `mode` | `single_thread` / `all_threads` |
| `sample_state` | 五态之一，见 §2；**永不 `null` / 空串** |
| `resume_state` | 与 `sample_state` **正交**：`not_applicable` / `verified_ok` / `failed` / `unknown` |
| `resume_ret` / `resume_ret_present` / `resume_ok` / `prev` | `ResumeThread` 原始返回值、是否有返回值、恢复是否成功、`SuspendThread` 上次挂起计数 |
| `errors` | `list[str]`，**恒为列表**（空列表 `[]` 只表示「本次没有错误」，不表示「恢复成功」） |
| `exception` | 字符串；空串 = 无异常（不是 `null`） |
| `budget_exceeded` / `budget_state` / `budget_ms` | 预算是否超限 / 状态 / 阈值（ms） |
| `n_threads_sampled` / `n_threads_attempted` | 实际采到帧的线程数 / 尝试线程数 |
| `preflight` / `ownership` | 前置校验结果（含 `is32`、`target_bits`、`walker_ready`、`n_threads_in_pid`）/ PID-TID 归属校验结果 |
| `frames_n` / `suspend_held_ms` | 帧数 / 采样器自报的挂起时长（ms，**仅参考**，见 §3） |
| `sample_called` / `sample_one_thread_calls` | 是否调用过全线程 `sample()` / 调用单线程入口次数（P1 自检） |
| `cost_ns` / `ns_marks` | 计时分项（ns）/ 原始整数里程碑（可独立复算） |

---

## 2. 五态语义（P4）

`SAMPLE_STATES = (not_attempted, ok, resume_verified_ok, resume_failed, error)`，
两两不同，**禁止用 `null` 或空值兼表任何一态**。

| 状态 | 含义 | 正面证据要求 |
|---|---|---|
| `not_attempted` | 未采集：preflight / PID-TID 归属 / 位宽校验被拒，或调用方放弃 | `n_threads_sampled=0`、零 `SuspendThread`、`preflight.ok=false` 且写明 `reason` |
| `ok` | 采到了、没有错误，但**没有逐线程恢复成功的正面证据** | `errors=[]` 且 `resume_ok is None` |
| `resume_verified_ok` | 恢复成功（**最强**） | `resume_ok=True` + `resume_ret` 有效 + 无恢复类错误 |
| `resume_failed` | 恢复失败 | `resume_ok=False` 或 `resume_ret∈{0xFFFFFFFF,-1}` 或 `_resume_errors` 非空；`errors` 必须非空 |
| `error` | 采样步异常 / 预算超限 / 未预期异常 | `exception` 非空或 `budget_exceeded=True`，且 `errors` 必须非空 |

`resume_state` 是独立维度：`verified_ok` 才是「恢复成功」的正面证据；
`errors=[]` **不能**推出恢复成功（这正是旧记录 `errors=null` 的问题）。

---

## 3. 事件成本的定义（P2；**端到端 ≠ 实际挂起时长**）

全部来自**同一个** `perf_counter_ns()` 整数时钟的里程碑做差，单位 **ns**：

```
candidate → verdict → preflight → ownership → suspend → context → walk → resume → end
```

| 字段 | 区间 | 说明 |
|---|---|---|
| `detect_ns` | candidate→verdict | 检测延迟（在 verdict **之前**，不属于 `end_to_end_ns`） |
| `preflight_ns` | verdict→preflight | 前置校验 |
| `ownership_ns` | preflight→ownership | PID/TID 归属校验（Toolhelp 快照） |
| `open_ns` | ownership→suspend | `OpenThread` + `SuspendThread` |
| `context_ns` | suspend→context | 上下文捕获 |
| `walk_ns` | context→walk | 走栈 |
| `resume_ns` | walk→resume | 恢复 |
| `overhead_ns` | resume→end | 恢复完成后的收尾（组事件、分段、写入） |
| **`end_to_end_ns`** | **verdict→end** | **端到端**：检测判定成立 → 事件结束（含恢复完成 + 收尾） |
| **`event_total_ns`** | **candidate→end** | **整事件**：含检测延迟，最完整 |
| **`suspend_held_ns`** | **suspend→resume** | **实际线程挂起时长的观测代理**，是上面分项的**重叠子区间**，**不可**加入分项之和 |

**关键区分**（写进结论时必须遵守）：

- `end_to_end_ns` / `event_total_ns` 是**本机观测到的整事件耗时**，包含 Python 调度、
  GC、文件 flush、符号/上下文准备等；**不是**「目标线程被挂起的物理时长」。
- `suspend_held_ns` 只是本机两次读时钟之间的差，是挂起窗口的**观测代理**；
  它与 `end_to_end_ns` 重叠，且**不等于**目标线程实际停止执行的时间。
- 因此 `paused_ms=0.0`（旧记录）既不是零开销，也不是整事件成本。
- **不得只记最后一次函数调用耗时**：旧驱动的 `paused_ms` 只包住
  `sample_one_thread()` 一次调用，漏掉检测、前置、走栈后收尾与落盘。
  T-A3 用「采样函数慢 + 后续步骤也慢」的假场景锁死这一点。

**望远镜恒等式（T-D1，容差 0 ns）**：

```
end_to_end_ns == preflight_ns + ownership_ns + open_ns
                 + context_ns + walk_ns + resume_ns + overhead_ns
```

因为所有分项都由同一组整数里程碑做差。容差 **0 ns** 的前提是同一时钟域；
跨进程 / 跨时钟域不适用。`suspend_held_ns ≤ end_to_end_ns`，
`detect_ns` 不计入 `end_to_end_ns`（但计入 `event_total_ns`）。

---

## 4. 计时器分辨率与可声称精度

实测（`out/timer_calibration_raw.txt` / `TIMER_CALIBRATION.md`）：
QPF = **10 MHz（100 ns/tick）**；`perf_counter_ns()` 最小非零间隔 **100 ns**；
`time.monotonic()` 在本机走 `GetTickCount64()`，分辨率 **15.625 ms**。

- 可声称：事件级分项在 100 ns 量级可分辨、单位 ns、同一时钟整数做差恒等。
- **不能**声称：纳秒级绝对精度、亚 100 ns 事件顺序、目标线程挂起的精确物理时长、
  逐帧耗时、采样「零扰动」。
- 旧记录 `paused_ms=0.0`：低于测量精度 / 被 `round(...,1)` 量化到 0.1 ms，
  **不是零开销**。

---

## 5. 能力边界（四条，逐条写清）

### 5.1 长停检测能力
标称轮询 `interval=0.2 s`，`stall_n=1.0 s`、`min_obs=6`。
能检测的是「**连续多次读数帧号不变、且累计真实时间 ≥1.0 s、且区间内无缺测证据**」的
**区间级**停滞。`confirmed` 需要同时满足：同一段内、`read_status` 全 `ok`、
帧值相同、`n≥min_obs`、`duration_ns≥stall_n_ns`、`gap_ns≤gap_max_ns`、
没有 `gap_interrupted` / `adjacent_to_gap`。
**零Δ连续段是区间结论，不是「游戏卡死 1.0 s」的因果结论。**

### 5.2 短停检测能力（0.1–0.2 s 是否覆盖）
**不覆盖。** 0.1–0.2 s 的停顿短于一个标称轮询间隔（0.2 s），
两次读数之间可能整段发生又结束而完全不被采样；即使被采到，
也达不到 `min_obs=6` 与 1.0 s 阈值。**本工具不能检测、不能度量、不能否认
0.1–0.2 s 量级的短停**；`fixture_short_stall.ndjson` 只是演示「不构成已证实长停」，
不是「没有短停」的证据。

### 5.3 区间推进速率
可以报告**区间级**推进：某段内 `frame_first→frame_last` 的增量 / 该段
`t_mono_ns` 时长，或零Δ段的时长分布。这是「按 0.2 s 抽样观测到的区间平均」，
不是瞬时帧率。旧驱动的 `median(非零Δ)/interval ⇒ fps` 把抽样差当逐帧速率，
**已删除，不得恢复**。

### 5.4 逐帧指标（**明写**）
> **0.2 s 轮询不能算逐帧 P95 / P99**（也不能算逐帧帧时间、逐帧抖动、
> 逐帧延迟分布、1% low）。两次读数之间可能跨过任意多帧，
> 帧号是**累计计数**而非逐帧时间戳；没有逐帧样本就没有分位数。
> 任何由本数据算出的「P95/P99 帧时间」都是无证据数字，本轮拒不出具。

---

## 6. 本数据不能支持的结论清单

1. 「游戏行为正确 / 没有卡死 / 性能达标」——离线测试通过只证明测量工具的记录与重算自洽。
2. 「真实 `SuspendThread` / `ResumeThread` / `StackWalk64` 配对行为正确」——全部是 stub，真机未验。
3. 「甲案采样零扰动 / 无挂起开销 / 满足 ≤50 ms 预算」——`paused_ms=0.0` 低于精度，且真机预算未测。
4. 「逐帧 P95/P99 / 帧率 / 帧时间分布」——见 §5.4。
5. 「0.1–0.2 s 短停不存在」——见 §5.2；只能说「本工具未观测到」。
6. 「读失败期间帧号没变」——读失败区间标 `missing_gap / undecidable`，**不可判**。
7. 「由 `raw/derived_from_14412.ndjson` 重算 3493 样本统计」——该样例只含 1 条真实事件
   + 4 行合成布局演示，**不含全量序列**；`source_n_samples=3493` 只是引用的元数据。
8. 「`gamemd.exe` 的 WOW64 上下文 / 符号解析可用」——真机前置条件未实现、未验
   （见 `UNCOVERED.md`）。
9. 「离线单测 13/0 ⇒ 真机可行」——见 `TEST_REPORT.md` 末尾声明。
10. 「两个 `workspace-write` / `danger-full-access` 下 selftest 读数不同 ⇒ 代码有 bug」——
    差别只在宿主文件策略（`%TEMP%`），见 `TEST_REPORT.md` §4。
