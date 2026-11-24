# S10-K5 PROGRESS（≤60 行）
目标 ra2youli\gamemd.exe SHA-256 73201CC0…F67476 现场复算一致；Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26；未用 Ghidra；只读目标，写入仅本卡目录。双通道：原始 PE 字节/capstone 入口到 ret；RTTI COL+0xC→TD+8 与虚表 slot；不依赖 atlas entry+size 作唯一证据。
两个读盘时点：03:51:32+08 初读 coverage mtime 03:27:21、size 3640877，S10 proved 111、named(S) 52，与卡面相符；03:53:10+08 复读发现 coverage 已于 03:52:48 被外部改写为 size 3652397，K4 那 19 行单源命名由 [已证] 降为 [静态推断]，现值 proved 92、named(S) 52。本卡以现场最新值 92 为结算基线，两个快照均存证。

## 结论表（7 行，全部 [已证]）
| entry | 新名 | grade | 证据路径 |
|---|---|---|---|
| 005B3A60 | MissionClass::scalar_deleting_destructor | [已证] | EVIDENCE/005B3A60_DELETING_DTOR.txt#005B3A60 |
| 004E0170 | FootClass::scalar_deleting_destructor | [已证] | EVIDENCE/s10_scalar_dtor_candidates.txt#004E0170 |
| 00523350 | InfantryClass::scalar_deleting_destructor | [已证] | EVIDENCE/s10_scalar_dtor_candidates.txt#00523350 |
| 006B1390 | SlaveManagerClass::scalar_deleting_destructor | [已证] | EVIDENCE/s10_scalar_dtor_candidates.txt#006B1390 |
| 006B8140 | SpawnManagerClass::scalar_deleting_destructor | [已证] | EVIDENCE/s10_scalar_dtor_candidates.txt#006B8140 |
| 00746E80 | UnitClass::scalar_deleting_destructor | [已证] | EVIDENCE/s10_scalar_dtor_candidates.txt#00746E80 |
| 005B3970 | MissionClass::Save | [已证] | EVIDENCE/005B3970_SAVE_PROOF.txt#005B3970 |

## 任务1：005B3A60 按 S13/S06 判据逐条成立
字节 56 8B F1 C7 06 C0 DC 7E 00 ... C2 04 00；入口到 ret 仅 11 条：恢复 4 vptr（7EDCC0/7EDCA4/7EDC9C/7EDC94）→ call 005F3B80 → test byte [esp+8],1 → call 007C8B3D → ret 4 → eax=this。
RTTI：虚表 007EDCC0 的 slot8（地址 007EDCE0）指向 005B3A60；COL 00805D28 → TD 00817B18 → .?AVMissionClass@@。ctor 005B2DA0 在 005B2DE9..2DFD 写同 4 vptr，ctor/dtor 闭环。
007C8B3D 为 CRT::_delete（盘上 [已证]，内部 call 007C93E8 CRT::free）；005F3B80 的字节写同组基类 vptr 并反注册数组，无 delete/ret4，符合基类析构而本行是标量删除析构。
name 非单源：类名来自 RTTI/虚表通道，deleting-dtor 角色来自字节通道；不使用 slotN 作语义。

## 任务2：同族清扫
Mission RTTI 池 5 个 TD（MissionClass + 4 个 MultiMission 容器）；MissionClass 4 张子虚表（007EDC94/9C/A4/C0）与主表 007EDCC0 全扫，strict 函数窗（入口到首 ret）命中标量删除析构 1/1：005B3A60。未发现 MissionControl RTTI TD；盘上 005B3700 名为 MissionClass::MissionControlClass 且已 [已证]，字节为常量初始化，不是析构。
Mission 家族在 delta 之外剩余 0 行。另按同一判据扫全部 S10 非已证行，检出 5 条同型非 Mission 类（Foot/Infantry/SlaveManager/SpawnManager/Unit slot8），RTTI 类名与 slot8 均独立成链，一并列表升级；未把非 Mission 行混入 Mission 命中数。
证据：EVIDENCE/mission_sweep_strict.txt、EVIDENCE/s10_scalar_dtor_candidates.txt、work/probe_vptr_writers.py 输出。

## 任务3：行为级语义（四环齐全才升）
005B3970 升 MissionClass::Save：①枚举/哨兵：005B3060 从 this+0xAC 取 mission id 走 0x5B34E8 派发表，0x816CAC 32 项名表，-1→0x817474 "<none>"；②字段：+AC/+B0/+B4/+BC/+C0 与由 +C8/+D0、0xA8ED84 现算的余量；③实参：edi=首个栈参，转给 005F6250 与每个 4A1D50/4A1CA0，调用者 0065AB10 同参；④被调语义：005F6250 调盘上已证 00410410 AbstractClass::Save，4A1D50/4A1CA0 为 4B/1B 序列化原语。详见 EVIDENCE/005B3970_SAVE_PROOF.txt。

## 任务4：失败关闭/穷举
005B3A10 仅 [B0]!=-1 布尔，无 caller 实参/被调语义，未升；005F5E80 有字段清零但缺枚举常量与命名闭环，未升；0070DD90 imm=1 与 RTTI 冲突仍为反例；B8 imm32 C3 26 行已在 K3/K4 全部归宿；K4 的 63 字符串命中均为共享尾引用。逐条结果见 EVIDENCE/mission_fields_probe.txt、EVIDENCE/behavior_disasm.txt、EVIDENCE/stream_callees_disasm.txt、S10_K4/EVIDENCE/task3_exhaustive.txt（引用核对）。

## 核心数字
现场最新基线（03:53:10 读）：S10 行 528 / ∩atlas 526 / 表外 2（0041B860,005B3740）；proved 92=17.4905%；named(S) 52；门槛 ceil(526/2)=263，尚差 171。
本 delta +7：合入模拟 proved 99=18.8213%，named(S) 59，门槛 263，尚差 164；0 重复 entry/name、0 placeholder name、0 证据断裂。
复算：work/baseline_recompute.py、work/mission_sweep_strict.py、work/probe_s10_dtors.py、work/probe_mission_fields.py、work/make_dtor_evidence.py、work/make_save_evidence.py、work/finalize.py；快照 EVIDENCE/baseline_recompute.txt（初读 111）与 EVIDENCE/baseline_after_change.txt（现读 92），校验 EVIDENCE/delta_validate.txt。
