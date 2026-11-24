# SAFETY.md —— 挂起/恢复计数、残留、耗时、扰动

- run_id: `NEXT_RE_20261112_R02`；生成时刻(UTC): `2026-11-12T15:25:11.921470+00:00`；单次挂起预算 = **50.0 ms**

## 1. 挂起/恢复计数核对（逐线程、精确还原）

| 趟 | tid | prev_count(SuspendThread 返回) | resume_ret(ResumeThread 返回) | resume_state | sample_state | errors | 无残留挂起(prev=0 且 ret=1) |
|---|---|---|---|---|---|---|---|
| C0 | 41924 | 0 | 1 | verified_ok | resume_verified_ok | [] | True |
| C1a | 41924 | 0 | 1 | verified_ok | resume_verified_ok | [] | True |
| C1b | 41924 | 0 | 1 | verified_ok | resume_verified_ok | [] | True |
| C1c | 41924 | 0 | 1 | verified_ok | resume_verified_ok | [] | True |

- 抓栈总次数：**4**；`resume_verified_ok`（恢复成功正面证据）：**4**；干净还原（prev=0 → resume_ret=1）：**4**。
- **零残留挂起 = 是**。判据说明：`SuspendThread` 返回 `prev_count`（本批要求 =0，即线程原本在运行、不接管别人的挂起态）；`ResumeThread` 返回其前一次挂起计数（=1），把计数还原到 0。两者配对即为「无残留挂起」的直接证据。
- 额外行为证据：每次抓栈后游戏仍能响应 `Esc` / `GUI:ResumeMission` 点击，且恢复后帧计数继续推进（详见 RUNLOG/CONTRAST 的 Δframe 读数），说明窗口线程未被遗留挂起。
- 实现约束落地：r2 `sample_single()` 只采 **1 个线程**（逐线程挂→走→立刻恢复，不一次性全挂）；`sample_one_thread()` 的 `try/finally` 保证任何异常路径都恢复；`prev>0` 的线程被跳过（`skipped=already_suspended`）；另加 `GetCurrentThreadId()` 显式守卫，目标 tid 与采样器自身线程不重合。

## 2. 单次挂起耗时（perf_counter_ns 分项）与预算

| 趟 | 取上下文 context_ns | 走栈 walk_ns | 恢复 resume_ns | 挂起总时长 suspend_held_ns(ms) | end_to_end(ms) | r2 预算超限 | 挂起窗口>50ms |
|---|---|---|---|---|---|---|---|
| C0 | 66200 | 5914200 | 11500 | 5991900 (5.992) | 74.690 | False | False |
| C1a | 63300 | 1877200 | 11000 | 1951500 (1.952) | 72.611 | False | False |
| C1b | 41400 | 1901300 | 13500 | 1956200 (1.956) | 75.173 | False | False |
| C1c | 55500 | 1998400 | 16400 | 2070300 (2.070) | 76.298 | False | False |

- 单次最长挂起耗时：**5.992 ms**（预算 50.0 ms）→ **未超限**。
- 超限处置：`hold_exceeded_50ms` 为真即中止后续抓栈并如实记录；本批触发 = **False**。
- 注：r2 的 `budget_exceeded` 以 `end_to_end_ns`（含 preflight/Toolhelp 枚举）计，**不是**纯挂起窗口；为避免 preflight 把有效样本误判成 error，r2 事件级预算放宽到 300 ms，而任务卡的 50 ms 口径单独施加在 `suspend_held_ns` 上。两者分别如实记录。
  `StackWalk64` 符号初始化 `SymInitialize(fInvadeProcess=TRUE)` 与 `modules_of()` 均在 **C0 之前、挂起任何线程之前** 完成。

## 3. 抓栈对目标的扰动 + 抓栈前后帧计数是否连续

扰动来源（均为只读或极短的线程暂停，无写入、无注入、无断点）：
1. 逐线程 `SuspendThread` 冻结游戏窗口线程 `suspend_held_ns`（上表，目标 ≤50ms）；期间该线程不推进逻辑帧，帧计数器 `0xA8ED84` 暂停；恢复后继续。
2. `StackWalk64` 通过只读 `ReadProcessMemory` 回调读取目标栈内存；`SymInitialize` 只读枚举目标已加载模块。均不写目标进程。
3. 抓栈前后各读一次哨兵（只读），本身不改状态。
4. **本趟（第 3 趟，主判据）额外**：挂起窗口内对 `ESP` 起 64 KiB 做只读 `ReadProcessMemory`（16 次 4 KiB 分块），用于交叉核验外层帧；该耗时已计入 `walk_ns` 与 `suspend_held_ns`，逐趟见 `out/*.json` 的 `raw_stack_crosscheck.capture_ns`。无任何写目标进程内存的操作。

| 趟 | 抓栈前 frame | 抓栈后 frame | Δframe(抓栈窗口内) | 说明 |
|---|---|---|---|---|
| C0 | 952 | 954 | 2 | 正常局内：短挂起导致该窗口内净增量偏小，恢复后继续推进 |
| C1a | 963 | 963 | 0 | 菜单暂停态：Δ=0 为预期（无回退、无虚增） |
| C1b | 1010 | 1010 | 0 | 菜单暂停态：Δ=0 为预期（无回退、无虚增） |
| C1c | 1057 | 1057 | 0 | 菜单暂停态：Δ=0 为预期（无回退、无虚增） |

- 结论：菜单暂停态（C1）抓栈前后帧计数**连续且恒定**（Δ=0），未出现回退或虚增；正常局内（C0）为单线程 ≤50ms 暂停，帧计数无回退。详见 `out/*.json` 的 `sentinels_at_grab` / `sentinels_after_grab`。

