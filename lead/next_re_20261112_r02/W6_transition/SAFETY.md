# SAFETY.md —— 挂起/恢复计数、残留、耗时、扰动

- run_id: `NEXT_RE_20261112_R02`；生成时刻(UTC): `2026-11-12T17:01:14.003606+00:00`；单次挂起预算 = **50.0 ms**（suspend_held_ns）。

## 1. 逐次抓栈的挂起/恢复核对

| label | tid | prev_count | resume_ret | sample_state | resume_state | held(ms) | errors | 干净还原 |
|---|---|---|---|---|---|---|---|---|
| G01 | 41576 | 0 | 1 | resume_verified_ok | verified_ok | 6.349 | [] | True |
| G02 | 41576 | 0 | 1 | resume_verified_ok | verified_ok | 2.086 | [] | True |
| G03 | 41576 | 0 | 1 | resume_verified_ok | verified_ok | 2.657 | [] | True |
| G04 | 41576 | 0 | 1 | resume_verified_ok | verified_ok | 1.881 | [] | True |
| G05 | 41576 | 0 | 1 | resume_verified_ok | verified_ok | 7.700 | [] | True |
| G06 | 41576 | 0 | 1 | resume_verified_ok | verified_ok | 1.287 | [] | True |
| G07 | 41576 | 0 | 1 | resume_verified_ok | verified_ok | 5.906 | [] | True |
| G08 | 41576 | 0 | 1 | resume_verified_ok | verified_ok | 1.204 | [] | True |
| G09 | 41576 | 0 | 1 | resume_verified_ok | verified_ok | 1.424 | [] | True |
| G10 | 41576 | 0 | 1 | resume_verified_ok | verified_ok | 1.509 | [] | True |
| G11 | 41576 | 0 | 1 | resume_verified_ok | verified_ok | 2.618 | [] | True |
| G12 | 41576 | 0 | 1 | resume_verified_ok | verified_ok | 4.425 | [] | True |
| G13 | 41576 | 0 | 1 | resume_verified_ok | verified_ok | 1.153 | [] | True |

- 抓栈总数 13；干净还原（prev=0 → resume_ret=1）=13 ⇒ **零残留挂起 = 是**。
- hold_abort（超预算中止）= False。

## 2. 安全约束落地

1. 逐线程「挂→走→立刻恢复」（W3 `do_grab`→r2 `sample_single` 单线程口径）；`try/finally` 兜底；`prev_count>0` 的线程被跳过。
2. 跳过自身线程：目标 tid=41576 ≠ 采样器自身线程（GetCurrentThreadId=37084）。
3. 符号初始化在挂起前完成（`attach_walker` 在任何抓栈之前执行）。
4. 单次挂起 ≤50 ms；r2 事件预算 300 ms；两者分别记录。
5. 全程只读 `ReadProcessMemory`；无写目标内存、无注入、无断点、无 MiniDump、无 hook。
6. 只处理自己启动的 pid=4460；收尾残留核对见 CONFIG_RESTORE.md。

