# S06-K4 PROGRESS（卡号 S06-K4）
> 目标 SHA-256 `73201CC0…F67476` 自算全值一致；纯静态；Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26；未用 Ghidra；写域仅 `S06_K4\`。
> 纪律 9：盘上复算 S06=848、∩atlas=848、proved=103、named_L=384（PANEL S06 行逐字一致）；50% 门槛=424。

## 结论表（每条均为 `[已证]`；证据路径相对本卡）
| entry | 语义名 | 证明类型 | 关键证据 | 证据路径 |
|---|---|---|---|---|
| 00483710 | CellClass::GrowTiberiumIfAllowed | 3 行为级 | 门控常量 + +0x44/+0x11C/+0x11E 读点 + 0x5FDD20/0x487190 调用 + 1e-5 常量 | EVIDENCE/growth_behavior.txt |
| 00487E60 | CellClass::WhatAmI | 1 WhatAmI |  → enum  + RTTI/slot11 定界 | EVIDENCE/whatami_proofs.txt |
| 00543A90 | IsometricTileClass::GetSize | 2 GetSize | b8b0000000c3 ↔ push 68b0000000 @ operator new | EVIDENCE/getsize_proofs.txt |
| 00543AA0 | IsometricTileClass::WhatAmI | 1 WhatAmI |  → enum  + RTTI/slot11 定界 | EVIDENCE/whatami_proofs.txt |
| 0054A140 | IsometricTileTypeClass::WhatAmI | 1 WhatAmI |  → enum  + RTTI/slot11 定界 | EVIDENCE/whatami_proofs.txt |
| 0054A150 | IsometricTileTypeClass::GetSize | 2 GetSize | b80c030000c3 ↔ push 680c030000 @ operator new | EVIDENCE/getsize_proofs.txt |
| 005FDF00 | OverlayClass::GetSize | 2 GetSize | b8b0000000c3 ↔ push 68b0000000 @ operator new | EVIDENCE/getsize_proofs.txt |
| 005FDF50 | OverlayClass::WhatAmI | 1 WhatAmI |  → enum  + RTTI/slot11 定界 | EVIDENCE/whatami_proofs.txt |
| 005FEF00 | OverlayTypeClass::WhatAmI | 1 WhatAmI |  → enum  + RTTI/slot11 定界 | EVIDENCE/whatami_proofs.txt |
| 005FEF10 | OverlayTypeClass::GetSize | 2 GetSize | b8bc020000c3 ↔ push 68bc020000 @ operator new | EVIDENCE/getsize_proofs.txt |
| 006B4F30 | SmudgeClass::GetSize | 2 GetSize | b8b0000000c3 ↔ push 68b0000000 @ operator new | EVIDENCE/getsize_proofs.txt |
| 006B4F40 | SmudgeClass::WhatAmI | 1 WhatAmI |  → enum  + RTTI/slot11 定界 | EVIDENCE/whatami_proofs.txt |
| 006B6130 | SmudgeTypeClass::WhatAmI | 1 WhatAmI |  → enum  + RTTI/slot11 定界 | EVIDENCE/whatami_proofs.txt |
| 006B6140 | SmudgeTypeClass::GetSize | 2 GetSize | b8a4020000c3 ↔ push 68a4020000 @ operator new | EVIDENCE/getsize_proofs.txt |
| 0071D300 | TerrainClass::WhatAmI | 1 WhatAmI |  → enum  + RTTI/slot11 定界 | EVIDENCE/whatami_proofs.txt |
| 0071E330 | TerrainTypeClass::WhatAmI | 1 WhatAmI |  → enum  + RTTI/slot11 定界 | EVIDENCE/whatami_proofs.txt |
| 0071E340 | TerrainTypeClass::GetSize | 2 GetSize | b8bc020000c3 ↔ push 68bc020000 @ operator new | EVIDENCE/getsize_proofs.txt |
| 007236E0 | TiberiumClass::GetSize | 2 GetSize | b828010000c3 ↔ push 6828010000 @ operator new | EVIDENCE/getsize_proofs.txt |
| 007236F0 | TiberiumClass::WhatAmI | 1 WhatAmI |  → enum  + RTTI/slot11 定界 | EVIDENCE/whatami_proofs.txt |
| 007286B0 | TubeClass::GetSize | 2 GetSize | b8c4010000c3 ↔ push 68c4010000 @ operator new | EVIDENCE/getsize_proofs.txt |
| 007286C0 | TubeClass::WhatAmI | 1 WhatAmI |  → enum  + RTTI/slot11 定界 | EVIDENCE/whatami_proofs.txt |
| 00763E00 | WaypointPathClass::GetSize | 2 GetSize | b840000000c3 ↔ push 6a40 @ operator new | EVIDENCE/getsize_proofs.txt |
| 00763E10 | WaypointPathClass::WhatAmI | 1 WhatAmI |  → enum  + RTTI/slot11 定界 | EVIDENCE/whatami_proofs.txt |

## 核心数字与复算
1. 基线：`S06_ROWS=848 ATLAS_INTERSECTION=848 GRADES=[已证]103/[静态推断]287/[未证]458`；门槛 424。复算 `python work/k4_validate.py` → `EVIDENCE/baseline_recompute.txt`。
2. 严格候选穷举：B8 imm32 C3 覆盖行=23，非已证=22（全部已升）；B8 imm32 C2 ret4 非已证=5（类型 1/2 不允许，未升）；RTTI 锚定 B8C3=413，∩S06=23，非已证=22。复算 `python work/k4_rtti.py && python work/k4_candidate_census.py`。
3. 行为级宽扫 42 个原始命中，仅 `00483710` 满足完整判据；其余 41 个未升（见 `UNKNOWNS.md`）。复算 `python work/k4_behavior_probe.py`。
4. 合入后：`DELTA_ROWS=23`，old grade 22 静态推断 + 1 未证，`NEW_PROVED=126/848=14.8585%`；重复 entry/name=0、bad=0。复算 `python work/k4_validate.py` → `EVIDENCE/validate_delta.txt`。
5. 无 `Class::slotN` / `Class::sub_XXXXXXXX` 名称进入 delta；未改主 coverage、未写台账、未改游戏文件、未 git commit。
