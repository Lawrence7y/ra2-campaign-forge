# S10-K4 · PROGRESS（19 行 Mission handler 语义/真名更正）
> ra2youli\gamemd.exe SHA-256 73201CC0…F67476；Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26；未用 Ghidra；只写本卡目录。

## 任务4：基线自算（EVIDENCE/baseline_recompute.txt）
- S10 coverage 528；coverage∩atlas（统一大小写）**526**；表外 2（005B3740 outside-atlas，0041B860）。
- ∩atlas grades：已证 **88**（16.7300%）／静态推断 423／未证 15；DoD 50% 门槛 **ceil(526/2)=263**，尚差 175。
- 严格 named(S)（排除 sub_/::sub_/::slotN/::vslotN）=29；L 口径=511。卡面 513/257 未采用。

## 任务1+2：19 行逐行更正（全部 return **0x1C2=450 帧**，无其他值）
- 统一语义：dispatch case 在 005B3086 置 `esi=edi+0xC8`，case 尾 `mov [esi+8],eax` ⇒ `[edi+0xD0]=TimeLeft=450`；`[edi+0xC8]=StartTime=CurrentFrame(0xA8ED84)`；函数头 005B307A–005B30A1 是倒计时门。⇒ **返回 450 帧轮询间隔（MissionClass::UpdateTimer，≈7.5s@60fps）**。
- NOP 列：`contig90`=body 后连续 0x90 字节（全 19 行均 10B）；`gap`=到本 19 集合下一行的字节间距减 6（审计口径：14 行 10B，4 行 26/58/26/42B，末行 n/a）。

| entry | 真名（mission id） | vslot / dispatch stub | const | NOP contig90 / gap | Timer 写回 |
|---|---|---|---|---|---|
| 005B2E20 | Mission_Harmless (23) | v130 / 005B30EA | 0x1C2 | 10 / 10 | 005B3104 [esi+8]=eax |
| 005B2E30 | Mission_Ambush (14) | v131 / 005B323E | 0x1C2 | 10 / 10 | 005B3258 [esi+8]=eax |
| 005B2E40 | Mission_Attack (1) | v132 / 005B3172 | 0x1C2 | 10 / 10 | 005B318C [esi+8]=eax |
| 005B2E50 | Mission_Capture (8; 同槽 17 Sabotage) | v133 / 005B330A | 0x1C2 | 10 / **26** | 005B3324 [esi+8]=eax |
| 005B2E70 | Mission_Guard (5; 同槽 6 Sticky) | v135 / 005B32E8 | 0x1C2 | 10 / 10 | 005B3302 [esi+8]=eax |
| 005B2E80 | Mission_AreaGuard (11) | v136 / 005B31D8 | 0x1C2 | 10 / 10 | 005B31F2 [esi+8]=eax |
| 005B2E90 | Mission_Harvest (10) | v137 / 005B31B6 | 0x1C2 | 10 / **58** | 005B31D0 [esi+8]=eax |
| 005B2ED0 | Mission_Return (12) | v141 / 005B31FA | 0x1C2 | 10 / 10 | 005B3214 [esi+8]=eax |
| 005B2EE0 | Mission_Stop (13) | v142 / 005B321C | 0x1C2 | 10 / 10 | 005B3236 [esi+8]=eax |
| 005B2EF0 | Mission_Unload (16) | v143 / 005B3260 | 0x1C2 | 10 / **26** | 005B327A [esi+8]=eax |
| 005B2F10 | Mission_Construction (18) | v145 / 005B312E | 0x1C2 | 10 / 10 | 005B3148 [esi+8]=eax |
| 005B2F20 | Mission_Selling (19) | v146 / 005B3150 | 0x1C2 | 10 / 10 | 005B316A [esi+8]=eax |
| 005B2F30 | Mission_Repair (20) | v147 / 005B3282 | 0x1C2 | 10 / 10 | 005B329C [esi+8]=eax |
| 005B2F40 | Mission_Missile (22) | v148 / 005B32C6 | 0x1C2 | 10 / 10 | 005B32E0 [esi+8]=eax |
| 005B2F50 | Mission_Open (24) | v149 / 005B32A4 | 0x1C2 | 10 / **42** | 005B32BE [esi+8]=eax |
| 005B2F80 | Mission_ParadropApproach (26) | v152 / 005B33D6 | 0x1C2 | 10 / 10 | 005B33F0 [esi+8]=eax |
| 005B2F90 | Mission_ParadropOverfly (27) | v153 / 005B33F8 | 0x1C2 | 10 / 10 | 005B3412 [esi+8]=eax |
| 005B2FA0 | Mission_Wait (28) | v154 / 005B345E | 0x1C2 | 10 / 10 | 005B3478 [esi+8]=eax |
| 005B2FB0 | Mission_SpyplaneApproach (30) | v155 / 005B341A | 0x1C2 | 10 / n/a | 005B3434 [esi+8]=eax |

## 命名证据（两条独立通道，不靠 YRpp 枚举名对应）
- 通道1：`005B30B2` 从 `[this+0xAC]` 取 mission id → `005B30C1 jmp [id*4+0x5B34E8]`；32 项表逐项解析出 stub→`call [vptr+disp]`→vslot；共享槽明确：133=(Capture,Sabotage)，135=(Guard,Sticky)。
- 通道2：镜像内 mission 名表 `0x816CAC[id]` 逐字符读出 Sleep/Attack/…/Spyplane Overfly；`005B3740`、`005B3760`、`005B3910`、`005B3950` 均引用该表（`EVIDENCE/probe_mission_strings.txt`）。
- 寄存器写入回溯：`005B3065 mov edi,ecx` 捕获 thiscall this；各 case `mov ecx,edi` 后虚调用；`005B3086` 是 store 前唯一 `esi` 写入（`EVIDENCE/register_trace.txt`）。
- 第三锚（非唯一依据）：RTTI `COL 0x805D28 +0xC → TD 0x817B18 → .?AVMissionClass@@`；ctor `005B2DE9` 写 vptr 007EDCC0；槽129..156 逐址落表（`EVIDENCE/vtable_mission.txt`）。
- 命名沿 S10-K1 既有约定：v133=Mission_Capture（亦 Sabotage）、v135=Mission_Guard（亦 Sticky）、AreaGuard/ParadropApproach 等去空格。

## 任务3：proved 穷举（EVIDENCE/task3_exhaustive.txt）
- B8 imm32 C3 的 26 行全部有归宿：004D27C0 原已证；005B2E10 基线已证；19 行本卡；006B1370/1380/8120/8130 为 K3 GetSize/WhatAmI 未重交；0070DD90 为反例。**无剩余 B8 行**。
- 非证行 439（∩atlas 438；RTTI anchor 422）；字符串_xref 扫描 63 行均为共享尾调用（EVA/SHP/rule key/source assert/Tip:*），无 mission-id↔name 闭合或第二命名通道，未升。
- 具体失败关闭：005B3970（序列化行为但 Save 名无独立绑定）、005B3A60（析构形但名无独立绑定）、005B3A10（仅布尔谓词）、005F5E80（继承字段例程）、0070DD90（imm=1 与 AircraftClass 冲突）、15 个 sub_ 占位无 RTTI anchor。
- 005B3060 的 Timer 门/派发体已复算为 MissionClass::UpdateTimer（`EVIDENCE/probe_timer_dispatch.txt`），但盘上已 [已证]，不重复入 delta。

## 交付/复算
- `coverage_delta.tsv`=19 行，无表头，grade 全 [已证]，evidence 全指 `EVIDENCE/mission_rows_corrected.txt`；0 重复 entry/name、0 坏行。
- 合入模拟：proved 88→**107/526 (20.3422%)**，门槛 263 仍差 156；严格 named(S) 29→48。校验见 `EVIDENCE/validate_delta.txt`。
- 复跑：`work/baseline_recompute.py`、`work/prove_corrections.py`、`work/validate_delta.py`、`work/task3_exhaustive.py`、`work/verify_esi_trace.py`。
