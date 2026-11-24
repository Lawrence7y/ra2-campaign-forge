# TIMER_CALIBRATION.md — 计时器分辨率实测与「能/不能声称什么精度」

run_id = `NEXT_RE_20261112_R01`。
实测脚本：`timer_calibration.py`（纯本机计时器查询 + CPython 的 `time` 模块）。
**原始实测输出：`out/timer_calibration_raw.txt`（本文件所有数字均来自该文件，无估算）。**

零真机声明：脚本只查询**本机** `QueryPerformanceFrequency`（对 kernel32 的频率查询）
和本 Python 进程的 `time.perf_counter_ns()` / `time.monotonic()`。
**未启动游戏、未 attach、未打开任何目标进程、未 ReadProcessMemory、
未 SuspendThread / ResumeThread / StackWalk64。**

---

## 1. 实测值（Python 3.12.10，Windows）

| 量 | 实测值 | 出处 |
|---|---|---|
| `QueryPerformanceFrequency` | `ok=1`，**10,000,000 Hz**（1 tick = 100 ns = 0.1 µs） | `out/timer_calibration_raw.txt` 第 5-7 行 |
| `time.get_clock_info('perf_counter')` | `resolution=1e-07 s` = **100 ns**，`monotonic=True`，`implementation='QueryPerformanceCounter()'` | 第 8 行 |
| `time.get_clock_info('monotonic')` | `resolution=0.015625 s` = **15,625,000 ns（15.625 ms）**，`implementation='GetTickCount64()'` | 第 9 行 |
| `time.get_clock_info('time')` | `0.015625 s`，非单调、可调 | 第 10 行 |
| `perf_counter_ns()` 连续 200,000 次取样 | **最小非零间隔 = 100.0 ns**，中位非零 = 200.0 ns，零间隔 0 次 | 第 12-14 行 |
| `perf_counter()` → ns | 最小非零 ≈ 99.986 ns，中位 ≈ 200.002 ns | 第 15-16 行 |
| `time.monotonic()` → ns | 最小非零 ≈ **14,999,999.999 ns**，中位 ≈ 15,499,999.994 ns；**200,000 次里只有 2 次非零** | 第 17-18 行 |

### 结论 1：`perf_counter_ns()` 与 `time.monotonic()` 不是同一个量级

本机 `time.monotonic()` 走 `GetTickCount64()`，可分辨间隔约 **15.6 ms**；
`perf_counter_ns()` 走 QPC，可分辨间隔 **100 ns**。
旧驱动用 `time.monotonic()` 测「几十毫秒的单次采样耗时」，读数可能被量化到
0 / 15.6 / 31.2 ms，**不足以支撑 ≤50 ms 预算或任何毫秒级成本结论**。
RE-N01 把事件级计时统一到 `perf_counter_ns()`（`re_n01_monitor.py:69-125`、
`e3_stack_sampler_candidate_r2.py:194-273`），理由即在此实测。

### 结论 2：能声称什么 / 不能声称什么

| 能声称 | 不能声称 |
|---|---|
| 事件级分项时间由**同一** `perf_counter_ns()` 整数里程碑做差，单位 ns，望远镜求和恒等（容差 0 ns，见 T-D1） | 「纳秒级精度」：QPC 一个 tick 就是 100 ns，`perf_counter_ns()` 返回的是按此频率换算的值 |
| 可分辨的最小非零间隔实测 100 ns；任何 ≥100 ns 的耗时不会被系统性读成 0 | 任何小于 100 ns 的耗时可被读成 0；也不能据此声称亚 100 ns 的事件顺序 |
| 端到端 / 分项是**本机墙钟上的观测耗时**，包含 Python 解释器调度、GC、文件 flush 等 | 「目标线程被挂起的精确物理时长」：`suspend_held_ns` 是本机两次读时钟的差，不是目标进程内部的计时 |
| 采样是 0.2 s 标称轮询，**区间级**推进/停滞证据 | 「逐帧」或「逐帧 P95/P99」；0.2 s 轮询两次读数之间可能跨过任意多帧 |
| 本报告原始 NDJSON 可离线重算，字段单位明确 | 「离线测试通过 ⇒ 真机采样行为正确」 |
| 缺测/读失败区间被保留并标「不可判」 | 「读失败期间帧号没变」——那是不可判，不是证据 |

---

## 2. `_hl_match_14412.json` 里 `paused_ms=0.0` 的正确解读

原件 `lead/re_d13_ruling_20261112/_hl_match_14412.json:16` 记
`"paused_ms": 0.0`（`mode=single_thread`，`picked_by=only_tid`，1 条事件，
`n_samples=3493`）。

> **`paused_ms=0.0` 是「低于当时测量精度」，不是零开销。**

依据（逐条有证据）：
1. 该值来自原件驱动 `t1 = time.monotonic(); one = sampler.sample_one_thread(...);
   cost = (time.monotonic() - t1) * 1000.0; "paused_ms": round(cost, 1)`。
   它**只包住了一次 `sample_one_thread()` 调用**，不含检测延迟、前置校验、
   走栈后的收尾、组事件与落盘，本身就不是「整事件成本」。
2. 本宿主机 `time.monotonic()` 分辨率 15.625 ms，且 `round(x, 1)` 把结果量化到
   **0.1 ms**：任何 <0.05 ms 的读数都会变成 `0.0`；15.6 ms 的量化台阶也让
   短耗时读数只有 0.0 / 15.6 两档附近。
3. 就算换成 `perf_counter_ns()`，仍受 100 ns/tick 与解释器调度限制；
   不可能由一次 0.0 读数推出「SuspendThread 没有开销」。
4. `raw/derived_from_14412.ndjson` 把这条真实事件原样保留在 `source_event`，
   并在 `meta.limitation` 明写这一条；该派生样例**不含全量 3493 样本序列**，
   **不能**用来重算 3493 样本统计。

因此：本轮**不**把 `0.0` 当作「甲案采样零扰动 / 无挂起开销 / 满足 ≤50 ms」的证据；
也不把「离线单测 13/0」当作任何真机性能结论。相关不可支持的结论清单见
`SAMPLER_CONTRACT.md` §5 与 `UNCOVERED.md`。
