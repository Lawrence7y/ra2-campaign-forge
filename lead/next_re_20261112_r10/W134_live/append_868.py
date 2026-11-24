#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append §868: C5 REFUTED decisively — 0xB0F730 is not a total-object count."""
import io

LED = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

SEC = """
## §868 · **【定性定谳】`0xB0F730` 不能当"对象总数"——`FootClass` 构造器只登记自己的类型表，完全不碰它**（2026-11-15 15:35）

> 来源：DeepSeek 对抗性复核 `ds-t2-refute` 判 **C5 = REFUTED**。
> **我亲自复算确认了它的核心证据（逐指令统计四个全局在函数体内的引用次数）。**
> 本条**终结** §859 遗留的 `AbstractClass::Array` 完整性问题：不是"未证"，而是**已证否**。

- **§868-1 [已证·决定性证据]** `FootClass::FootClass`（`0x004D31E0`，860 字节）内的全局引用计数：
  | 全局 | 引用次数 |
  |---|---:|
  | `0xB0F724` `AbstractClass::Array.Items` | **0** |
  | `0xB0F730` `AbstractClass::Array.Count` | **0** |
  | `0x8B3DC4` `FootClass::Array.Items` | **1** |
  | `0x8B3DD0` `FootClass::Array.Count` | **3** |
  | `0xA8EB44`/`0xA8EB50`（Building） | 0 / 0 |
  | `0x8B410C`/`0x8B4118`（Unit） | 0 / 0 |
  - ⇒ 这是一个**标准的"1 次 Items + 3 次 Count"内联 `AddItem`**（§859-6 里我自己描述过的那个形态），
    它**确实在登记**——但登记的是 **`FootClass::Array`**，**`AbstractClass::Array` 一次都没碰**。
  - ⇒ 一个基类构造器**有此行为**，就足以否证"凡对象皆登记进 `AbstractClass::Array`"。

- **§868-2 [已证·覆盖面（复核给出的横向统计）]**
  在 `0x004101F0`（`AbstractClass` 构造器）的 **47 个调用者**里，
  只有 **`AlphaShapeClass`、`FactoryClass`、以及一个 `AnimClass` 析构器** 内联了 push。
  下列类**全部缺席**：
  `TechnoClass`、`BuildingClass`、`UnitClass`、`InfantryClass`、`AircraftClass`、
  `FootClass`、`BulletClass`、`AnimClass`(构造)、`OverlayClass`、`TerrainClass`、
  `SmudgeClass`、`HouseClass`。
  - ⇒ **读 `[0xB0F730]` 当对象总数，会静默漏掉所有建筑、载具、步兵、飞机。**

- **§868-3 [已证·与 §862/§867 三条互相独立地指向同一结论]**
  | 节 | 独立证据 | 结论 |
  |---|---|---|
  | **§862** | `AbstractClass::AbstractClass` 只有 28 字节 / 4 条 `mov` / `n_callees=0` | 根类不登记 |
  | **§867** | `AbstractClass*` 有 **12 个**不同数组（同一虚表 `0x7E91EC`） | 不是"一个总表" |
  | **§868** | `FootClass` 构造器登记自己的表、`AbstractClass` 表 0 引用 | 无总表行为 |
  - ⇒ 三条**用不同方法**得到同一结论。**"`AbstractClass::Array` 是完整对象注册表"已证否。**

- **§868-4 [已证·那么"对象总数"该怎么读]**
  | 想要的量 | 读法 | 状态 |
  |---|---|---|
  | 所有**可移动**对象 | `[0x008B3DD0]` `FootClass::Array.Count` | **可靠**（构造器实证登记） |
  | 载具 | `[0x008B4118]` | 可靠 |
  | 步兵 | `[0x00A83DF8]` | 可靠 |
  | 飞机 | `[0x00A8E3A0]` | 可靠 |
  | 建筑 | `[0x00A8EB50]` | 可靠 |
  | **所有对象（含建筑）** | `FootClass.Count + BuildingClass.Count + 其它叶子类` | **估算，须声明口径** |
  | ~~`[0xB0F730]`~~ | **不可用** | **已证否** |

- **§868-5 [已证·复核自曝的一个假否证（方法学价值高）]**
  复核报告自己写明：它**第一轮把 C2–C4 判成了 REFUTED，那是它自己的 bug** ——
  本镜像的 `TypeDescriptor` 名字是**内联在 `TD+0x08`**，不是 `char*`。
  用 `read_string(u32(TD+0x08))` 的写法会**静默返回 0 个类型**，它一度把这"沉默"当成了"身份是编造的"。
  修正后得到 **988** 个 TypeDescriptor，与 W132 的独立计数一致。
  - ⇒ 这与 **§859-3** 里我自己踩的坑**完全同源**（`u32(TD+8)` 是 ASCII 而非指针 / `.rdata` vs `.data`）。
  - ⇒ **教训升级**：`TD+0x08` 内联这一点**至少已让两个独立实现各错一次**。
    任何"扫描得到 0 个结果"的情形，**必须先怀疑扫描器**，不能当成"事实不存在"。

- **§868-6 [已证·被确认的其余 6 条]**
  | 声明 | 判定 | 关键证据 |
  |---|---|---|
  | C1 布局（`+0/+4/+8/+0xC/+0xD/+0x10/+0x14`，increment=10） | **CONFIRMED** | 8 个独立 `.CRT$XCU` 构造器 + 虚方法自己的 `[this+disp]` 集合 `{0,4,8,12,13,16}` + 内联 `Add` 序列 |
  | C2 `0xA8EB40` = Building | **CONFIRMED** | `0x4E6B7D`→`0x7E9E24`→`BuildingClass*`；`0xA8EB44` ±0x20 内无 UnitClass 派生虚表 |
  | C3 `0x8B4108` = Unit | **CONFIRMED** | 全镜像 1,971 个 `C7 05` 里，**载具只有这一个向量**，无第二份 |
  | C4 `0xA80228` = House | **CONFIRMED** | 飞机是另一个对象 `0xA8E390`，相距 0xE168 |
  | C6 `0x8B3DC0` = Foot | **CONFIRMED**（并集完整性 `[未证]`） | 插入点 `0x4D3487` 实证 `[+8]=Capacity`、`[+0x10]=Count`、`[+0x14]=increment`、`[ecx+eax*4]=Items` |
  | C7 4 个 vptr / `0x4101F0` | **CONFIRMED** | 四 COL `0x7FB118/0x7FB008/0x7FAFF0/0x7FAFD8` 全部指向 TD `0x8177C8` `.?AVAbstractClass@@`，offset **0/4/8/12** |
  - ⇒ **§859 的 49 数组表在"身份"层面经受住了对抗性复核**（除 C5 的定性被推翻）。
  - ⚠️ 但复核那句"**每个元素类型恰好只有一个向量**"**只在载具上成立**：
    §867 已实证 `TechnoClass` 有 4 个、`ObjectClass` 3 个、`BulletClass` 2 个、`BuildingClass` 2 个。
    这句话**作为通则不成立**，不应引用。

- **§868-7 [未证·如实登记]**
  1. `ClassDescriptor` 的 `+0x40` 自校验在本镜像上**对所有类都失败**，因此**继承关系无法从 RTTI 层验证**
     （这影响 `FootClass` 是否为另外三者的基类这一"并集完整性"判断）。
  2. 那 12 个 `AbstractClass*` 数组各自的用途**仍未知**：其中是否有一个**确实**在收集全部对象
     （例如待删除队列）—— 本轮没有证据支持，也**没有证据排除**。
  3. §868-2 的"47 个调用者里只有 3 个内联 push"**我未独立复算**（只复算了 §868-1 那条）。

- **§868-8 [已证·产物]** `lead\\next_re_20261112_r10\\W135_ds\\T2_refute\\`
  `t2_refute.py`、`verdicts.tsv`、`counter_evidence.txt`（946 行）、`report.md`。
"""

P = LED
s = io.open(P, encoding="utf-8", newline="").read()
if "## §868 ·" in s:
    raise SystemExit("REFUSE: §868 already present")
s = s.rstrip("\n") + "\n" + SEC
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
bad = [(i, hex(ord(c))) for i, c in enumerate(s) if ord(c) < 32 and c not in "\n\t"]
print("appended §868; size=%d; control chars=%d" % (len(s.encode("utf-8")), len(bad)))
