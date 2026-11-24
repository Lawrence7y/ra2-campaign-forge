# LAYOUT.md — S10 Mission 虚槽语义 / GetSize / 字段增量（S10-K2）

> 目标 `gamemd.exe` SHA `73201CC0…F67476`，ImageBase `0x400000`，**只读字节通道**。全部由 `work/*.py` 独立重取，`capstone skipdata=True`（实测 .text 1,392,592 指令），vtable 定界从 `.rdata` 的 COL/`vtable[-1]`/表间边界做（纪律 7），**未用 atlas 边界反推**；类名只认 `COL+0xC→TD+8`（读不到 fail-closed）。`function_atlas.tsv` 仅用于 T4 的函数区间包含（边界来源），不用于发现。

## 1 · RTTI 与主 vtable 定界（`.rdata`，实测）

| 类（TD 名逐字符核对） | off=0 主 VT | 槽数 | end-delim | COL | TD |
|---|---|---|---|---|---|
| AbstractClass | `0x7E1F50` | 24 | noncode | `0x7FB118` | `0x8177C8` |
| ObjectClass | `0x7EF060` | 122 | noncode | `0x807448` | `0x817AF8` |
| MissionClass | `0x7EDCC0` | **157** | noncode | `0x805D28` | `0x817B18` |
| TechnoClass | `0x7F4960` | 309 | code-cont | `0x80C058` | `0x817B58` |
| FootClass | `0x7E8C94` | 341 | code-cont | `0x800948` | `0x817B78` |
| InfantryClass | `0x7EB058` | 343 | code-cont | `0x8033B8` | `0x825508` |
| AircraftClass | `0x7E22A4` | 341 | code-cont | `0x7FB4C0` | `0x817B90` |
| BuildingClass | `0x7E3EBC` | 322 | code-cont | `0x7FC360` | `0x818D60` |
| UnitClass | `0x7F5C70` | 344 | code-cont | `0x80CC68` | `0x842D80` |
| FoggedObjectClass | `0x7E8B38` | 25 | noncode | `0x800768` | `0x822438` |

- MissionClass 157 槽 = v[0..156]；**Mission 处理槽 = v[129..156]（最后 28 槽，disp 0x204..0x270）**。与父类逐槽对齐：Object==Mission 21/24（前 24 槽），ObjectClass 122 槽止于 v[121] ⇒ 派发槽在 MissionClass 自有区（v129+），**不是按"槽 12/65 惯例"猜出**（S11-K2 裁定已守）。
- 派生大 vtable 的 "code-cont" 是 capstone `maxn=400` 上界内连续 code pointer，未到表尾；但不影响 v129..v156（远在内）。

## 2 · T2 逐槽表：v[129..156] 语义（派发 call-context 为硬依据）

语义依据 = ②该槽被调用的上下文：派发表 `0x5B34E8` 32 项 → stub `call [vptr+disp]`（`ff 9x disp32`），disp/4 = 槽号，mission id = 表下标。基线先测：裸 `B8 imm32 C3` 全 .text 666（严格）/837（后随任意 ret），16B 对齐起点 36.6% ⇒ 单一字节形态无鉴别力，必须叠加派发槽锚定。

| 槽 | disp | Mission(派发映射) | 有实现的类:地址 | 全桩? | 分级 |
|---|---|---|---|---|---|
| v[129] | 0x204 | 0:Sleep;3:QMove;29:Attack Move | (全桩: `0x5B2E10` 等 7 类同址) | YES | [已证] |
| v[130] | 0x208 | 23:Harmless | (全桩: `0x5B2E20`) | YES | [已证] |
| v[131] | 0x20C | 14:Ambush | (全桩: `0x5B2E30`) | YES | [已证] |
| v[132] | 0x210 | 1:Attack | Aircraft `0x417FE0`, Building `0x44ACF0`, Foot `0x4D4DC0`, Infantry `0x51F3E0`, Unit `0x7447A0`(jmp→`0x4D4DC0`) | no | [已证] |
| v[133] | 0x214 | 8:Capture;17:Sabotage | Air/Foot/Inf/Unit `0x4D4B20`(共用), Building `0x44B760`(jmp→桩) | no | [已证] |
| v[134] | 0x218 | 9:Eaten | Air/Foot/Inf/Unit `0x4D4CB0`(共用) | no | [已证] |
| v[135] | 0x21C | 5:Guard;6:Sticky | Air `0x41A5C0`, Building `0x4496B0`, Foot `0x4D5070`, Infantry `0x51F620`, Unit `0x740810` | no | [已证] |
| v[136] | 0x220 | 11:Area Guard | Air `0x41A940`, Building `0x449A40`(jmp→v135), Foot `0x4D6AA0`, Infantry `0x51F640`, Unit `0x744100` | no | [已证] |
| v[137] | 0x224 | 10:Harvest | Infantry `0x522E70`, Unit `0x73E5E0`（Air/Foot/Building 用桩） | no | [已证] |
| v[138] | 0x228 | 15:Hunt | Air `0x414A80`, Foot `0x4D5350`, Infantry `0x51F540`, Unit `0x73EFC0` | no | [已证] |
| v[139] | 0x22C | 2:Move | Air `0x4166C0`, Foot `0x4D4200`, Infantry `0x51F660`, Unit `0x740A90` | no | [已证] |
| v[140] | 0x230 | 4:Retreat | Air `0x415A50`, Foot/Inf/Unit `0x4DA2C0` | no | [已证] |
| v[141] | 0x234 | 12:Return | (全桩: `0x5B2ED0`) | YES | [已证] |
| v[142] | 0x238 | 13:Stop | (全桩: `0x5B2EE0`) | YES | [已证] |
| v[143] | 0x23C | 16:Unload | Air `0x4151E0`, Building `0x44D880`, Infantry `0x51F6E0`, Unit `0x73D630` | no | [已证] |
| v[144] | 0x240 | 7:Enter | Air `0x419C80`, Foot/Inf/Unit `0x4D9290` | no | [已证] |
| v[145] | 0x244 | 18:Construction | Building `0x449A50` | no | [已证] |
| v[146] | 0x248 | 19:Selling | Building `0x449C30` | no | [已证] |
| v[147] | 0x24C | 20:Repair | Building `0x44B780`, Unit `0x740EF0` | no | [已证] |
| v[148] | 0x250 | 22:Missile | Building `0x44C980` | no | [已证] |
| v[149] | 0x254 | 24:Open | Building `0x44E440` | no | [已证] |
| v[150] | 0x258 | 21:Rescue | Air/Foot/Inf/Unit `0x4DDF90` | no | [已证] |
| v[151] | 0x25C | 25:Patrol | Air `0x417300`, Foot/Inf `0x4D4280`, Unit `0x740B10` | no | [已证] |
| v[152] | 0x260 | 26:Paradrop Approach | Aircraft `0x4158E0` | no | [已证] |
| v[153] | 0x264 | 27:Paradrop Overfly | Aircraft `0x415960` | no | [已证] |
| v[154] | 0x268 | 28:Wait | (全桩: `0x5B2FA0`) | YES | [已证] |
| v[155] | 0x26C | 30:Spyplane Approach | Aircraft `0x4155F0` | no | [已证] |
| v[156] | 0x270 | 31:Spyplane Overfly | Aircraft `0x4157C0` | no | [已证] |

完整逐槽原始 dump（含每槽各 7 类首 3 指令）见 `EVIDENCE/t2_mission_slots.txt`；最终判表 `EVIDENCE/t2_final_slots.txt/.json`；派发表 32 项与 stub call 字节 `EVIDENCE/t2_dispatch.txt`。

### 2.1 已入账数字逐条落地（停机核验通过）

- **桩步长纠正**：base stub = `B8 C2 01 00 00 C3`（`mov eax,0x1C2;ret`）+ nop，共 **28 处**，从 `0x5B2E10` 到 `0x5B2FC0`，**步长 0x10**（S10-K1 写"每 0x10B"是错的，已纠）。
- **全桩槽 6 个**：v129/v130/v131/v141/v142/v154 ⇒ 对应 **8 个全桩 Mission**：Sleep(0)、QMove(3)、Return(12)、Stop(13)、Ambush(14)、Harmless(23)、Wait(28)、Attack Move(29)（Sleep/QMove/Attack Move 共用 v129）。与台账 §965 名单逐字吻合。
- **有实现槽 22/28**：v132..v140、v143..v153、v155、v156（上表 "no" 行）。
- **有实现 Mission 24/32**：32 − 8 全桩 = 24（id 1,2,4,5,6,7,8,9,10,11,15,16,17,18,19,20,21,22,24,25,26,27,30,31）。
- **196 单元 = 桩 144 / 非桩 52 / 去重 43**：须用 S10-K1 原始 7 表（MissionClass + **RadioClass `0x7F0508`** + Techno/Foot/Infantry/Aircraft/Building，每表 v129..156）复算才精确闭合（我独立改用 UnitClass 得 133/63/49，**不采**，见 DISAGREE D2）；`work/verify_ledger.py` 用 RadioClass 得 **196/144/52/43** 完全一致。⚠️ **43 = 非桩入口地址数，不是"有实现的 Mission 数"**（台账 §965）。

## 3 · T3 GetSize 双点闭合（不假定槽 12，三重佐证）

基类共用桩 `0x4C9150`（`33 C0 C3`）**不是真 GetSize**。v[11](WhatAmI) 与 v[12](size) 同形 `B8 imm32 C3`，靠「slot 值 + 工厂分配点 + ctor 写 vtable 上界」三重闭合：

| 类 | A: v[12] imm | B: 工厂 push size → new `0x7C8E17` → ctor 写 VT | 闭包 |
|---|---|---|---|
| AircraftClass | `B8 D8 06…C3`=0x6D8 | `push@0x6C373C 68 D8 06 00 00` → ctor `0x413D20` 写 `0x413D89` | ✓ |
| BuildingClass | `B8 20 07…C3`=0x720 | `push@0x6C35BC 68 20 07 00 00` → ctor `0x43B740` 写 `0x43B9FC` | ✓ |
| InfantryClass | `B8 F0 06…C3`=0x6F0 | `push@0x6C38BC 68 F0 06 00 00` → ctor `0x517A50` 写 `0x517ACE` | ✓ |
| UnitClass | `B8 E8 08…C3`=0x8E8 | `push@0x6C343C 68 E8 08 00 00` → ctor `0x7353C0` 写 `0x73543C` | ✓ |
| FoggedObjectClass | `B8 78 00…C3`=0x78 | `push@0x6C5FBC 6A 78`（**imm8**）→ ctor `0x4D08B0` 写 `0x4D090B` | ✓ |

- **§972 陷阱复现**：4/5 用 `68 imm32`，FoggedObject 用 `6A imm8` — 只扫 imm32 会漏。
- **同形风险实证**：v[11]=WhatAmI 亦为 `B8 imm32 C3`（Aircraft=2, Building=6, Infantry=0xF, Unit=1, FoggedObject=0x3D），与 v[12] 仅靠槽号区分 ⇒ 纯字节扫描取错槽风险实存，本卡按 `.rdata` 定槽后取 v[12]。
- 排除：MissionClass/ObjectClass/TechnoClass/FootClass/AbstractClass 的 v[11]=v[12]=`0x4C9150`（桩），无真实尺寸。
- 证据：`EVIDENCE/t3_getsize_raw.txt/.json`、`t3_getsize_closure.txt`、`t3_getsize_final.txt/.json`。

## 4 · T4 字段布局增量（3 个单边字段补另一侧）

扫描 MissionClass 自身方法区 `0x5B2D00..0x5B3B00`（atlas 仅作函数边界），`call/jmp [reg+disp]` 虚槽调用**剔除 34 处**（显式计数，不计入数据读点）；全 .text 广扫按 byte/dword 宽度 + this-alias 寄存器过滤：

| 字段 | 已入账 | 本卡增量 | 结论 |
|---|---|---|---|
| +0xB8 (byte) | 6 写 / 0 读 | 补 1 读点 `0x74431F`（fn `0x744270`=UnitClass::slot128，`mov al,[esi+0xb8]`；前文 `cmp eax,5`/`cmp eax,1` + target `[esi+0x2b4]` mission 上下文；`+0x184` 处是虚槽 call 已剔除） | 读点带 mission 语义上下文，**但该读点在派生类 UnitClass 方法而非 MissionClass 自身方法** ⇒ 记 [静态推断] 升级候选，严格"同类双支撑"仍不足 → 保留 [未证] 备注 |
| +0xCC (dword) | 2 写 / 0 读 | 广扫 109 dword 读点全在无关类（`0x409A5D`/`0x41E68C`…），无 MissionClass 归属 | **补不出，保留 [未证]** |
| +0x6C (dword) | 0 写 / 1 读 (`0x5B30A7` in MissionClass::AI) | 广扫 80 dword 写点全在无关类 ctor（`0x5F3919` ObjectClass ctor 等），跨类陷阱禁止套用 | **补不出，保留 [未证]** |

- 字段偏移不定语义：未把 `+0x94`/`+0x184`/`+0x80` 跨类套用；本卡所有字段结论只字节层。证据：`EVIDENCE/t4_fields.txt/.json`、`t4_fields_broad.txt/.json`。

## 5 · 交叉说明

- 基线（先测后 claim）：裸 `B8 imm32 C3`=666 strict / 837 后随 ret；16B 对齐起点 36.6%；`ret 0xC` 全 .text 指令级 1651（与 §969 的 672 定义/范围不同，见 DISAGREE D4）。均说明"单一形态 N/N"不成立。
- 双通道：RTTI/vtable/派发表完全不依赖 `function_atlas.tsv`；仅 T4 函数区间用 atlas 作边界（非发现）。未改游戏文件、未写台账、未 git commit。
