# DIFF.md — 原文 vs 候选（统一 diff 与修改映射）

run_id = `NEXT_RE_20261112_R01`。
完整统一 diff：**`candidate.diff`**（1,072 行 / 53,572 B），由 `make_diff.py`
用 `difflib.unified_diff(n=3)` 生成，覆盖两对文件：

```
a/lead/re_d13_ruling_20261112/_run_hl_match.py
b/lead/next_re_20261112/RE-N01/candidate/_run_hl_match_candidate.py

a/lead/re_d13_ruling_20261112/e3_stack_sampler_candidate.py
b/lead/next_re_20261112/RE-N01/candidate/e3_stack_sampler_candidate_r2.py
```

原件 SHA-256 / 字节数开工前与收尾各实算一次、均一致（见 `FACT_CHECK.md` §0）。
`candidate.diff` 里的 `+` 行同时包含前代理的 r2 增量与本轮续做的修正；
新增的 `candidate/re_n01_monitor.py`、`test_re_n01_offline.py`、
`make_fixture.py`、`mutation_run.py`、`timer_calibration.py`、`make_diff.py`
是本轮/前代理**新文件**，没有「原文」可比，故不进 unified diff，逐项列在 §3。

---

## 1. 问题编号口径

任务卡要求映射到「问题 A/B/C/D」。此处沿用驱动候选件 docstring 的编号（前代理自己写的）：

| 编号 | 含义 |
|---|---|
| **A** | `--only-tid` 与全线程路径不互斥：先 `sample(pid)` 再丢弃结果，单线程路径又直接调 `sample_one_thread` |
| **B** | 单线程入口没有 preflight / 恢复返回值 / 异常 / 预算 / 线程数 / 归属校验；只记一次函数调用耗时；异常会穿透循环 |
| **C** | 没有流式原始记录：异常退出丢数据；摘要不能由原始记录离线重算 |
| **C2** | 读失败区间被过滤后，两端同值拼成「连续冻结」 |
| **D** | 计时用 `time.monotonic()`、输出 `median(非零Δ)/interval ⇒ fps` 伪帧率 |

本轮另立 **E**：驱动把结果写回**只读原件目录**，且模块级加载 Win32 DLL。

---

## 2. 「每个修改 → 对应 P1…P6 / 问题 A/B/C/D」映射表

| # | 修改（文件:行） | P1 | P2 | P3 | P4 | P5 | P6 | 问题 |
|---|---|:--:|:--:|:--:|:--:|:--:|:--:|---|
| 1 | `_run_hl_match_candidate.py:374-428`：删掉旧 N7 循环（无条件 `sample(pid)` → `sample_one_thread` → `paused_ms` → 写 BASE），改为委托 `mon.run_monitor()` | ✅ | ✅ | | | ✅ | ✅ | **A / B / C / C2 / E** |
| 2 | `re_n01_monitor.py:631-650` `build_event()`：`only_tid` 只调 `sample_single(tid,pid,timer=...)`；否则只调 `sample(pid,timer=...)`，**不直接**调 `sample_one_thread` | ✅ | | | | | | **A** |
| 3 | `e3_stack_sampler_candidate_r2.py:781-914` `sample_single()`：`preflight_target()` 在任何挂起之前完成；恢复返回值/异常/预算/线程数/归属入事件；`try/except` 不穿透 | ✅ | | ✅ | ✅ | | | **B** |
| 4 | `e3_stack_sampler_candidate_r2.py:916-933` `sample(pid, timer=None)`：新增可选 timer（原 47 项自检语义逐字不变），让全线程路径也有分项里程碑 | ✅ | ✅ | | | | | **A / D** |
| 5 | `e3_stack_sampler_candidate_r2.py:127-130` `SAMPLE_STATES` + `RESUME_STATES` 五态 + 正交恢复态 | | | ✅ | ✅ | | | **B** |
| 6 | `re_n01_monitor.py:69-125` `EventTimer` / `cost_from_marks`：`perf_counter_ns()` 整数里程碑，端到端 + 检测/前置/归属/上下文/走栈/恢复/挂起时长/收尾 | | ✅ | | | | | **B / D** |
| 7 | `re_n01_monitor.py:652-702` `run_monitor()`：`candidate` 标在检测前、`end` 标在事件收尾后；`post_hook` 之后仍计入整事件 | | ✅ | | | | | **B / D** |
| 8 | `re_n01_monitor.py:566-629` `_event_from_single` / `_event_from_all`：恢复值、异常、预算、线程数、preflight、归属全部写进事件行 | | | ✅ | | | | **B** |
| 9 | `re_n01_monitor.py:138-163` `NDJSONSink`：逐条 NDJSON、每行 `flush()`、可选 `fsync`；`run_monitor` 的 `try/finally` 关文件并写摘要 | | | | | ✅ | | **C** |
| 10 | `replay_re_n01.py:78-163` + `re_n01_monitor.py:170-243,245-392`：缺测感知零Δ扫描 + **独立**流式 `OnlineAccumulator`，两者输出 `re_n01_summary_v1` 逐字段一致（T-C4） | | | | | ✅ | ✅ | **C / C2** |
| 11 | `re_n01_monitor.py:408-565` `MonitoringSession.observe()`：读失败保留 `t_mono_ns` / `gap_ns` 原值并切 `read_failed_gap` / `resume_after_gap` 段；帧号回退 / 新局 / 读档 / PID 变化各自切段 | | | | | | ✅ | **C2** |
| 12 | `replay_re_n01.py:127-133,153-154`：把「帧号变化」从 `frame_change_or_gap` 改为 `frame_change`，修掉「只有末段能 confirmed」 | | | | | | ✅ | **C2**（防 C2 空壳） |
| 13 | `e3_stack_sampler_candidate_r2.py:194-273` `_now_ns()` / `EventTimer` / `cost_from_marks`（前代理增量） | | ✅ | | | | | **D** |
| 14 | `_run_hl_match_candidate.py:87-123` Win32 绑定延迟到 `main()`；`:70` 只 import 纯 Python 模块 | | | | | | | **E**（可测性 / 零 Win32 副作用） |
| 15 | `e3_stack_sampler_candidate_r2.py:1395-1402` MF8-d 输出目录从 `%TEMP%` 改到工作区内 `out/_selftest_scratch`（**不删断言**） | — | — | — | — | — | — | §四 宿主沙箱坑；**不是采样器缺陷** |
| 16 | 删除 `median(非零Δ)/interval ⇒ fps` 伪帧率输出与写回 BASE 的结果文件 | | ✅ | | | | | **D / E** |

图例：✅ = 该修改直接支撑该性质；空白 = 不直接相关。

---

## 3. 新增文件清单（无「原文」可比）

| 文件 | 用途 |
|---|---|
| `candidate/re_n01_monitor.py` | 纯 Python：`EventTimer` / `NDJSONSink` / `_RunScanner` / `OnlineAccumulator` / `MonitoringSession` / `build_event` / `run_monitor` |
| `test_re_n01_offline.py` | 13 项独立离线测试（T-A1…T-D1 + T-C2b 阳性对照） |
| `replay_re_n01.py` | 前代理交付的只读离线重算器；本轮只修 §2 第 12 项 |
| `make_fixture.py` | 可重复生成 `raw/fixture_*.ndjson` 与 `raw/derived_from_14412.ndjson` |
| `mutation_run.py` | 5 条变异测试驱动器（只改副本） |
| `timer_calibration.py` | 本机计时器分辨率实测 |
| `make_diff.py` | 生成 `candidate.diff` |
| `raw/*.ndjson` | 6 个合成 fixture + 1 个派生样例 |
| `TEST_OUTPUT.txt` / `out/*.txt` / `out/*.json` | 原始 stdout 与在线摘要 |

---

## 4. 体积与差异规模（实算）

| 对 | 原件行 | 候选行 | LCS ratio | 主要改动 |
|---|---:|---:|---:|---|
| driver | 442 | 438（收尾后） | ≈0.87 | 前代理 +19 行 docstring；本轮删旧 N7 循环、加惰性 Win32 绑定与 `run_monitor` 委托 |
| sampler | 1,190 | 1,798（收尾后） | ≈0.79 | 前代理 +约 600 行（五态 / preflight_target / sample_single / 分项计时 / N01 自检）；本轮 +约 9 行（`sample(timer=)`、MF8-d） |

前代理交付时的 driver 是 470 行、与原件 ratio=0.9671（**只改了 docstring**）——
这是 `FACT_CHECK.md` §1 #1 的核心证据。

---

## 5. 未做的改动（刻意保持「改动要小」）

- 不重构 `main()` 的 N1–N6 导航（保留原 CLI 语义）；只替换 N7 监测段。
- 不改 r2 采样器原有 47 项自检的任何判据；`sample()` 新参数是**可选**的。
- 不动 `lead/re_d13_ruling_20261112/` 下任何原件（只读、零字节改动）。
- 不执行任何 git 写操作。
