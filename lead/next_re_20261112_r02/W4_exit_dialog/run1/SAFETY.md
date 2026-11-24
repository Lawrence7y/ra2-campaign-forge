# SAFETY.md —— 挂起/恢复计数、残留、耗时、扰动

- run_id: `NEXT_RE_20261112_R02`；生成时刻(UTC): `2026-11-12T15:54:11.433787+00:00`；单次挂起预算 = **50.0 ms**（作用于 `suspend_held_ns`）

## 1. 挂起/恢复计数核对（逐线程、精确还原）

| 趟 | tid | prev_count | resume_ret | resume_state | sample_state | errors | 无残留挂起(prev=0 且 ret=1) |
|---|---|---|---|---|---|---|---|
| D0 | 37264 | 0 | 1 | verified_ok | resume_verified_ok | [] | True |

- 抓栈总次数：**1**；`resume_verified_ok`：**1**；干净还原（prev=0 → resume_ret=1）：**1**。
- **零残留挂起 = 是**。判据：`SuspendThread` 返回 `prev_count`（本批要求 =0，即线程原本在运行、不接管别人的挂起态）；`ResumeThread` 返回其前一次挂起计数（=1），把计数还原到 0。

## 2. 单次挂起耗时（perf_counter_ns 分项）

| 趟 | context_ns | walk_ns | resume_ns | suspend_held_ns(ms) | end_to_end(ms) | r2 预算超限 | >50ms |
|---|---|---|---|---|---|---|---|
| D0 | 53200 | 9046300 | 12000 | 9111500 (9.111) | 89.777 | False | False |

- 单次最长挂起耗时：**9.111 ms**（预算 50.0 ms）→ **未超限**；超限触发中止 = **False**。

## 3. 安全约束落地

1. `r2.sample_single()` 只采 **1 个线程**，逐线程「挂→走→立刻恢复」，不一次性全挂；`sample_one_thread()` 的 `try/finally` 保证任何异常路径都恢复；`prev>0` 的线程被跳过。
2. 跳过自身线程：显式 `GetCurrentThreadId()` 守卫，目标 tid ≠ 采样器自身线程 （本趟 = 12100）。
3. 跳过 `prev_count>0`：每趟 `prev_count` 见上表，均为 0 才抓。
4. `SymInitialize(fInvadeProcess=TRUE)`、`modules_of()`、回溯器挂载均在 **挂起任何线程之前**（D0 之前）完成。
5. 逐趟 `SuspendThread` 前记 `prev_count`，`ResumeThread` 按差值精确还原；全程 `try/finally`；最外层 `finally` 负责 SymCleanup/关游戏/还原配置。
6. 抓栈只在**平静状态**做：D0 = 开局后平静态阴性对照（协议强制），D1 = 确认对话框稳定存在 >3 s 后，D2 = 关框后平静恢复态。**未在激烈战斗中挂起**。（任务卡「抓栈只在对话框稳定存在时做」与协议强制的 D0 阴性对照存在张力，本趟按「两者都要求平静、禁止战斗中挂起」落地并如实说明。）
7. 挂起窗口内额外对 `ESP` 起 64 KiB 做**只读** `ReadProcessMemory`（交叉核验外层帧），耗时已计入 `walk_ns`/`suspend_held_ns`；无任何写目标进程内存、无注入、无断点、无 MiniDump。

## 4. 抓栈前后帧计数连续性

| 趟 | 抓栈前 frame | 抓栈后 frame | Δframe(窗口内) |
|---|---|---|---|
| D0 | 964 | 966 | 2 |

