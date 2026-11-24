# FACT_CHECK.md — RE-N01 前代理产物逐项对账

run_id = `NEXT_RE_20261112_R01`；本文件由续做执行代理**实算复核**后写。
原则：**不盲信表格，不看 docstring 当实现**。所有行号以本轮收尾后的文件为准。

---

## 0. 原件零字节改动（开工前 / 收尾后实算）

| 文件 | 期望 SHA-256 | 期望字节 | 开工前实算 | 收尾实算 |
|---|---|---|---|---|
| `_run_hl_match.py` | `33bb2f61a7696e51eed979452f3d6d86859ebcb1d8322f348ff04bdb0ffa9426` | 15,949 | 一致 | 一致 |
| `e3_stack_sampler_candidate.py` | `98210b4af460a75746913e35c791147982ec9d492349c9ace275ec817d51840a` | 55,720 | 一致 | 一致 |

用 `Get-FileHash -Algorithm SHA256` 实算，非转引。本轮**未执行任何 git 写操作**，
未对 `lead/re_d13_ruling_20261112/` 下任何文件写入一个字节。
（注：r2 采样器 `run_selftest` 的 `MF8-e` 只做**字符串前缀检查**，不写该目录；
本轮已把 `MF8-d` 的输出目录改到本轮写域，见 §4。）

---

## 1. 「原代理声称 / 实际」逐条

| # | 原代理声称（出处） | 实际（续做实算） | 处置 |
|---|---|---|---|
| 1 | 驱动副本「相对原件的关键修正 A/B/C/C2/D」均已实现（`candidate/_run_hl_match_candidate.py:23-30` docstring） | **假**。与原件做 LCS 逐行比对：`orig=442 行 / cand=470 行 / ratio=0.9671 / 仅新增 19 行注释 + 1 行 usage + 2 行 import`，**函数体逐字相同**。N7 循环仍是无条件 `res = sampler.sample(pid)`（旧 line 378），再判 `--only-tid`（379），再直接 `sampler.sample_one_thread(want_tid)`（381）；输出仍是 `paused_ms=round(cost,1)` 只记一次函数调用；仍打印 `median(非零Δ)/interval ⇒ fps` 伪帧率；仍把结果写进 **只读原件目录** `BASE / "_hl_match_%d.json"`（旧 line 483）。 | **已修正**：新增 `candidate/re_n01_monitor.py`，N7 改为委托 `mon.run_monitor()`（现 `_run_hl_match_candidate.py:367-419`）；删掉写回 BASE 与伪帧率。详见 DIFF.md。 |
| 2 | docstring 说「离线测试只调用可注入的 `run_monitor()`」（旧 line 20） | **假**：全文 grep 无 `run_monitor` 定义、无 `OnlineAccumulator`、无 NDJSON 写入。 | **已补齐**：`re_n01_monitor.py:run_monitor` / `MonitoringSession` / `OnlineAccumulator`。 |
| 3 | `replay_re_n01.py` 注释称「与驱动候选件内的 `OnlineAccumulator`（独立实现）逐字段一致；T-C4 对此做硬校验」（`replay_re_n01.py:21-22`） | **假**：驱动候选件里没有这个类；前代理也**没有写** `test_re_n01_offline.py`，因此该「硬校验」当时不存在。 | **已补齐**：`re_n01_monitor.py:OnlineAccumulator`（流式增量，与 replay 的批式归约无共用代码）+ `test_re_n01_offline.py:test_T_C4`（114 个叶子字段逐字段比对）。 |
| 4 | `candidate\e3_stack_sampler_candidate_r2.py` = 84,589 B，`--selftest` = 58 项 / 0 失败 / exit 0 | **读数属实**：本轮独立复跑 `python -I -X utf8 … --selftest` 得 `58 项检查，0 项失败`，`EXITCODE=0`（`out/selftest_verify_stdout.txt`）。字节数在本轮续做**之后**变为 85,650 B，因为补了 `sample(timer=)` 与 MF8-d 修正；前代理交付时 84,589 B 属实。 | 记录差异来源，无需回滚。 |
| 5 | `candidate\_run_hl_match_candidate.py` = 17,828 B，已 `py_compile` 通过 | **读数属实**（py_compile 通过）。但「通过」≠ 实现正确，见 #1。本轮改动后为 16,391 B。 | 同上。 |
| 6 | `out\r2_selftest_raw.txt` = 7,258 B，含 N01-08~N01-11 四项新断言 | **属实**：文件 7,258 B；第 68-71 行确有 N01-08（六计时字段 e2e≥分项和）、N01-09（E3Fail 被事件吸收）、N01-10（五取值两两不同）、N01-11（不写私有 `_target_is32` 也能采样）。但该自检器是**作者自检器**，不是本轮要求的独立离线测试。 | 本轮另写 `test_re_n01_offline.py`（13 项），并做 5 次变异测试证明能变红。 |
| 7 | `out\` 下 `_probe_direct.json` 等探针「内容只有 2 字节，可能是残留」 | **属实且已定性**：`_probe_direct.json` 内容恰为 `{}`（2 B），是空残留；`out/` 下另有 `original_selftest_stdout.txt` 5,249 B、`_harness_probe.py` 317 B 与三个空临时目录。 | 记为残留，不删（写域内、无副作用），不据此声称任何结论。 |
| 8 | 前代理 `out/r2_selftest_raw.txt` 第 44 行 `MF8-d` 为 RED（`write_fail:PermissionError`，47 项 1 红） | **属实，且不是代码缺陷**：`workspace-write` 策略下 `%TEMP%` 被映射到 `…\Temp\dsh-*`，允许 `mkdtemp` 建目录、拒绝在目录内新建文件。当前 `danger-full-access` 下同代码 58/0 通过。两个读数都真实，差别在宿主策略。 | 按 §四：**不删断言**，把输出目录改成被测工作区内 `out/_selftest_scratch`（`e3_stack_sampler_candidate_r2.py:1395-1402`），断言性质不变；TEST_REPORT.md 并列两个读数。 |
| 9 | 「输出报告必须能由原始 NDJSON 离线重算」（任务卡硬要求） | 前代理只交付了**重算器**，没有交付**在线写出报告的一方**（#1/#3）。此外 `replay_re_n01.py` 原 `_scan_zero_delta_runs()` 把「帧号变化」也记成 `frame_change_or_gap` 并排除出 `confirmed`，导致**只有整条流最后一段**才可能被证实为连续冻结 —— 这是会让「不产生已证实冻结」变成空壳全绿的隐藏缺陷。 | **两处同改**：`replay_re_n01.py:127-133,153-154` 改为 `frame_change`（正常推进），`re_n01_monitor.py:_RunScanner` 同步语义；新增 **T-C2b 阳性对照**证明无缺测长停确实能 `confirmed>=1`，防 T-C2 空壳。T-C4 逐字段校验两侧仍一致。 |
| 10 | 原件母本 SHA（见 §0） | 属实，开工前 / 收尾各实算一次，均一致。 | — |

---

## 2. P1–P6 核实结论（收尾后）

| 性质 | 续做前 | 续做后 | 证据（文件:行） |
|---|---|---|---|
| P1 单/全线程互斥 | **未成立**（驱动层）；采样器层成立 | **成立** | `candidate/e3_stack_sampler_candidate_r2.py:781-914`（`sample_single` 不调 `sample`）；`candidate/re_n01_monitor.py:631-650`（`build_event` 两分支互斥）；`candidate/_run_hl_match_candidate.py:374-428`（N7 只委托 `run_monitor`） |
| P2 事件级完整成本 | **部分**（采样器有 `perf_counter_ns` 分项，但驱动未用，且驱动仍只记一次调用） | **成立** | `re_n01_monitor.py:69-125`（`EventTimer` / `cost_from_marks` 11 字段）；`:652-702`（`run_monitor` 检测前标 `candidate`、收尾标 `end`）；`e3_stack_sampler_candidate_r2.py:194-203, 206-273` |
| P3 事件级完整状态 | **部分**（采样器有字段，驱动事件里没有） | **成立** | `re_n01_monitor.py:566-591`（`_event_from_single` 带恢复值/异常/预算/线程数/preflight/归属）；`e3_stack_sampler_candidate_r2.py:803-914` |
| P4 五态可区分 | **成立**（仅采样器常量） | **成立**，且驱动事件也强制校验 | `e3_stack_sampler_candidate_r2.py:119-130`；`re_n01_monitor.py:41-42`；`test_re_n01_offline.py:test_T_B2` |
| P5 流式原始记录 | **未成立**（完全没有 NDJSON） | **成立** | `re_n01_monitor.py:138-163`（每行 flush / 可选 fsync）；`:652-702`（`try/finally` 关文件并写摘要）；`test_T_C1` |
| P6 缺测/回退/新局/读档分段 | **未成立** | **成立** | `re_n01_monitor.py:170-243`（`_RunScanner`）、`:408-565`（`MonitoringSession.observe` 分段并保留 `t_mono_ns`/`gap_ns`）；`replay_re_n01.py:78-163`；`test_T_C2 / T-C2b / T-C3` |

---

## 3. 本轮新发现、前代理未提到的问题

1. **驱动会把结果写回只读原件目录**（旧 line 483 `BASE / "_hl_match_%d.json"`）：一旦跑 `main()` 就违反「`lead/re_d13_ruling_20261112/` 零字节改动」。已删除，全部产物改落 `RE-N01/out/`。
2. **离线 import 会加载 Win32 DLL**：旧驱动模块级 `ctypes.WinDLL("user32"/"kernel32")`。改为 `_bind_win32()` 延迟到 `main()`（`_run_hl_match_candidate.py:87-123`），离线 import 零 Win32 副作用。
3. **伪帧率**：`median(非零Δ)/interval ⇒ fps` 把 0.2 s 轮询的抽样差当逐帧速率，无物理依据，已删除并在 SAMPLER_CONTRACT.md「不能支持的结论」里明写。
4. **`time.monotonic()` 在本宿主机分辨率仅 15.625 ms**（`out/timer_calibration_raw.txt`），旧驱动用它测「几十 ms 的采样耗时」不可信；现统一 `perf_counter_ns()`（100 ns/tick）。
