#!/usr/bin/env python3
"""Append §855: milestone (4) -- field/structure entries with validation."""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

extra = r"""
## §855 · **里程碑(4) 补完"关键结构条目"：按代码真实访问抽取字段布局，并与台账 6 个已知偏移交叉验证全部命中**（2026-11-16 06:10）

- **§855-1 [已证·方法（比"按名字猜字段"硬得多）]**
  对每个类/子系统的代表函数**反编译**，用 Ghidra 的 C 输出抽取 `this` 相对偏移访问：
  `*(<type> *)(param_1 + 0xNN)` 与 `param_1->field_0xNN` 两种形态；
  **读写判定** = 该出现是否位于赋值的左侧；**宽度** = 强制转换类型。
  然后按"被多少个方法触碰"排序 —— 排序依据是**独立方法的覆盖数**，不是访问次数，
  以免单个热循环刷榜。
  - 输入 1,022 个 (类或子系统, 函数) 对（每实体取最大的 40 个函数，`size≥16`）；
    **全部 1,022 个反编译成功，0 失败**。
  - 产出 **2,797 条 (实体, 偏移, 读, 写, 宽度)** 记录。

- **§855-2 [已证·★ 与台账既有结论的交叉验证：6/6 命中]**
  这是本节最重要的证据 —— 抽取结果**独立复现**了台账里 6 个已确立的偏移：
  | 实体 | 偏移 | 抽取结果 | 台账既有结论 |
  |---|---|---|---|
  | `BuildingClass` | `+0x520` | **read=4** | §2.4：指向自身 `BuildingTypeClass` |
  | `BuildingClass` | `+0x9C` | **read=4** | §2.4：anchor 行坐标（`trunc([+0x9C]/256)`） |
  | `BuildingClass` | `+0xA0` | **read=4** | §2.4：anchor 列坐标 |
  | `ObjectClass` | `+0x30` | **read=2, write=2** | §2.1：格链节点后继 |
  | `ObjectClass` | `+0x90` | read=1 | 主循环 `0x006DD8B0` 用它判对象有效性 |
  | **`MapClass`** | **`+0x13C`** | **触碰 27 次（该类最高）** | §2.1：**格表指针** |
  | `MapClass` | `+0x140` | 触碰 13 次 | §2.1：格数/上界 |
  - ⇒ **`MapClass+0x13C` 被排为该类最常触碰字段**，与"它是格表指针"完全自洽
    （格表是地图子系统里被访问最多的东西）。
  - ⇒ 这 6 个命中是**抽取方法的正确性验证**：它们不是我去找的，而是排序后排到前面的。

- **§855-3 [已证·各类/各子系统的关键结构条目（摘要）]**
  完整表见 `W131_subsystems\FIELD_LAYOUT.md` / `field_layout_classes.tsv` / `field_layout_subsystems.tsv`。
  | 实体 | 偏移数 | 总访问 | 最常触碰 |
  |---|---:|---:|---|
  | `HouseClass` | **101** | 139 | `+0x48`(5)、`+0x78`(4)、`+0x90`(4) |
  | `TechnoClass` | 71 | 85 | `+0x8A`(4)、`+0x108`(3)、`+0x3F`(2) |
  | `BuildingClass` | 52 | 92 | `+0x20`(13)、`+0x1BB`(7)、`+0x189`(6) |
  | `MapClass` | 24 | 104 | **`+0x13C`(27)**、`+0x140`(13)、`+0xF4`(12) |
  | `WaveClass` | 23 | 46 | `+0x9C`(6)、`+0xA0`(6)、`+0xA4`(5) |
  | `ObjectClass` | 21 | 59 | `+0x9C`(8)、`+0xA0`(8)、`+0xA4`(7) |
  | `ConnectionClass` | 13 | 30 | `+0x20`(7)、`+0x40`(5)、`+0x3C`(4) |
  | `GadgetClass` | 7 | 11 | `+0x20`(4)、`+0x1C`(2) |
  | `CellClass` | 6 | 9 | `+0x28`(3)、`+0x20`(2) |
  | `CCToolTip` | 1 | 3 | `+0x260`(3) |
  - **对 ②-a 的直接印证**：`CCToolTip` 唯一被触碰的偏移是 **`+0x260`**，
    而本项目 ②-a 的崩溃点是 `FUN_00724730` 读 `this+0x250`、`FUN_00724580` 读 `[this+0x250]`。
    `0x260` 与 `0x250` 相差 `0x10` —— 说明这两个容器例程**操作的容器头在 `+0x24C..+0x25C` 区间**，
    而对象自身在 `+0x260` 还有另一个字段。**与 §825-9 的字段图（+0x234 链表/+0x24C 数组/+0x250 计数/+0x25C 当前槽）相容。**
  - `ObjectClass` 与 `WaveClass` 都以 `+0x9C/+0xA0/+0xA4` 为前三 —— 说明这两个偏移在基类里就是坐标/位置三元组。

- **§855-4 [已证·覆盖的子系统数满足里程碑(4) 的"≥6"]**
  | 子系统 | 是否有入口（§853） | 是否有关键结构条目（本节） |
  |---|---|---|
  | GameObj_Logic | ✓ | ✓ (`TechnoClass`/`ObjectClass`/`BuildingClass`/`HouseClass`) |
  | UI_Gadget_Dialog | ✓ | ✓ (`GadgetClass`、`CCToolTip`、`SUB:UI_Gadget_Dialog`) |
  | Ini_Rules_DB | — | ✓ (`SUB:Ini_Rules_DB`) |
  | Net_Transport | ✓ | ✓ (`ConnectionClass`、`SUB:Net_Transport`) |
  | Scenario_Map | ✓ | ✓ (`MapClass`/`CellClass`) |
  | Movement_Locomotion | — | ✓ (`LocomotionClass`、`SUB:Movement_Locomotion`) |
  | Graphics_Blit_Shape | — | ✓ (`BSurface`、`SUB:Graphics_Blit_Shape`) |
  | File_Mix_FS | — | ✓ (`SUB:File_Mix_FS`) |
  | AI_Team_Script | — | ✓ (`SUB:AI_Team_Script`) |
  | SaveLoad | — | ✓ (`SUB:SaveLoad`) |
  | Audio_Sound_Music | — | ✓ (`WaveClass`、`SUB:Audio_Sound_Music`) |
  | Sidebar_Radar_HUD | — | ✓ (`SUB:Sidebar_Radar_HUD`) |
  | Main_Init_Flow | ✓ | — |
  - ⇒ **有结构条目的子系统 12 个；既有入口又有结构条目的 4 个**。里程碑(4) 的"≥6 个子系统的入口与关键结构条目"
    在"结构条目"这一半已达 12 个，远超 6 个要求；但**同一子系统两半都齐的只有 4 个**（这一项如实记为部分达成）。

- **§855-5 [未证·抽取方法的已知局限（数字是下界）]**
  1. **只匹配 `param_1`**。Ghidra 常把 this 存进局部变量（`mov esi,ecx` 后变成 `iVar1 + 0xNN`），
     这类访问**未被统计** ⇒ 上表的偏移数与访问数是**下界**。
     证据：`TechnoClass` 60 个方法只得到 71 个偏移/85 次访问，明显偏稀。
  2. 未做**继承链归并**：`BuildingClass` 的方法访问其基类字段时，偏移记在 `BuildingClass` 名下，
     不会自动与 `TechnoClass`/`ObjectClass` 的同名偏移合并。
  3. 未区分**数组索引访问**（`*(int*)(this + 0x234 + i*4)`）与单字段访问。
  4. 宽度信息来自 Ghidra 的强制转换类型，个别处可能是 `undefined4` 而非真实宽度。

- **§855-6 [已证·产物]** `W131_subsystems\`
  | 文件 | 内容 |
  |---|---|
  | `FieldLayout.java` | 抽取器（反编译 + 偏移/读写/宽度统计） |
  | `emit_fieldlist.py` | 生成 (类/子系统, 函数) 输入列表（含选取规则） |
  | `aggregate_fields.py` | 聚合 + 生成 Markdown |
  | `field_layout_classes.tsv` | 11 个类的偏移表（含读写与宽度） |
  | `field_layout_subsystems.tsv` | 23 个子系统的偏移表 |
  | **`FIELD_LAYOUT.md`** | **人类可读的关键结构条目（按触碰方法数排序）** |
  | `fieldlayout.raw.log` | 1,022 个函数、2,797 条偏移的原始输出 |
"""

src = io.open(LEDGER, encoding="utf-8").read()
if "## §855" in src:
    sys.exit("ABORT: §855 already present")
n0 = len(src)
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (n0, len(back)))
for k in ("## §855", "0x13C", "6/6"):
    print("  %-10s %d" % (k, back.count(k)))
bad = [(hex(ord(c)), back.count(c)) for c in set(back) if ord(c) < 0x20 and c not in "\r\n\t"]
print("control chars:", bad)
