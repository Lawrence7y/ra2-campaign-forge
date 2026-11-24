# W94 UNKNOWNS（未知/待验清单）

> 结论分级：**[已验]** 离线实证；**[推断]** 由已验事实推出但未实测；**[未知]** 本卡无法回答。
> 本卡未启动游戏（真机锁归 W91），故一切"真机行为"均为 [推断]，等级如实标注。

## U1 · [未知] 每趟子进程链在真机上的锁/门禁时序
`w94_trip.py` 的锁门禁检查 `owner.startswith("w94")`，矩阵层在趟开始写 `owner=w94-batchrun`、结束恢复 `lead`。逻辑上闭合，但 install 阶段（`w94_offline.py`）也在 owner=w94-batchrun 期间跑，其门禁接受 `w94-batchrun`（已改）——**首次真机跑务必先跑 1 格 1 趟的迷你矩阵**确认无门禁竞态。

## U2 · [未知] 残留 gamemd 停机的实际处置手感
趟 runner 被杀（超时）后游戏是 detached 进程，矩阵层只记录 pid 并停机，**不做**一揽子 taskkill。谁来关、怎么关（唯一 pid 甄别后 taskkill）留人工。这条是纪律的保守取舍，不是功能缺失——但真机上第一次撞到时要在 matrix_log 里补处置记录。

## U3 · [未知] `Crewed` 规则覆盖是否被引擎按 rules 解析
照抄 W88 C4 的 caveat（静态不可证明）。W88 C7 的行为学判据可以复用：若 C7 臂（crewed+全 Hunt+重叠）转绿而 C2 崩，则覆盖生效且车组刷新必要。矩阵层不改这条结论，只提供臂。

## U4 · [推断] 同格重复趟的包复用
`BUILD_<cell>.json` verdict=PASS → 不重建；安装时三件套 sha 相同 + verify 过 → 短路。推断依据：W88/W90 已验证"installed == package 逐字节断言"有效。风险：`ra2forge_install.json` manifest 里的条目名仍是同一 package id 的重复安装记录——`w94_offline` 的短路径不重装，因此不会产生重复条目；但**换格后**（uninstall→install）manifest 是否累积脏条目未验。

## U5 · [未知] shuffle 抵消时间漂移的实际效果
只保证了执行顺序随机化（seed 固定可复现）并逐趟记录 `matrix_log.ndjson`。漂移本身（W90 §2 观察到交战臂 ±8% 波动、对照臂 ~1.9%）是否被 N 趟均值吸收，要真机 N≥3 数据才能说。

## U6 · [推断] trip 目录名解析约束
`trip_<cell>_r<k>` 贪婪解析要求 cell id 不以 `_r<数字>` 结尾（如 `c4_r1` 会错位）。validate 未硬拦（正则只查字符集）——**计划期不会报错**，解析期才错。已在 BATCH.md 写明，未加硬校验（见 DISAGREE D2）。

## U7 · [未知] `stop_on` 多条件并存的真实语义
示例（卡面原文）同时给 `engine_error_count>=2` 与 `any_crash`；因引擎错误计入 crash，`any_crash` 必然先触发。矩阵层按"每趟结束逐条评估、先命中先停"实现，但**">=2 是为了容忍单次软错误再观察一趟"的意图**在这种并存下无法表达——需要真机数据后决定要不要加"允许 N 趟宽限"语法。
