# S06-K4 UNKNOWNS

## U1 覆盖率缺口
- 盘上基线 103/848；本卡严格升级 23 行（22 字节闭合 + 1 行为级）=> 126/848 = 14.8585%。
- DoD 50% 门槛为 424；仍差 298 行。本卡不凑数，未把 vtable 槽归属当语义。

## U2 已穷举的允许类型 1/2
- `B8 imm32 C3`：覆盖集 23 行，其中 1 行原已 `[已证]`，非已证 22 行；22/22 均完成 WhatAmI 或 GetSize 证明并进入 delta。
- RTTI/COL/vtable 全镜像锚定 `B8 imm32 C3` 413 处，∩S06=23，非已证=22（与裸字节通道集合一致）。
- `B8 imm32 C2 04 00` 5 行非已证：不属于类型 1（要求 `C3`），也无完整行为级判据，未升。
- 行级穷举与计数：`EVIDENCE/candidate_census.txt`；脚本 `work/k4_rtti.py`、`work/k4_candidate_census.py`。

## U3 行为级宽扫（类型 3）
- 以已知锚点（+0x44 覆盖物/矿石类型、+0x11E 密度、0x5FDD20 类型->DVC 索引、0x485020 价值、0x487190 IncreaseTiberium、0x47C620 CanThisExistHere）扫描 S06 非已证行：42 个原始命中。
- 仅 `00483710` 同时满足：规则门控字节、`+0x44`->`0x5FDD20`、`+0x11C==0`、密度 `< [type+0xE4]`、`[type+0xB0] >= 1e-05`、以 `(typeIndex,1)` 调用 `0x487190`。证据：`EVIDENCE/growth_behavior.txt`。
- 其余 41 个原始命中仅具备字段访问/锚点调用，缺少“常量 + 写/读字段 + 调用者实参 + 被调语义”的完整闭环；按 fail-closed 保持原级。原始清单可由 `work/k4_behavior_probe.py` 复跑（42 个 entry）。
- 未尝试把 `0x80110`（屏幕矩形/贴图坐标候选）、`0x47EC90`/`0x5FC570`（占用链遍历候选）等升为语义，因 +0x11C 的精确语义仍是 `[静态推断]`，不能写成“占用判定”。

## U4 未使用/不足以升级的证据
- 仅 vftable 槽值直指（入口归属）：不作为语义证据（R14_COMMON §8.1 ⑬）。
- `TD+8` 当作指针读取：未使用；本卡按 `COL+0xC -> TD`，`TD+8` 内联 ASCII 名串读取，失败即 fail-closed。
- 未从 atlas `entry+size` 发现新入口；两通道发现均为裸字节形态与全 RTTI/COL/vtable 锚定。
