# UNCOVERED.md — 本轮未闭合 / 未覆盖项（诚实清单）

run_id = `NEXT_RE_20261112_R01`。
写下来比假装完成有价值。以下每一项都**没有**在本轮验证；`TEST_REPORT.md`
的「13/0 全绿」不覆盖其中任何一条。

---

## 1. 真机与真实 Win32 行为（最大缺口）

| # | 未覆盖内容 | 为什么没做 |
|---|---|---|
| U1 | 真实 `SuspendThread` / `ResumeThread` 的挂起计数语义与配对 | 授权边界铁律：严禁真机 / attach / 活进程 |
| U2 | 真实 `StackWalk64` + dbghelp 符号初始化 / 回溯正确性 | 同上；本轮 `_walk` 全部是 stub 或单帧回退 |
| U3 | 真实 `Wow64GetThreadContext` 读 32 位 `gamemd.exe` 的 WOW64_CONTEXT | 同上。r2 采样器 docstring 自承「这是真机放行前置条件，**尚未实现**」 |
| U4 | 「结构不匹配时 GetThreadContext 返回成功但字段全零」的静默失败在真机上的复现 | 同上；只有离线 stub 能模拟 |
| U5 | 19 线程目标下「单次总停顿 ≤50 ms」是否真的满足 | 无真机、无真实线程挂起窗口；`paused_ms=0.0` 低于精度（见 TIMER_CALIBRATION.md） |
| U6 | `CreateToolhelp32Snapshot` / `Thread32First` 的 `dwSize` 设置在真机上的必要性 | 只有 stub 验证 |
| U7 | 反身护栏 MF-8「采样窗口与②读数窗口不重叠」在真机上是否成立 | 只有纯函数 `reflexive_guard_ok()` 的离线单测 |
| U8 | `--live` / `main_live()` 的真机入口护栏（除「拒绝自 pid / 无 pid」两条离线断言） | 不执行，避免任何触碰真机的可能 |

## 2. 游戏行为与数据

| # | 未覆盖内容 |
|---|---|
| U9 | 游戏窗口线程 tid 的判定（`GetWindowThreadProcessId` 返回值）在真机上是否正确 |
| U10 | `G_FRAME = 0x00A8ED84` 在当前游戏版本是否仍是帧号地址 |
| U11 | 停滞阈值 `N=1.0 s`、`min_obs=6` 的误触率（原件称 §532 复算 0）是否仍成立 |
| U12 | 3493 样本统计的**重算**：`raw/derived_from_14412.ndjson` 只含 1 条真实事件 + 4 行布局演示，不含全量序列，**不能**重算 |
| U13 | 逐帧 P95 / P99 / 帧时间分布：0.2 s 轮询不产生逐帧样本（见 SAMPLER_CONTRACT.md §5.4） |
| U14 | 0.1–0.2 s 短停的检测能力：低于一个标称轮询间隔，本工具**不覆盖** |
| U15 | 读失败区间内帧号是否变化：标 `missing_gap / undecidable`，**不可判** |

## 3. 工程与流程

| # | 未覆盖内容 |
|---|---|
| U16 | `workspace-write` 策略下「MF8-d 改后是否转绿」：本会话是 `danger-full-access`，无法复现另一策略；只证明代码路径不再用 `%TEMP%` |
| U17 | `main()` 的 N1–N6 导航（启动游戏、控件点击、地图列表读取）端到端执行：**刻意不跑**（零真机铁律）；只对 N7 委托做了离线注入测试 |
| U18 | `attach_stackwalker()` 挂载真 `e3_stackwalker.py` 的路径（依赖同目录模块是否存在）未在本轮核实 |
| U19 | Windows 以外的平台可移植性（全部代码假定 Windows / ctypes.wintypes） |
| U20 | 长时间（240 s）连续运行的 NDJSON 文件体积 / flush 开销 / 磁盘失败恢复：只验证了「异常退出保留此前行」 |
| U21 | 并发写入同一 NDJSON、多进程重算、文件权限 / ACL 异常路径 |
| U22 | `perf_counter_ns()` 在跨 CPU / 休眠 / 虚拟机迁移下的单调性：只测了本机短时连续取样 |

## 4. 与「离线测试通过」的边界

`test_re_n01_offline.py` 13/0 全绿、`MUTATION_LOG.md` 5/5 变异变红，
证明的是：**这些断言有区分力，且当前候选件的记录/分段/计时/重算逻辑自洽**。
它没有证明、也不打算证明上表任何一项。特别是：

> 真实 `SuspendThread` / `ResumeThread` / `StackWalk64` 在活进程上的行为未验；
> 因此不能由本轮结果推出「甲案采样在真机上安全 / 无死锁 / 满足预算」。

---

## 5. 建议的下一步（需另行授权，本轮不做）

1. 在**无害哑进程**上做真实 Win32 路径的最小验证（前代理台账称曾做过
   `_live_verify_dummy.py` 17 项，但本轮**未复核该结论**，也不把它计入本轮证据）。
2. 实现 / 验证 32 位 WOW64 上下文读取，再谈 `gamemd.exe` 采样。
3. 若要逐帧指标，必须换测量手段（逐帧探针 / ETW / 游戏内埋点），
   不能靠 0.2 s 轮询外推。
