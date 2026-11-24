#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Update SESSION_HANDOVER_R10.md with §859 (the instance-array table)."""
import io

P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\SESSION_HANDOVER_R10.md"
s = io.open(P, encoding="utf-8", newline="").read()

# ---- 1. rewrite open item 6 (it was overturned, not merely pending) ----
OLD6 = ("6. **§853 的 `DAT_00a8eb44`（疑似单位主表）未真机验证** ← 下一轮最值得做\n")
NEW6 = ("6. ~~§853 的 `DAT_00a8eb44`（疑似单位主表）未真机验证~~ → **§859 已把它推翻并定名**：\n"
        "   它不是单位主表，而是 `BuildingClass::Array.Items`。真正的单位清单是 `UnitClass::Array`\n"
        "   @ `0x008B4108`（Count `0x008B4118`）。**类型已证、数值（真机读数）未验**。详见下方 0'.4。\n")
if s.count(OLD6) != 1:
    raise SystemExit("REFUSE: open item 6 not found exactly once")
s = s.replace(OLD6, NEW6)

# ---- 2. add 0'.4 section right before "## 0. 锚点（未变）" ----
ANCHOR = "## 0. 锚点（未变）"
SEC = """### 0'.4 **引擎全部实例数组已定名（§859）—— `DAT_00a8eb44` 不是单位表**

> 2026-11-15 新增。起因是上面那条"下一轮最值得做"，结果**静态就把前提问倒了**，没上真机。

**结论**：`0x006DD8B0`（状态机分派器）遍历的不是"单位列表"，而是**六种不同类型数组**；
项目一直在找的"单位列表"是 `UnitClass::Array` @ `0x008B4108`。

**对象布局（字节级已证，源自 `0x004E6B60` 静态构造器 + `0x004E6BA0` atexit 析构器）**

| 偏移 | 字段 |
|---:|---|
| `+0x00` | vftable（ctor 写 `DynamicVectorClass`，dtor 写回基类 `VectorClass`） |
| `+0x04` | `T* Items` |
| `+0x08` | `int Capacity` |
| `+0x0C` | `bool IsInitialized` |
| `+0x0D` | `bool IsAllocated` |
| `+0x10` | `int Count` |
| `+0x14` | `int CapacityIncrement`（= 10） |

⇒ **`Items = base + 4`，`Count = base + 0x10`**。知道基址，两个字段地址就确定。

**计数该怎么读（口径表）**

| 想要的量 | 读址 | 状态 |
|---|---|---|
| 全部游戏对象 | `[0x00B0F730]` `AbstractClass::Array.Count` | 身份 `[已证]`，完整性 `[未证]` |
| 全部可移动对象 | `[0x008B3DD0]` `FootClass::Array.Count` | `[已证]` |
| 载具 units | `[0x008B4118]` `UnitClass::Array.Count` | `[已证]` |
| 步兵 | `[0x00A83DF8]` | `[已证]` |
| 飞机 | `[0x00A8E3A0]` | `[已证]` |
| 建筑 | `[0x00A8EB50]` | `[已证]` |
| Techno | `[0x00A8EC88]` | `[已证]` |

⚠️ **口径修正**：`FootClass` = 步兵 + 载具 + 飞机，所以**「单位总数」应读 `0x8B3DD0`**；
过去把 `0x8B4118` 当"单位总数"是**偏窄口径**（漏掉步兵与飞机）。

**另外纠正一处项目文档（不是台账）**：`docs/re/net_sync_checksum.md:261` 把
`0xA8022C / 0xA80238` 标成 "for each Aircraft" —— 实际是 **`HouseClass::Array`**；
飞机是 `0xA8E394 / 0xA8E3A0`（也就是 harness 里 `MEASURE_AIRCRAFT_VA` 读的，**harness 对、文档错**）。

**产物**：`W132_arrays\\` —— `W132_ARRAYS.md`（报告）、**`instance_arrays.tsv`（49 行全表）**、
`w132d_instance_arrays.py`（可复跑生成器）、`w132c_*`/`w132b_*`/`w132_*`。

**限制**：49 个身份全是**静态**结论；`AbstractClass::Array` 的"完整性"未证（14 个函数内联 push/pop，
说明它活着，但没证"每个派生类构造都登记自己"）。判定只需一次真机读数比对各类型计数之和。

---

"""
if SEC in s:
    raise SystemExit("REFUSE: 0'.4 already present")
if s.count(ANCHOR) != 1:
    raise SystemExit("REFUSE: anchor '## 0. 锚点（未变）' not found exactly once")
s = s.replace(ANCHOR, SEC + ANCHOR)

# ---- 3. the overturned-conclusions table gains an 8th row ----
OLDROW = "| `EIP=0` 是项目内最多崩溃签名 | **错**：真机现场 **25/26 是 ②-a** | §835 |\n"
NEWROW = (OLDROW +
          "| `DAT_00a8eb44` 是\"单位/对象主表\" | **错**：它是 `BuildingClass::Array.Items`；单位表是 `0x8B4108` | **§859** |\n")
if s.count(OLDROW) != 1:
    raise SystemExit("REFUSE: overturned-table row anchor not found exactly once")
s = s.replace(OLDROW, NEWROW)
s = s.replace("### ⚠️ 后续接手必读：交付过程中被推翻的旧结论（7 条）",
              "### ⚠️ 后续接手必读：交付过程中被推翻的旧结论（8 条）")

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("handover updated; size %d bytes" % len(s.encode("utf-8")))
bad = [(i, hex(ord(c))) for i, c in enumerate(s) if ord(c) < 32 and c not in "\n\t"]
print("control-char problems:", len(bad), bad[:5])
