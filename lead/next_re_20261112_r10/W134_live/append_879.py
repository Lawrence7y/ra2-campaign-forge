#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append §879: the dispatcher's 145-entry jump table decoded — 15 per-type update states."""
import io

LED = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
s = io.open(LED, encoding="utf-8", newline="").read()

SEC = """
## §879 · **【① 的结构答案】`0x006DD8B0` 的跳转表已解：145 项 → 143 个 case 目标，其中 **15 个 state 各自遍历一种实例数组** —— 每帧模拟不是"一个主循环"，而是 15 路按类型分工的更新**（2026-11-15 18:20）

> 承接 §873（`case 1` 被排除）。纯静态，零真机。**这是 ① 卡顿线在排除错误锚点后拿到的第一个可信结构。**

- **§879-1 [已证·分派机制]**
  `0x006DD8B0` 开头的分派：
  ```asm
  006DD8D7  8b562c           mov  edx, [esi + 0x2C]        ; 状态字段
  006DD8DB  81fa90000000     cmp  edx, 0x90               ; 上界 144
  006DD8E7  ff2495ecfd6d00   jmp  dword ptr [edx*4 + 0x006DFDEC]   ; <<< 跳转表
  ```
  - 表在 **`0x006DFDEC`**，`cmp edx,0x90` ⇒ **145 个表项（state 0..144）**。
  - 我逐项读出：**145 项全部有效**（都指向 `.text`），但只有 **143 个不同目标**（2 项重复）。
  - ⇒ T6 报的"143 个 case"更接近"143 个不同目标"，而**表长是 145**。两个数都对，口径不同。

- **§879-2 [已证·★ 15 个 state 各自遍历一种实例数组（我逐一判定）]**
  对每个 case 目标，取其到下一个目标之间的区间，统计其中引用了哪些"数组 Count 全局"：
  | state | 目标 | 指令数 | 遍历的数组 |
  |---:|---|---:|---|
  | **90** | `0x006DDAF9` | 39 | **Infantry** |
  | **81** | `0x006DDBF6` | 41 | **Foot** |
  | **82** | `0x006DDC71` | 41 | **Foot** |
  | **83** | `0x006DDCEC` | 47 | **Techno** |
  | **59** | `0x006DDEF5` | 40 | **Building** |
  | **60** | `0x006DDF65` | 41 | **Building** |
  | **61** | `0x006DDFD9` | 41 | **Building** |
  | **51** | `0x006DEFBC` | 49 | **Building** |
  | **110** | `0x006DF717` | 47 | **Building** |
  | **11** | `0x006DF051` | 22 | **Trigger** |
  | **21** | `0x006DF0E7` | 27 | **Trigger** |
  | **53** | `0x006DF164` | 24 | **Trigger** |
  | **88** | `0x006DF49E` | 42 | **ParticleSystem** |
  | **105** | `0x006DF5D1` | 55 | **House** |
  | **101** | `0x006DD9EC` | 63 | （无数组引用） |
  - 汇总：**Building ×5、Trigger ×3、Foot ×2、Infantry ×1、Techno ×1、ParticleSystem ×1、House ×1 = 15 个**
  - ⇒ **没有 `UnitClass`，没有 `AircraftClass`。** 与 §873 的独立结论一致（载具属 `FootClass`，已被 Foot 覆盖）。

- **§879-3 [已证·★ 对 ① 的净结论：不存在"一个每帧主循环"]**
  **每帧模拟是 15 路按类型分工的更新**，各自对应一个 `state` 值，各自遍历自己那一类实例数组。
  - ⇒ **§853 说"主循环 `0x006DD8B0` 遍历六种数组"这个画面是错的**：
    不是一个循环遍历六种，而是**六个 state 各自遍历一种**（外加 Foot 两种、Building 五种）。
  - ⇒ **这解释了 ① 调查为何反复失败**：所有"找主循环 / 找那个热点"的努力都预设了**单一入口**，
    而实际结构是**多入口、按类型分工、由 `[obj+0x2C]` 在运行时选择**。
    任何"逐帧成本"的静态排序都必须先知道**这一帧有哪几个 state 在跑** —— 而那是运行时数据。
  - ⇒ 与 §873-5 的"数据依赖分支"叠加：**即使知道哪个 state 在跑，循环体内还有
    `[obj+0x90]`/`[obj+0x74]`/`[obj+0x81]`/`[obj+0x34]` 等条件决定最重的调用是否执行**。
  - ⇒ **因此：静态分析能给的最强结论只到"15 路分工 + 各路遍历谁"，给不出成本排序。**
    这与 §873-6 的判断一致，但现在有了结构依据而不是猜测。

- **§879-4 [已证·分派器的调用拓扑]**
  | 节点 | 直接调用者 |
  |---|---|
  | 分派器 `0x006DD8B0` | **1 个**：`0x00726605`（在 `0x007265C0` 内） |
  | `0x007265C0` | **5 个**：`0x006DF119`、`0x006E2AD0`、`0x006E5439`、`0x006E5450`、`0x006E546D` |
  | Trigger 循环头 `0x006DF0FF` | 0（它是循环头，不是函数入口） |
  - ⇒ `0x006DF119` 落在 Trigger 循环体内 ⇒ **分派器会在 Trigger 循环里被逐节点重入**（§873-4）。
  - ⇒ **分派器自身不是"每帧一次"，而是"每个触发节点一次"** —— 这一条比 §873 的表述更精确：
    "每帧"是通过 Trigger 循环的迭代次数间接实现的。

- **§879-5 [未证·如实登记]**
  1. **哪个 state 在某一帧生效**：由 `[obj+0x2C]` 运行时决定，**静态不可知**。
     `obj` 是什么对象（`esi` 的来源）**我未追溯**。
  2. **145 项里 2 项重复**（同一目标对应两个 state）—— 具体是哪两个 state 我**未列出**。
  3. 我只统计了"数组 Count 全局"的引用；**未统计 `Items` 指针的引用**，
     因此"该 case 遍历某数组"的判据依赖 Count，可能漏掉"只用 Items 不用 Count"的循环。
  4. state 101（`0x006DD9EC`，63 条指令）**无数组引用但我未定性**。
  5. `0x007265C0` 的另外 4 个调用者（`0x6E2AD0`/`0x6E5439`/`0x6E5450`/`0x6E546D`）**未定性**。
  6. 本节的 state 编号是**表索引**，与 `switch` 里的 `case` 标号**未核对是否一致**。
"""

if "## §879 ·" in s:
    raise SystemExit("REFUSE: §879 already present")

# forward pointer at §873-4
OLD = "  | 循环头 | **19 个**，分布在 **13 个 case 块** |"
NEW = ("  | 循环头 | **19 个**，分布在 **13 个 case 块** |\n"
       "  | ⚠️ 更正 | **§879 已解出跳转表**：表长 **145**、不同目标 **143**、"
       "其中 **15 个 state 各遍历一种数组**（Building×5/Trigger×3/Foot×2/Infantry/Techno/ParticleSystem/House）|")
if s.count(OLD) == 1:
    s = s.replace(OLD, NEW)
    print("§873-4 forward pointer added")
else:
    print("WARN: §873-4 anchor found %d times, skipped" % s.count(OLD))

s = s.rstrip("\n") + "\n" + SEC
io.open(LED, "w", encoding="utf-8", newline="\n").write(s)
bad = [(i, hex(ord(c))) for i, c in enumerate(s) if ord(c) < 32 and c not in "\n\t"]
print("appended §879; size=%d; control chars=%d" % (len(s.encode("utf-8")), len(bad)))
