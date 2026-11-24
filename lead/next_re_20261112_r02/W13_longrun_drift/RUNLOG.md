# W13 · RUNLOG.md（RE-N04b attempt 3）

时间均为本地 +08:00（2026-11-13）。

| 时刻 | 事件 |
|---|---|
| 03:22 | 开工：现场核对——锁 owner=lead（attempt2 后 Lead 收回）、gamemd 残留 0、载体 175,361 B / sha `3e3c8745…bfd5b19` 实算一致、baseline 5 文件在位 |
| 03:23 | 读 attempt1 归档：探针缺陷已修（`longrun_probe.py:166` EnumChildWindows 三参绑定在位）；attempt1 stdout 确认死点与其修复；attempt2 残档=out\run.ndjson 4 行（止于 pid_found 36088，无 meta_end） |
| 03:26 | 归档 attempt2 残档 → `out/attempt2_run.ndjson`；attempt1 收尾原件与归档哈希比对一致（CECA5708… / 70666AE0…） |
| 03:27 | **补丁**：探针 finally 增加「恢复锁 owner=lead」自愈环（attempt1/2 归档版缺失此环）；py_compile rc=0 |
| 03:28 | 绑定实测：`import longrun_probe` 通过，EnumChildWindows.argtypes=3 参（attempt1 死点验证已修） |
| 03:29:57 | **启动（方式 B：WMI 完全脱离）**：ProbePID=4940，ReturnValue=0；启动前锁 owner=lead、残留 0 复核通过 |
| 03:30:50 | 轮询#1：探针存活、gamemd pid=42824、已 phase=ingame（首帧后 13.7 s，frame=431） |
| 03:32:11 | 轮询#2：elapsed=94.5 s，frame=2956（区间 ~31.25 计数/s），fg=True |
| 03:33:37 | 轮询#3：elapsed=180.3 s，frame=5637，速率稳定 |
| 03:35:48 | 轮询#4：elapsed=311.7 s，frame=9743，速率稳定 |
| 03:38:27 | 轮询#5：elapsed=471.0 s，frame=14722，速率稳定 |
| 03:40:56 | 轮询#6：**末行 kind=meta_end**、ProbePID=4940 已退出、gamemd 残留 0 —— 探针自愈收尾闭环 |
| 03:41 | 读 meta/probe_stdout：stop_reason=**natural_end_grace_done**（对局 476.7 s 自然结束，GUI:Continue 检出 → grace 20 s）；有效局内段 496.7 s 计时 / 476.7 s ok 参考；读失败 0；配置还原自证全过；**lock_restored=true** |
| 03:41 | `analyze_drift.py` 跑通：**[未观测到漂移]**（drop_pct=−0.0048%，斜率 −0.000172 计数/s per 10 s）；windows.csv + analysis.json 落盘；锁 owner=lead 复核 |
| 03:42 | DRIFT_REPORT.md / SAFETY.md / CONFIG_RESTORE.md / RUNLOG.md / UNCOVERED.md 落盘；汇总发 Lead |

## 启动方式说明（为何选 B 而非推荐序里的 A）
卡面硬要求「探针必须脱离你的进程树，且自带收尾」。A（前台阻塞）探针仍是代理 pwsh 的子进程：
代理被收或 pwsh 超时转后台 job 时即 attempt2 失败模式。B（WMI Create）探针父进程为 WMI 服务宿主，
两级脱离（探针脱离代理、游戏脱离探针所属会话树），代理中途死亡探针照样跑完并自愈——本次实际采用 B。
