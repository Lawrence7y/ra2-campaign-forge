#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append §859 to the atlas ledger. Writes UTF-8, LF, no control chars."""
import io
import os

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, "instance_arrays.tsv")

rows = [l.split("\t") for l in io.open(TSV, encoding="utf-8").read().splitlines()[1:] if l.strip()]

tbl = ["| 元素类型（**二进制自带 RTTI**） | base | Items | Count | 虚表 | COL |",
       "|---|---|---|---|---|---|"]
for r in rows:
    el, base, it, cn, vt, col = r[0], r[1], r[2], r[3], r[4], r[5]
    mark = ""
    if any(k in el for k in ("BuildingClass", "UnitClass", "InfantryClass",
                             "AircraftClass", "FootClass", "TechnoClass",
                             "HouseClass", "AbstractClass", "TriggerClass")):
        mark = "**"
    tbl.append("| %s`%s`%s | `%s` | `%s` | `%s` | `%s` | `%s` |"
               % (mark, el, mark, base, it, cn, vt, col))
TABLE = "\n".join(tbl)

SEC = """
## §859 · **修正 §853-3：`DAT_00a8eb44` 不是"单位主表"，而是 `BuildingClass::Array.Items`；顺带用二进制自带 RTTI 把引擎全部 49 个实例数组逐一定名**（2026-11-15 13:50）

> 起因：§857-5 第 6 条把"`DAT_00a8eb44`（疑似单位主表）未真机验证"列为待办。
> 我本轮**没有先上真机**，而是先把静态问题问清楚，结果发现**这条待办的前提本身就是错的**。

- **§859-1 [已证·纠错（我的错）]**
  §853-3 写「`DAT_00a8eb44` 是"对象指针数组 + 计数 `DAT_00a8eb50`"这一对，是最像"单位/对象主表"的结构」，
  并据此在 §853-3 末尾写「这也解释了 §707 的"格链不登记单位（213 vs 设计 1500）"：**单位不在格链上，而在这些全局数组里**」。
  **这两句都错**，错在"这些全局数组"的**元素类型判断**：
  | 全局 | §853-3 的说法 | **真身份（本轮已证）** |
  |---|---|---|
  | `DAT_00a8eb44` | 单位/对象主表 | **`BuildingClass::Array.Items`** |
  | `DAT_00a8eb50` | 同型列表上界 | **`BuildingClass::Array.Count`** |
  - ⇒ 主循环 `0x006DD8B0` 遍历的**不是"单位列表"，而是六种不同类型数组**
    （`TriggerClass` / `BuildingClass` / `FootClass` / `TechnoClass` / `HouseClass` / `InfantryClass`）。
  - ⇒ **项目真正在找的"单位列表"是 `UnitClass::Array` @ `0x008B4108`（Count `0x008B4118`）**，
    这个地址 harness 早就在读（`MEASURE_UNITS_VA`），只是**没人把它和 §853-3 的叫法对上**。
  - ⇒ 教训（与 §835/§837 同类）：**"这段代码在遍历一个指针数组 + 一个计数"能证明它是数组，
    不能证明数组里装的是什么**。类型必须由 RTTI 或写入方决定，不能由调用点的形态猜测。

- **§859-2 [已证·对象布局（字节级）]**
  `0x004E6B60` 是 `BuildingClass::Array` 的 `.CRT$XCU` 静态构造器，`0x004E6BA0` 是它
  `atexit` 注册的析构器。两者把布局钉死到字节：
  ```
  +0x00 vftable            ct 写 0x7E9E24(DynamicVectorClass) ; dt 写回 0x7E9E44(VectorClass 基类)
  +0x04 T*   Items         ct 置 0                            ; dt 若 IsAllocated 则 delete[] 后置 0
  +0x08 int  Capacity      ct 置 0
  +0x0C bool IsInitialized ct 置 1
  +0x0D bool IsAllocated   ct 置 0                            ; dt 据此决定是否释放
  +0x10 int  Count         ct 置 0
  +0x14 int  CapacityIncrement ct 置 10
  ```
  - ⇒ **`Items = base + 4`，`Count = base + 0x10`**。这条算术把此前所有"某个全局是计数还是指针"的争论一次性消掉：
    只要知道数组对象基址，两个字段的地址就是确定的。
  - ⇒ 构造器/析构器各写一次 vptr（派生→基类）是标准 C++ 语义；**正是这一点让元素类型可从二进制反查**。

- **§859-3 [已证·定名方法]** 三段链，全部在镜像内：
  `vftable V --[V-4]--> COL --[COL+0x0C]--> TypeDescriptor --[TD+8]--> ".?AV?$DynamicVectorClass@PAVBuildingClass@@@@"`
  - 本镜像的 **RTTI 名字串在 `.data`（`0x815DE8+`）而不在 `.rdata`** ——
    只扫 `.rdata` 会得到 **0 个** TypeDescriptor（我第一版就踩了这个坑）。
    全扫后得到 **988 个 TD**，与 §849 的类总数 988 **逐一吻合**；其中 **404 个**是 `VectorClass`/`DynamicVectorClass` 实例化。
  - 数组对象本身在 BSS（`.data` 超过 rawEnd `0x87E000`），静态读不到 vptr，
    所以 vptr 必须从**构造器的 `C7 05 <base> <vftable>` 字节模式**取；直接用 capstone 从 `hit-16` 开始解
    会因跨指令起点而错位，**这曾让我把 4 个数组误判成基类 `VectorClass`**（已修正，见 §859-7-3）。

- **§859-4 [已证·引擎全部 49 个实例数组]**
  **49 / 49 全部由二进制自带 RTTI 定名**（不依赖任何外部头文件）。
  与仓库内 `YRpp` 头文件交叉核对：**48 个一致**，第 49 个只是拼写差异
  （二进制 `SpotLightClass`，YRpp `SpotlightClass`）。

{TABLE}

- **§859-5 [已证·另一处文档错误（不是我的台账，是项目文档）]**
  `docs/re/net_sync_checksum.md:261` 把 `0xA8022C / 0xA80238` 标成 "for each Aircraft"。
  本轮证明这一对是 **`HouseClass::Array.Items / .Count`**（`0xA80228` 基址 +4/+0x10）。
  飞机是 **`0xA8E394 / 0xA8E3A0`**（基址 `0xA8E390`）——也就是 harness 里 `MEASURE_AIRCRAFT_VA = 0x00A8E3A0` 读的那个，
  **harness 是对的，文档是错的**。（这条错误从未进入任何结论，但会误导后续读者。）

- **§859-6 [已证·对 §707「格链不登记单位」的意义]**
  §707 的观察（链 A 213 节点 / 链 B 全空 vs 设计 1500 单位）原本是个悬案。现在结构上清楚了：
  **格链（`CellClass +0xE4/+0xE8`）是空间索引，实例数组才是对象清单，两者本来就不是一个东西。**
  从格链读 N 与从数组读 N 测的是不同量，"213 vs 1500" 不构成"对象丢失"的证据。
  - ⇒ **§707-6 要的"如何得到真实单位数"，答案在这里**（口径表；本轮只证**身份**，数值仍需真机读）：
  | 想要的量 | 读址 | 状态 |
  |---|---|---|
  | 全部游戏对象 | `[0x00B0F730]` `AbstractClass::Array.Count` | 身份 `[已证]`，**完整性 `<{UNPROVEN}>`** |
  | 全部可移动对象 | `[0x008B3DD0]` `FootClass::Array.Count` | 身份 `[已证]` |
  | 载具（units） | `[0x008B4118]` `UnitClass::Array.Count` | 身份 `[已证]` |
  | 步兵 | `[0x00A83DF8]` `InfantryClass::Array.Count` | 身份 `[已证]` |
  | 飞机 | `[0x00A8E3A0]` `AircraftClass::Array.Count` | 身份 `[已证]` |
  | 建筑 | `[0x00A8EB50]` `BuildingClass::Array.Count` | 身份 `[已证]` |
  | Techno（建筑+可移动） | `[0x00A8EC88]` `TechnoClass::Array.Count` | 身份 `[已证]` |
  - `FootClass` = infantry + units + aircraft 的公共父类，所以**「单位总数」应读 `0x8B3DD0` 而不是 `0x8B4118`**
    —— 过去把 `0x8B4118` 叫 "units" 并当作"单位总数"，**口径偏窄**（漏掉步兵与飞机）。

- **§859-7 [未证·如实登记]**
  1. **`AbstractClass::Array` 的"完整性"未证**：`0xB0F724`/`0xB0F730` 上有 **14 个函数**内联了 push/pop
     （每个函数 1 次 Items 读 + 3 次 Count 访问），说明它确实是活的注册表，
     但我**没有**证明"每个 `AbstractClass` 派生类构造时都登记自己"。
     要判定只需一次真机读数：`[0xB0F730]` 是否等于各类型计数之和。
  2. **本轮 49 个身份全是静态结论，零真机验证**。某局 `[0x008B4118]` 是否等于图上实际载具数，仍是经验问题
     （虽然历史 harness 一直按此口径使用）。§857-5 第 6 条因此**从"未验证"降级为"类型已证、数值未验"**。
  3. `refs` 计数（参考列）用的是窗口反汇编，**可能少算**（16 字节回看会失步）；身份结论不依赖它。
  4. 我只枚举了 **YRpp 声明过的 49 个**。引擎里可能还有**没有对应头文件声明**的 `DynamicVectorClass` 全局；
     588 个 COL 里有 `VectorClass` 类型，但**并非每个都有静态全局实例**。这条未穷举。

- **§859-8 [已证·产物]** `lead\\next_re_20261112_r10\\W132_arrays\\`
  | 文件 | 内容 |
  |---|---|
  | **`W132_ARRAYS.md`** | 本轮报告（含完整推导、反汇编证据、诚实账） |
  | **`instance_arrays.tsv`** | 49 行 × 11 列（element/base/items/count/vftable/col/td/refs/yrpp/agree） |
  | `w132d_instance_arrays.py` | **生成上表**（字节模式 `C7 05` + RTTI 链，可复跑） |
  | `w132c_vtable_names.py` | 关键数组的 vftable→COL→TD→名字 |
  | `w132b_vector_family.py` | YRpp 交叉核对 + 静态构造器区域转储 |
  | `w132_array_globals.py` | 任意全局/函数的绝对引用扫描（`--fn 0x4E6B60`） |
  | `run1.log`..`run7.log` | 各步原始输出 |
"""

SEC = SEC.replace("{TABLE}", TABLE).replace("{UNPROVEN}", "未证")

path = LEDGER
txt = io.open(path, encoding="utf-8").read()
if "## §859 ·" in txt:
    raise SystemExit("§859 already present, refusing to append twice")
txt = txt.rstrip("\n") + "\n" + SEC
io.open(path, "w", encoding="utf-8", newline="\n").write(txt)

# control-char audit (lesson from the \\next_re and \\verify incident)
bad = [(i, hex(ord(c))) for i, c in enumerate(txt) if ord(c) < 32 and c not in "\n\t"]
print("appended §859, new size=%d bytes, control-char problems=%d" % (len(txt.encode("utf-8")), len(bad)))
if bad:
    print("FIRST BAD:", bad[:5])
