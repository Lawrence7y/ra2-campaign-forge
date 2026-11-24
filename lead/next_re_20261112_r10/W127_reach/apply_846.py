#!/usr/bin/env python3
"""Append §846: atlas milestone (1) -- class atlas v1 + inherited-map corrections."""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

extra = r"""
## §846 · **全程序逆向 里程碑(1)：类图谱 v1（1,219 虚表 / 954 类 / 955 主表）；继承来的 RTTI 表查出 87 个假阳性**（2026-11-15 21:40）

- **§846-1 [已证·动机]** 本会话新目标是把"整个 RA2 逆向"落成可判定完成度的知识库。
  里程碑(1) = 全量类图谱。原计划直接沿用既有 `_lead_rtti_map.json`（1,305 虚表），
  **但一次质检发现它不可直接采信**，于是改为**从镜像重建**。

- **§846-2 [已证·继承表的两个真缺陷（重建后 diff 得出）]**
  | 缺陷 | 数量 | 证据 |
  |---|---:|---|
  | "虚表地址"落在 **`.text`** 段内 | **87 / 1305** | 真虚表不可能在代码段；这些条目的 `+0x2C` 槽读出 `0xD00D8B00`、`0x24448B12` 这类垃圾 |
  | 模板类名**被截断** | **9** | 例：继承 `?$VectorClass@V?$DistributionObject@PAVCellClass@@@` vs 重建 `…@@@?$DiscreteDistributionClass@VCellClass@@@@@@` |
  - ⇒ 台账 §646-2 引用的"由 COL 反查出的 vtable 起点 **1,305** 个"这个数字**偏高**，正确值约 **1,219**
    （重建 1,219；与继承表交集 1,217；继承表独有 88 条中 87 条是 `.text` 假阳性）。

- **§846-3 [已证·重建方法（标准 MSVC，可复跑）]** `W130_atlas\vtables_rebuild.py`
  1. 扫 `.rdata`/`.data` 的**每 4 字节**（且限于 `SizeOfRawData` 内有文件字节的范围），把该 dword 当候选 COL 指针；
  2. COL 自洽判据：`pTypeDescriptor`（COL+0x0C）在 `.rdata/.data`，且 `[pTD+8..]` 以 `.?AV` 或 `.?AU` 开头；
  3. **虚表起点 = 该 dword 的位置 + 4**（因为 `vtable[-1]` 存 COL 指针）；
  4. 校验槽序列。

- **§846-4 [已证·★ 本镜像的虚表是 `{COL, vtable, COL, vtable, …}` 交错排布]**
  ```asm
  0x007E1F20  0x007FAFD8   ; ← 下一张表 0x007E1F24 的 COL
  0x007E1F24  0x00410590   ; vtable（1 槽）
  0x007E1F28  0x007FAFF0   ; ← 下一张表 0x007E1F2C 的 COL（COL.offset=0x8，即非主表）
  0x007E1F2C  0x00410580   ; vtable（1 槽）
  0x007E1F30  0x007FB008   ; ← COL
  0x007E1F34  0x004105E0   ; vtable（5 槽）
  ```
  - ⇒ **"每 8 字节一个条目、一半是 COL 指针"不是异常**，是 MSVC 的正常排布。
  - ⇒ 因此**槽数不能用"到下一个虚表起点的距离"来算**（会算成 1 槽）；正确终止判据是
    **"下一个 dword 是一个合法 COL 指针"**。这条是本轮才发现的方法要点。

- **§846-5 [已证·类图谱 v1 结果]**
  | 指标 | 值 |
  |---|---|
  | 候选虚表 | **1,219** |
  | 有 ≥2 个连续合法槽的虚表 | 1,018 |
  | 类名（去重） | **954** |
  | 主虚表（`COL.offset == 0`） | **955** |
  | 槽序列终止原因 | `next-col` 692 / `other` 230 / `data` 33（仅统计主表） |

- **§846-6 [已证·★ 槽数的内部一致性检验（方法正确性的强信号）]**
  | 类 | 主表槽数 | 继承关系 |
  |---|---:|---|
  | `TechnoClass` | **309** | 基类 |
  | `FootClass` | **340** | ← TechnoClass（+31） |
  | `UnitClass` | **345** | ← FootClass（+5） |
  | `AircraftClass` | **342** | ← FootClass（+2） |
  | `InfantryClass` | **344** | ← FootClass（+4） |
  | `BuildingClass` | **321** | ← TechnoClass（+12） |
  - ⇒ **每个派生类的槽数都严格大于其基类**，且 `FootClass` 的三个子类各只多 2–5 个。
    若槽计数是随机截断，不会出现这种单调结构。⇒ **槽计数方法可信**。
  - 这也是 §2.5"`BuildingClass` 主虚表 `0x007E3EBC`"的独立复核：重建同样给出 **0x007E3EBC，且 offset==0（主表）**。

- **§846-7 [未证·v1 的已知局限]**
  1. `941 个类中只 185 个`能解析出 WhatAmI —— 因为 **`+0x2C` 并非普遍是 `WhatAmI()`**：
     900 个主虚表在该槽指向普通方法（prologue `53`/`8B`/`56`/`8A`）。
     ⇒ **§629-2/§646-3 的"`+0x2C` = WhatAmI()"只在 `ObjectClass` 继承树上成立**，不是全局规律（见 §846-8）。
  2. 230 个主表的槽序列终止在 `other`（非代码非 COL），可能有个别表被截断或越界 1–2 槽；
     目前**没有独立方法交叉验证**这些表的精确槽数。
  3. 纯虚槽（值为 0）与 `_purecall` 目前**同等接受**，未区分。

- **§846-8 [已证·对既有结论的修正]** §629-2 写"`.rdata` 中 **69 个 vtable** 的槽 11（`+0x2C`）全部指向 `mov eax,N; ret` 且 N 唯一"，
  §646-3 据此建了 60+ 条 WhatAmI 阶梯表。**在该子集内是成立的**（本轮 5 个已知类 ID 全部复核通过：
  6=Building / 11=Cell / 36=Terrain / 8=Bullet / 15=Infantry），
  但**不能外推为"所有类都如此"**。⇒ 后续凡用 WhatAmI 反查类名，必须先确认该虚表在 `ObjectClass` 继承树上。

- **§846-9 [产物]** （均在 `W130_atlas\`，可复跑）
  | 文件 | 内容 |
  |---|---|
  | `vtables_rebuild.py` | 重建器（本节的 1,219 / 954 / 955 全部由它产出） |
  | `vtables_rebuilt.tsv` / `.json` | 每张虚表：vt / class / primary / col_offset / slots / terminator / section / col |
  | `class_atlas.py` + `class_atlas.tsv` | 早一版（基于继承表）的类图谱，保留作对照 |
  | `vtable_validity.py` + `vtable_validity.json` | 继承表质检（VALID 1001 / SUSPECT 217 / FALSE 87） |
"""

src = io.open(LEDGER, encoding="utf-8").read()
if "## §846" in src:
    sys.exit("ABORT: §846 already present")
n0 = len(src)
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (n0, len(back)))
for k in ("## §846", "1,219", "87 / 1305"):
    print("  %-12s %d" % (k, back.count(k)))
bad = [(hex(ord(c)), back.count(c)) for c in set(back) if ord(c) < 0x20 and c not in "\r\n\t"]
print("control chars:", bad)
