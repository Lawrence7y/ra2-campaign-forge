# S10-K3 · PROGRESS（Mission 子系统严格 proved 提升）
> 目标 ra2youli\gamemd.exe，自算 SHA-256 73201CC0…F67476；Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26；未用 Ghidra；只写本卡目录。

## 结论表
| entry | 结论（证据要点） | 级别 | 证据路径 |
|---|---|---|---|
| 全局 | 盘上 S10 atlas 交集 526、proved 88、PANEL named(L)=511；门槛 263（非卡面约 513 的 257） | [已证] | EVIDENCE/baseline_recompute.txt |
| 005B2E20 | Mission 默认 no-op：v130/dispatch 005B30EA；body b8c2010000c3 +10×90；caller store [esi+8] | [已证] | EVIDENCE/mission_noop_s10.txt |
| 005B2E30 | Mission 默认 no-op：v131/dispatch 005B323E；同一精确 body/ret/nop/store 判据 | [已证] | EVIDENCE/mission_noop_s10.txt |
| 005B2E40 | Mission 默认 no-op：v132/dispatch 005B3172；同一精确 body/ret/nop/store 判据 | [已证] | EVIDENCE/mission_noop_s10.txt |
| 005B2E50 | Mission 默认 no-op：v133/dispatch 005B330A；mission 8/17 复用；同一 body/store 判据 | [已证] | EVIDENCE/mission_noop_s10.txt |
| 005B2E70 | Mission 默认 no-op：v135/dispatch 005B32E8；mission 5/6 复用；同一 body/store 判据 | [已证] | EVIDENCE/mission_noop_s10.txt |
| 005B2E80 | Mission 默认 no-op：v136/dispatch 005B31D8；body 至 ret 打完，10 NOP 到下一桩 | [已证] | EVIDENCE/mission_noop_s10.txt |
| 005B2E90 | Mission 默认 no-op：v137/dispatch 005B31B6；同一精确 body/ret/nop/store 判据 | [已证] | EVIDENCE/mission_noop_s10.txt |
| 005B2ED0 | Mission 默认 no-op：v141/dispatch 005B31FA；同一精确 body/ret/nop/store 判据 | [已证] | EVIDENCE/mission_noop_s10.txt |
| 005B2EE0 | Mission 默认 no-op：v142/dispatch 005B321C；同一精确 body/ret/nop/store 判据 | [已证] | EVIDENCE/mission_noop_s10.txt |
| 005B2EF0 | Mission 默认 no-op：v143/dispatch 005B3260；同一精确 body/ret/nop/store 判据 | [已证] | EVIDENCE/mission_noop_s10.txt |
| 005B2F10 | Mission 默认 no-op：v145/dispatch 005B312E；同一精确 body/ret/nop/store 判据 | [已证] | EVIDENCE/mission_noop_s10.txt |
| 005B2F20 | Mission 默认 no-op：v146/dispatch 005B3150；同一精确 body/ret/nop/store 判据 | [已证] | EVIDENCE/mission_noop_s10.txt |
| 005B2F30 | Mission 默认 no-op：v147/dispatch 005B3282；同一精确 body/ret/nop/store 判据 | [已证] | EVIDENCE/mission_noop_s10.txt |
| 005B2F40 | Mission 默认 no-op：v148/dispatch 005B32C6；同一精确 body/ret/nop/store 判据 | [已证] | EVIDENCE/mission_noop_s10.txt |
| 005B2F50 | Mission 默认 no-op：v149/dispatch 005B32A4；同一精确 body/ret/nop/store 判据 | [已证] | EVIDENCE/mission_noop_s10.txt |
| 005B2F80 | Mission 默认 no-op：v152/dispatch 005B33D6；同一精确 body/ret/nop/store 判据 | [已证] | EVIDENCE/mission_noop_s10.txt |
| 005B2F90 | Mission 默认 no-op：v153/dispatch 005B33F8；同一精确 body/ret/nop/store 判据 | [已证] | EVIDENCE/mission_noop_s10.txt |
| 005B2FA0 | Mission 默认 no-op：v154/dispatch 005B345E；同一精确 body/ret/nop/store 判据 | [已证] | EVIDENCE/mission_noop_s10.txt |
| 005B2FB0 | Mission 默认 no-op：v155/dispatch 005B341A；同一精确 body/ret/nop/store 判据 | [已证] | EVIDENCE/mission_noop_s10.txt |
| 006B1370 | SlaveManagerClass::GetSize：b864000000c3=0x64；factory 006C0BBC 6A 64 → new 007C8E17 → ctor 006AF360 写 vptr 007F31C8 | [已证] | EVIDENCE/getsize_s10.txt |
| 006B1380 | SlaveManagerClass::WhatAmI：b848000000c3=0x48=SlaveManager；off0 slot11，slot12 GetSize 闭合定界，TD 名逐字符 | [已证] | EVIDENCE/whatami_s10.txt |
| 006B8120 | SpawnManagerClass::GetSize：b874000000c3=0x74；factory 006C0A3C 6A 74 → new 007C8E17 → ctor 006B6EA0 写 vptr 007F3650 | [已证] | EVIDENCE/getsize_s10.txt |
| 006B8130 | SpawnManagerClass::WhatAmI：b841000000c3=0x41=SpawnManager；off0 slot11，slot12 GetSize 闭合定界，TD 名逐字符 | [已证] | EVIDENCE/whatami_s10.txt |
| 全局 | 26 行 B8 imm32 C3 全部归档：2 原已证、19 no-op、2 GetSize、2 WhatAmI、1 反例 0070DD90；23 行 delta/0 坏行/0 重复 entry/0 重复 name | [已证] | EVIDENCE/semantic_census_s10.txt；EVIDENCE/validate_delta.txt |

## 核心数字
- 卡前：S10 coverage 528 行；∩atlas 526（大小写归一）；proved 88（16.73%）；PANEL named(L)=511；门槛 ceil(526/2)=263，尚差 175。
- 交付：23 行 [静态推断]→[已证]（19 Mission no-op + 2 GetSize + 2 WhatAmI）；合入模拟 proved 111/526 = 21.1027%，仍差 152。
- 严格命名口径：排除 sub_/Class::sub_/Class::slotN/Class::vslotN 后，named(S) 29→52；本卡未把任何 slot 名当语义。
- 未用“在虚表里”单独升级；所有 RTTI 类名经 COL+0xC→TD+8 内联串读取，失败即不升。

## 复算
1. `python work/baseline_recompute.py > EVIDENCE/baseline_recompute.txt`
2. `python work/rebuild_all_rtti.py && python work/candidate_census.py && python work/prove_semantics_s10.py`
3. `python work/nonupgraded_dump.py && python work/validate_delta.py > work/validate_delta.log`
