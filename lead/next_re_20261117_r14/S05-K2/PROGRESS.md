# S05-K2 · PROGRESS.md — S05 对象模型深化（读点修复 + 字段/槽增量）

> 卡号 S05-K2｜2026-11-18｜目标只读 `gamemd.exe` SHA `73201CC0…F67476`（已核，未改）｜写域仅本卡目录 + `_ghidra\S05-K2\`
> 一句话：**5 字段读点口径混杂已修（虚槽调用显式剔除，5/5 恢复 [已证]）；字段双支撑 8→10；GetSize 4 具体类双点闭合 + 6 抽象桩裁定（4→10 类全覆盖）；S05 delta 24 行全 [已证]。**

## 结论表

| 项 | 结论 | 分级 | 证据 |
|---|---|---|---|
| T1 TARGETS | S05∩atlas(大小写归一) = **643**；named_L 520(80.87%)/named_S 519(80.72%)/proved **170**(26.44%)；距 50%(322) 差 **152** | [已证] | `TARGETS.tsv`、`work/t1_stats.json` |
| T2 读点修复 | 5 字段虚槽调用剔除数 1328/358/131/197/40；旧读=数据读+lea+vcall 逐字段精确成立 | [已证] | `EVIDENCE/t2_field_rescan.json` |
| T2 分级回升 | 5/5 字段（+0x10/20/74/80/94）恢复 [已证] | [已证] | `EVIDENCE/t2_field_rescan.json`、`LAYOUT.md` §1 |
| T2 +0x80 第三值 | byte 写 **179**（=R14，≠S07 181），79 atlas 函数 +38 空洞写 ⇒ 真函数数 >79 | [已证] | `EVIDENCE/t2_080_focused.json` |
| T3 新字段 | `+0x674` loco 指针（ctor 8 写/300 读）、`+0x140` 当前武器阶段（写点=SetCurrentWeaponStage） | [已证] | `EVIDENCE/t3_targeted_fields.json` |
| T4 GetSize | 4 具体类 v[12] 双点闭合；v[11] WhatAmI 值 {6,1,15,2} 与 §2.4 比较集互证；6 抽象桩 0x4C9150 | [已证] | `EVIDENCE/t4_getsize_slots.json` |
| T5 vslot 语义 | 24 个 S05 [静态推断] vslot 函数据「this 回溯 + ≥3 已知字段数据访问」升 [已证] | [已证]/见 UNKNOWNS | `EVIDENCE/t5_fieldslot_final.json` |
| delta | 24 行全 [已证]（16 Aircraft + 2 Foot + 3 Techno + 2 Building + 1 Object） | — | `coverage_delta.tsv` |
| 停机核验 | 卡面 prove=138/atlas=638 为 M2 前旧值；盘上现值 170/643 ⇒ 按纪律 9 用盘上值，不凑数（见 DISAGREE D1） | — | `COVERAGE/PANEL.md` S05 行 |

## 给审计员的 3 个核心数字（可独立复算）

1. **5 字段虚槽调用剔除数**：`python work/t2_field_rescan.py`。该脚本分类口径与 S05-K1 逐字对齐（`old_reads` 列 = S05-K1 `total_reads` 全 8 字段精确相等）后再拆 vcall/lea。锚点：`+0x81` vcall=0 ⇒ 数据读=238（审计"精确吻合 238"）；`+0x1AC` vcall=86（审计 20→86）。5 字段剔除数 = 1328/358/131/197/40。等式 旧读=数据读+lea+vcall 逐字段成立。

2. **GetSize 槽锚定**：`python work/t4_getsize_slots.py`。从 `.rdata` vtable 读全槽，`B8 imm32 C3` 命中逐槽列出（**显式展示 v[11] 与 v[12] 同形**，避免取错槽）；4 具体类 imm=0x720/8E8/6F0/6D8，各 13/11/11/N 个 `68 imm→call 0x7C8E17` 分配点；6 抽象类 v[12]=0x4C9150=`33 C0 C3` 桩。WhatAmI 值 {6,1,15,2} 与 R14_COMMON §2.4 比较集独立吻合。

3. **24 行 delta 的 this-register 证据**：`python work/build_delta_final.py` + `work/verify_delta_thiscall.py`。每行：S05 `[静态推断]` vslot 函数 → 序言 `mov reg,ecx` 回溯 this → 该函数体内对已知字段（+0x10/20/74/80/81/94/21C/674）的数据访问 ≥3（vcall/lea/esp 剔除）。`EVIDENCE/t5_fieldslot_final.json` 逐行给访问地址与指令。

## 交付与纪律自检

- 交付：`PROGRESS.md`/`TARGETS.tsv`/`LAYOUT.md`/`UNKNOWNS.md`/`DISAGREE.md`/`coverage_delta.tsv`(24)/`EVIDENCE/`(8)/`work/`(11)。
- 双通道非同源：类名/槽数来自 RTTI(COL+0xC→TD+8) + `.rdata` 定界；读点/字段来自 `.text` capstone skipdata 重扫；GetSize 来自 vtable imm + 分配点 imm 两处独立；均不依赖 atlas entry+size 取数。
- 先测基线：+0x81(0 vcall)/+0x1AC(86 vcall) 双锚点自证剔除口径，未写"N/N"空判据。
- 字段偏移未定语义：+0x94 只算 ObjectClass 族；`call [reg+disp]` 全列剔除数；ebp=this 陷阱（0x636595）沿用 S05-K1 已核结论。
- 槽号不假定（§981）：v[11]/v[12] 全槽穷举 + 双点闭合；未用固定槽 12，未把 0x4C9150 当真 GetSize。
- 类名只认 RTTI；本卡未据字段名猜类；升级只用字节级证据。
- 未改 `gamemd.exe`/`COVERAGE\coverage.tsv`；未写主台账；未 git commit/push；未跑真机。
