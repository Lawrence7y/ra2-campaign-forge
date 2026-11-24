#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append §869: T6 was incomplete (1 of 21 loops); here is the corrected inventory."""
import io

LED = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

SEC = """
## §869 · **`0x006DD8B0` 的逐帧循环清单：实际 **21 条回边 / 20 个不同循环**，子代理只报了 1 个 —— 我重做并给出权威表**（2026-11-15 15:45）

> 来源：DeepSeek 子代理 `ds-t6-frame` 的产出**不完整**（`loops.tsv` 只有 1 行）。
> 我独立重扫该函数体的全部回边，得到下表。**这是本节的主要交付物。**

- **§869-1 [已证·子代理的产出不可用]**
  `ds-t6-frame` 的 `loops.tsv` 只登记 **1 个循环**（`0x006DDD9B ← 0x006DEA4D`，遍历 `BuildingClass`），
  且其 `cost_centres.tsv` 的全部 15 项 `per_frame_multiplicity` 都是 **1**。
  - 我实测该函数体内**回边 21 条**（`jl`/`jne`/`je`/`jns`/`jge`），构成 **20 个不同循环**（其中 2 条回边共用同一头 `0x006DDD9B`）。
  - ⇒ **它漏了 20 个循环中的 19 个**，其成本排序因此无意义（把"只在某个小循环里跑一次"当成了全帧一次）。
  - ⇒ 本条**不是**在指责模型：它的方法是"找 backward branch"（正确的方法），只是实现漏了。

- **§869-2 [已证·权威循环清单（我重扫，可复跑）]**
  扫描方式：从函数入口 `0x006DD8B0` 起严格解码 9,530 字节，收集所有目标 < 自身地址的跳转；
  对每个 `[head, back]` 区间，统计其中引用了哪些"数组 Count 全局"。
  | head | back | 指令数 | 区间内引用的 Count 全局 |
  |---|---|---:|---|
  | `0x006DDB0D` | `0x006DDB56` | 26 | **Infantry** |
  | `0x006DDC0C` | `0x006DDC60` | 29 | **Foot** |
  | `0x006DDC87` | `0x006DDCDB` | 29 | **Foot** |
  | `0x006DDCFB` | `0x006DDD66` | 36 | **Techno** |
  | **`0x006DDD9B`** | `0x006DEA4D` | **1020** | **Building** |
  | `0x006DDD9B` | `0x006DEA7D` | 1034 | **Building** |
  | `0x006DDF09` | `0x006DDF54` | 27 | Building |
  | `0x006DDF79` | `0x006DDFC8` | 28 | Building |
  | `0x006DDFED` | `0x006DE03D` | 28 | Building |
  | `0x006DE3DA` | `0x006DE3FB` | 10 | — |
  | `0x006DE7C6` | `0x006DE7FE` | 19 | — |
  | `0x006DEFC7` | `0x006DF040` | 38 | Building |
  | `0x006DF06B` | `0x006DF083` | 9 | — |
  | `0x006DF0B2` | `0x006DF0D6` | 16 | — |
  | `0x006DF0FF` | `0x006DF126` | 14 | **Trigger** |
  | `0x006DF17C` | `0x006DF19C` | 11 | **Trigger** |
  | `0x006DF4C7` | `0x006DF50A` | 23 | **ParticleSystem** |
  | `0x006DF5EB` | `0x006DF62E` | 29 | — |
  | `0x006DF5F3` | `0x006DF611` | 14 | — |
  | `0x006DF64F` | `0x006DF661` | 5 | — |
  | `0x006DF72B` | `0x006DF768` | 22 | Building |

- **§869-3 [已证·结构性结论]**
  | 遍历的数组 | 循环数 |
  |---|---:|
  | `BuildingClass` | **7**（含一个 1020 指令的主循环 + 6 个小区间） |
  | `FootClass` | **2** |
  | `TriggerClass` | **2** |
  | `InfantryClass` | 1 |
  | `TechnoClass` | 1 |
  | `ParticleSystemClass` | 1 |
  | 无数组（局部/区间循环） | 6 |
  - ⇒ **没有 `UnitClass` 循环**，也**没有 `AircraftClass` / `HouseClass` 循环**。
  - ⇒ 这**修正了 §853-3 的表述**：那里说主循环"遍历六种不同类型数组"。更准确的说法是：
    **它遍历 Building / Foot / Infantry / Techno / Trigger / ParticleSystem 六种，
    但 `UnitClass` 不单独遍历** ——因为载具本身就是 `FootClass`，已被两个 Foot 循环覆盖。
  - ⇒ 对 ① 卡顿的直接含义：**每帧对每个 `BuildingClass` 实例要跑 7 个循环区间**，
    而对 `FootClass` 只有 2 个。若某局建筑很多、单位不多，逐帧开销仍可能由建筑侧主导。
    （这是**结构观察**，不是性能结论——没有计时数据。）

- **§869-4 [未证·如实登记]**
  1. **嵌套关系未解析**：`0x006DDF09`/`0x006DDF79`/`0x006DDFED`/`0x006DEFC7`/`0x006DF72B`
     在指令地址上都**落在主循环 `0x006DDD9B..0x006DEA4D` 区间内**，因此**很可能是主循环体内的内层循环**
     （即"建筑 × 建筑"或"建筑 × 触发"的嵌套）。我**没有**做嵌套深度判定。
  2. **`[virt]` 虚调用未解析**：`loops.tsv` 里标了 `[virt]@0x006DDF44` / `[virt]@0x006DE73C` /
     `[virt]@0x006DE769` 三处，**我未解析它们的 vtable 槽**。
  3. **成本排序未重做**：既然循环数从 1 变 21，任何基于"multiplicity × size"的排序都必须重算。
     **本轮没有重做**，因此 §869 **不提供成本排名**。
  4. 未验证 `0x006DD8B0` 的全部 21 条回边中是否有属于**内联的其他函数**（编译期内联会把别处的循环带进来）。

- **§869-5 [已证·复跑方法]**
  ```
  从 0x006DD8B0 起严格解码 9530 字节（capstone, 32-bit, 不加 skipdata）
  收集 mnemonic 以 'j' 开头且 op_str 为 '0x...' 且目标 < 自身地址的指令 => 回边
  对每条 (head, back)，在 [min(head,back), max(head,back)] 内统计含 '0x<CountVA>' 的指令
  ```
  数组 Count 全局：`Trigger 0xA8EAF8`、`Foot 0x8B3DD0`、`Unit 0x8B4118`、`Infantry 0xA83DF8`、
  `Aircraft 0xA8E3A0`、`Building 0xA8EB50`、`Techno 0xA8EC88`、`House 0xA80238`、
  `ParticleSystem 0xA80218`、`Abstract 0xB0F730`、`Bullet 0xA8ED50`、`Anim 0xA8E9B8`。
"""

P = LED
s = io.open(P, encoding="utf-8", newline="").read()
if "## §869 ·" in s:
    raise SystemExit("REFUSE: §869 already present")
s = s.rstrip("\n") + "\n" + SEC
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
bad = [(i, hex(ord(c))) for i, c in enumerate(s) if ord(c) < 32 and c not in "\n\t"]
print("appended §869; size=%d; control chars=%d" % (len(s.encode("utf-8")), len(bad)))
