# TEST_REPORT.md — RE-N01 测试报告

run_id = `NEXT_RE_20261112_R01`；策略：`danger-full-access`。
**原始 stdout 与逐条 exit code：`TEST_OUTPUT.txt`（22,696 B，由 `make_test_output.py`
用 `subprocess` 捕获，未加工）。**

> **本轮零真机，所有 Win32 为 stub；真实 `SuspendThread` / `ResumeThread` /
> `StackWalk64` / `Wow64GetThreadContext` 行为未验。**
> 未启动游戏（gamemd.exe / ra2loader / YURI.exe）、未 attach、未
> `ReadProcessMemory` 活游戏进程、未 `SuspendThread` / `ResumeThread` /
> `StackWalk64` / MiniDump / 断点 / 注入 / 部署 / `taskkill`。
> 唯一一次真实的 Win32 调用是本机的 `QueryPerformanceFrequency`（计时器频率查询，
> 不打开任何进程），见 `TIMER_CALIBRATION.md`。

---

## 1. 精确命令与读数

| # | 精确命令 | 原始 stdout | 退出码 |
|---|---|---|---|
| 1 | `python -X utf8 test_re_n01_offline.py` | `结果：13 项检查，0 项失败` | **0** |
| 2 | `python -I -X utf8 candidate\e3_stack_sampler_candidate_r2.py --selftest` | `结果：58 项检查，0 项失败` | **0** |
| 3 | `python -X utf8 make_fixture.py` | 6 个 fixture + 1 个派生样例；每个都断言在线摘要 == replay 重算 | **0** |
| 4 | `python -X utf8 timer_calibration.py` | QPF=10,000,000 Hz；perf_counter_ns min=100 ns；monotonic=15.625 ms | **0** |
| 5 | `python -X utf8 mutation_run.py` | 5/5 变异变红、5/5 复原回绿（见 `MUTATION_LOG.md`） | **0** |
| 6 | `python -X utf8 -m py_compile <5 个模块>` | 无输出（成功） | **0** |
| 7 | `python -X utf8 replay_re_n01.py raw\<file> --quiet`（7 个文件逐个） | 无输出（成功） | 全部 **0** |

所有命令的 `cwd = D:\Project\ra2-campaign-forge\lead\next_re_20261112\RE-N01`。
`TEST_OUTPUT.txt` 里 `EXITCODE SUMMARY` 列出 13 条退出码，全为 0。

---

## 2. `test_re_n01_offline.py` 覆盖项（13 项）

| 断言 | 覆盖性质 | 关键手段 |
|---|---|---|
| T-A1 | P1 | 计数 spy：`--only-tid` ⇒ `sample()` 调用数 == 0、`sample_single` == 1 |
| T-A2 | P1 | 计数 spy：全线程 ⇒ 驱动不直接调 `sample_one_thread`，`sample()` == 1 |
| T-A3 | P2 | 假时钟「采样函数慢 6 tick + 后续步骤慢 4 tick」；断言 `event_total_ns > 最后一次调用耗时` |
| T-B1 | P3/P4 | 真 r2 采样器 + stub OPS，`resume_thread` 返回 `0xFFFFFFFF` ⇒ `resume_failed` 且 errors 非空 |
| T-B2 | P4 | 5 个假采样器构造五态，断言实际写出的 NDJSON event 行状态两两不同 |
| T-B3 | P3 | preflight 失败（`context_not_bound`）⇒ 零挂起 + `not_attempted` + 原因 |
| T-B4 | P3 | TID∉PID（Toolhelp 快照）⇒ 拒绝 + 写入事件 + 零挂起 |
| T-C1 | P5 | 循环第 4 tick 注入异常 ⇒ NDJSON 仍可解析、含此前 3 条 frame_read、文件已关闭 |
| T-C2 | P6 | 帧100 → 长读失败（真实 gap 2 s）→ 帧100 ⇒ 在线/离线两方 `confirmed==0`、段标缺测 |
| T-C2b | P6 阳性对照 | 无缺测长停 ⇒ `confirmed>=1`（防 T-C2 空壳全绿） |
| T-C3 | P6 | 帧号回退 / 新局 / 读档 / PID 变化 / 读失败 ⇒ 段号改变、marker 计数 >0 |
| T-C4 | 离线重算契约 | 同一 NDJSON：在线摘要 vs `replay_re_n01.py`，114 个叶子字段逐字段一致 |
| T-D1 | P2 | 六计时字段存在 + `end_to_end_ns >= 分项之和`（**容差 0 ns**，同一整数时钟望远镜恒等） |

**测试不是复跑作者自检器**：`--selftest`（58 项）是 r2 采样器自带的作者自检器，
本轮另写 13 项，并用 `mutation_run.py` 的 5 次变异证明这些断言**能失败**。

---

## 3. 覆盖 / 未覆盖

**已覆盖（离线、可重放）**：
- 驱动两条路径互斥（P1）、事件级分项计时（P2）、事件级完整状态（P3/P4）、
  流式 NDJSON 与异常保留（P5）、缺测/边界分段与不合并（P6）、
  在线摘要可由 `replay_re_n01.py` 逐字段重算（T-C4）。
- 6 个合成 fixture + 1 个派生样例的 NDJSON 全部可由 replay CLI 成功重算（exit 0）。
- 原件 SHA 开工前 / 收尾后各实算一次，完全一致（`FACT_CHECK.md` §0）。

**未覆盖**：见 `UNCOVERED.md`。最核心一句：
> 真实 `SuspendThread` / `ResumeThread` / `StackWalk64` 在活进程上的行为、
> 32 位 WOW64 上下文读取、dbghelp 符号解析、19 线程下的 ≤50 ms 预算、
> 以及任何游戏行为，本轮**一项都没有验证**。

---

## 4. §四 宿主沙箱坑：并列两个读数（都真实）

`e3_stack_sampler_candidate_r2.py` 的 `run_selftest()` 里
`MF8-d 输出写入独立目录成功` 原来用 `tempfile.mkdtemp()` 再往里写文件。

| 策略 | 读数 | 出处 | 原因 |
|---|---|---|---|
| **`workspace-write`**（前代理当时） | **47 项检查 / 1 项失败**；唯一红：`MF8-d … write_fail:PermissionError` | `out/original_selftest_stdout.txt:44,61`；`out/r2_selftest_raw.txt:44,74` 亦记录同一红 | DSH 把 `%TEMP%` 映射到 `…\Temp\dsh-*\`，**允许建目录、拒绝在该目录内新建文件** ⇒ `PermissionError` |
| **`danger-full-access`**（本轮） | **58 项检查 / 0 项失败 / exit 0** | `TEST_OUTPUT.txt` 第 2 条命令；`out/selftest_verify_stdout.txt` | 同一行代码可写 `%TEMP%` |

**两个读数都真实，差别在宿主文件策略，不是采样器缺陷，也不是代码回归。**
r2 自检器从 47 项扩到 58 项是前代理加了 N01-01…N01-11 共 11 项断言，
与 MF8-d 的红/绿无关。

按任务卡 §四 的处置：
1. **没有删该断言**（`e3_stack_sampler_candidate_r2.py:1402` 保留
   `t("MF8-d 输出写入独立目录成功", pth is not None and werr is None, …)`）；
2. 把输出目录改成**被测工作区内的临时子目录**
   `Path(__file__).resolve().parent.parent / "out" / "_selftest_scratch"`
   （`:1395-1400`），不再依赖 `%TEMP%`，断言性质（写入独立目录成功）不变；
3. 本轮 `danger-full-access` 下改后复跑仍 `58 项 / 0 失败 / exit 0`；
   **无法在本会话复现 `workspace-write` 策略**，故「改后在 workspace-write 下是否转绿」
   不声称已验证 —— 但代码路径已不再触碰 `%TEMP%`，写域也收回
   `lead/next_re_20261112/RE-N01/` 内。
4. **不把它写成采样器缺陷**；`UNCOVERED.md` 只记「宿主策略差异未复现」这一事实。

---

## 5. 产物清单

```
RE-N01/
  candidate/_run_hl_match_candidate.py      驱动候选（N7 已委托 run_monitor）
  candidate/e3_stack_sampler_candidate_r2.py 采样器候选（+ sample(timer=) / MF8-d）
  candidate/re_n01_monitor.py              纯 Python 测量内核（新增）
  replay_re_n01.py                         只读离线重算器（修 confirmed 语义）
  test_re_n01_offline.py                   13 项离线测试
  make_fixture.py / mutation_run.py / timer_calibration.py / make_diff.py /
  make_test_output.py                      可复现脚本
  raw/*.ndjson                             6 fixture + 1 派生样例
  candidate.diff / DIFF.md / FACT_CHECK.md / MUTATION_LOG.md /
  SAMPLER_CONTRACT.md / TIMER_CALIBRATION.md / TEST_REPORT.md /
  UNCOVERED.md / DISAGREE.md / TEST_OUTPUT.txt
  out/*.txt / out/*.json                   原始 stdout、在线摘要、变异输出
```

---

## 6. 声明

**本轮零真机，所有 Win32 为 stub；真实 `SuspendThread` / `StackWalk64` 行为未验。**
13 项离线测试全绿只说明「测量工具的记录、分段、计时、离线重算自洽」，
**不说明游戏行为正确**、不说明甲案在真机上可行或安全。
任何把「离线测试通过」写成「游戏行为正确」的说法都与本报告冲突。
