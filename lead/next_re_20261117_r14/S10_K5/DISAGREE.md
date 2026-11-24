# S10-K5 · DISAGREE

| # | 对象 | 本卡结果与处置 | 依据 |
|---|---|---|---|
| D1 | S10_K4 U4 / task3_exhaustive 对 005B3A60 写“名无独立命名通道，未升” | **不同意**。按 S13_K4/S13_K5 已用判据逐条成立：RTTI/ctor/vtable 给类名，body 给 deleting-dtor 角色；升 [已证] MissionClass::scalar_deleting_destructor。 | EVIDENCE/005B3A60_DELETING_DTOR.txt；S13_K5/EVIDENCE/PROOF_SIX.md；S13_K5/_audit/VERDICT.md |
| D2 | S10_K4 U3 / task3_exhaustive 对 005B3970 写“Save 名无绑定，未升” | **部分不同意**。K4 在“字符串/独立符号名”口径下正确；但按本卡任务3的四环行为口径，枚举字段、写字段、caller 实参、callee Save/序列化语义齐全，升 [已证] MissionClass::Save。 | EVIDENCE/005B3970_SAVE_PROOF.txt；EVIDENCE/behavior_disasm.txt；EVIDENCE/stream_callees_disasm.txt |
| D3 | 19 行 K4 单源命名 grade | **初读发现不一致，工作期间被外部更正**。03:51 初读仍 111（19 行 [已证]）；03:53 复读 coverage 已于 03:52:48 降为 92（19 行 [静态推断]），与审计一致。本卡不越权改盘，两个快照都存证。 | EVIDENCE/baseline_recompute.txt；EVIDENCE/baseline_after_change.txt；S10_K4/_audit/VERDICT.md 必审2 |
| D4 | 派卡提醒 K3/K4 delta 可能刚被 M7 并入 | **以现场两次读盘为准**。初读 111 与卡面相符；03:52:48 外部又做了一次 grade 更正（非本卡 delta 并表），现读 92。本卡 delta 按现读 92 结算，不按旧卡面 111。 | EVIDENCE/baseline_recompute.txt；EVIDENCE/baseline_after_change.txt；COVERAGE/coverage.tsv 文件时间 |
| D5 | S13_K5 文中 test [esp+8] 作为通例 | **照其审计修正**：偏移随 push 数变为 0xC/0x10；本卡 6 行均一 push，字面 [esp+8] 成立，不把偏移本身当恒真判据。 | EVIDENCE/s10_scalar_dtor_candidates.txt |
| D6 | “MissionControl 及 slot 表还有同型 dtor”假设 | **未证实**。RTTI 无 MissionControl；MissionClass/MultiMission 全部虚表严格扫后仅 005B3A60 一条。 | EVIDENCE/mission_sweep_strict.txt |
| D7 | 5 条非 Mission 同型 S10 dtor 入 delta | **决策登记**：它们满足同一 S13 判据且同为 S10 非已证行，但不在任务2字面的 Mission 类范围；若 lead 要求严格范围可删，差额已在 UNKNOWNS U10 写明。 | EVIDENCE/s10_scalar_dtor_candidates.txt；EVIDENCE/delta_validate.txt |
| D8 | 005F3B80 盘上名 ObjectClass::ObjectClass | **不作为证据**。该名疑似陈旧/错位；本卡只引用其字节形态与 ctor 005F3900 的同组数组闭环。 | EVIDENCE/005B3A60_DELETING_DTOR.txt |

## 纪律自检
- 目标只读；未写 COVERAGE/coverage.tsv、未 git commit、未用 Ghidra。
- 写域仅 lead/next_re_20261117_r14/S10_K5/；所有 delta 行 entry/name 唯一，grade 为结论自身证据，不以 slot 归属单独升级。
