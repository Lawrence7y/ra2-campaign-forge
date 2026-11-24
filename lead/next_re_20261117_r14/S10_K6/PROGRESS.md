# S10-K6 PROGRESS（≤60 行）
目标 ra2youli\gamemd.exe SHA-256 73201CC0…F67476 现场复算一致；Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26；未用 Ghidra；只读目标，写域仅本卡。
## 现场基线（统一大小写；grade 只读第 5 列）
初读 04:09:26+08 与 finalize 04:22:07+08：coverage mtime 2026-11-18 04:05:20+08（M7/M8 已改）、size 3652533；S10 行 528、∩atlas 526、表外 2（0041B860/005B3740）；∩atlas proved **92/526=17.4905%**，named(S) 52，门槛 263，差 171。K5 7 行盘上仍未并入，本卡不触碰/不计数。
## 结论表（5 行，全部 [已证]，均行为级四环）
| entry | 新名 | 核心行为 |
|---|---|---|
| 004DF320 | AircraftClass::QueueMissionId2Or1_If5C8Or5CC | 清 +0x5D1；+0x5C8 非空则 QueueMission(id=2,target=1)，否则 +0x5CC 非空则 id=1,target=1 |
| 004DF3A0 | AircraftClass::QueueMissionId1_AfterCellTargetCheck | 清/恢复 +0x2B4，用 +0x9C 组目标，虚检后 QueueMission(1,1)，写 +0x5D1=1 |
| 004DFA70 | AircraftClass::QueueMissionId9_AfterNearestUnitSearch | 扫 House +0xA8/+0x9C 取最近对象，QueueMission(9,0)，返回 true |
| 00521760 | InfantryClass::QueueMissionId5Or15_OnOwnerCheck | 首参门控；owner(+0x21C)分支 QueueMission(5,0) 或 (15,0)，再调 [v+0x558] |
| 006F4960 | AircraftClass::QueueMissionId15_OnMissionId14 | 写 +0x41C；当前 mission(id=14) 且 House 非全局时 QueueMission(15,0)，写 +0x41B/+0x5778/+0x5779/+0x1F4 |
## 四环（见 EVIDENCE/QUEUE_MISSION_S10_PROOFS.txt#<entry>，逐行不截断）
①关键枚举常量：mission id 域由 0x816CAC 32 项指针表 + 005B30B8 cmp eax,0x1F 锁定；本卡只用数字 id 1/2/5/9/15，不用镜像名串命名。②字段写：QueueMission 005B35E0 将 [esp+4] id 写 [this+0xB4]、清 [this+0xB8]；SetMission 005B3570 再 +B4→+AC 并写 timer；各 body 另有上表字段写。③调用者实参：每个入选调用点均以 push target; push id; mov ecx,this; call [v+0x1E8] 传入 id/target，首参门控行另有 [esp+4]。④被调语义：005B35E0/005B3570 字节逐条展开，非按槽名推断。
## 命名与穷举
新名均由“数字 mission id + 可见字段/门控条件 + QueueMission 行为”生成；类名仅取 RTTI vtable，slot 号只作定位，不作语义；未用 mission 名表、slotN/vslotN/sub_ 作语义。
全量扫描：434 条 S10 非已证 ∩atlas 行；222 条含已证直接被调，17 条含字符串。QueueMission v[122] 在未证 S10 行内 41 个调用点/22 个 entry（EVIDENCE/queue_calls_nonproved.txt）。只升 5 个四环齐全且可行为命名的 entry；其余 17 个 entry 多为多 id 分支无法用单一行为名覆盖、缺字段写环或目标条件不可归属，失败关闭。
字符串候选（EVA_UnitSold/Lost、TXT_TECHNICIAN、Tip:*、TXT_PRIMARY）逐体复核仍缺独立被调/字段闭环，未升：EVIDENCE/string_candidates_disasm.txt、candidate_details.txt。K4 19 行单源命名仍为 [静态推断]，未重交；K5 7 个 entry 未触碰。
## 结算
本 delta +5：模拟 proved **97/526=18.4411%**，named(S) 57，门槛 263，差 166；0 重复 entry/name、0 占位名、0 证据断裂、0 forbidden 触碰。复算：work/baseline_recompute.py、rank_candidates.py、scan_queue_calls.py、make_queue_evidence.py、finalize.py、final_audit.py；校验 EVIDENCE/delta_validate.txt。
