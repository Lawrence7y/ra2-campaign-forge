#!/usr/bin/env python3
"""Append §849: GLM vtable audit -- confirmations, corrections, atlas v2, open items."""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

extra = r"""
## §849 · **GLM 独立抽查：确认 1,214；修正 4 处（类名 988、offset 可很大、子表可长于主表、簇间常量）；槽计数 v2**（2026-11-16 00:20）

- **§849-1 [已证·第三套独立方法再次收敛到同一集合]**
  | 来源 | 方法 | 结果 |
  |---|---|---|
  | 我（§846） | 扫 COL 指针 + 结构自洽 | 1,219 候选 |
  | DeepSeek（§848） | 严格双条件 + 非 `.text/.rsrc` | 1,214 |
  | **GLM（本节）** | 扫 + 逐槽抽查 40 个 + COL 全镜像唯一性 | **1,219 候选；`.rdata` 1,214 全 REAL，`.data` 5 全假** |
  - ⇒ **三方在"canonical = 1,214"上收敛**，且 GLM 的论证路径与 DeepSeek 完全不同
    （它用"该 COL 在全镜像只被引用 1 次"做真实性判据）。
  - 它点名的 **5 个 `.data` 假表**：`0x00875028`（RadioClass，slot0=`0x007FB5F5` 是 `.rdata` 数据指针）、
    `0x00877000/0x00877010/0x0087B17C/0x0087B18C`（DropPodLocomotionClass，COL@`0x00800040` 被 `.data` 结构复用 4 次，
    slot0=`0x010000C0` 未映射）⇒ **与我 C 集合排除的 5 个完全一致**。

- **§849-2 [已证·GLM 的四处修正（我采纳）]**
  1. **类名总数应为 988，不是 954**：全镜像有 **988 个结构完整的 TypeDescriptor**（`+0` 是 type_info vftable、`+4` spare==0、`+8` 内联名）。
     其中 **34 个有 TD 但无本地虚表实现** —— 全是 WOL/COM 接口（`IConnectionPoint`、`IUIApplication` 等）。
     ⇒ 里程碑(1) 应报 **988 类 = 954 有虚表实现 + 34 纯接口**。
  2. **`COL.offset` 可以很大**：`MouseClass` = **21784（0x5518）**，不是只有 4/8/12。offset≠0 的共 **264** 个。
  3. **子表按 `COL.offset` 降序发射、主表（offset=0）在最后**：`AbstractClass` 是 `off12→off8→off4→off0`；
     `MouseClass` 是 `off21784→off0`。⇒ **绝不能把"类的第一张虚表"当主表**，必须用 `COL.offset==0`（我的 atlas 一直这么做 ✓）。
  4. **`AbstractClass` 是多继承类**：CHD 记 **num=8 个基类**，BCA 有 8 条 BCD，其中
     `BCD@0x7FB020→TD INoticeSource`、`BCD@0x7FB038→TD INoticeSink`、`BCD@0x7FB0C8→TD AbstractClass(自基)`。
     ⇒ 之前看到的"每 8 字节一个条目"解释为**相邻的 1 槽子对象虚表**（每对的前一个 dword 本来就是那张表的合法 `[vt-4]`）。

- **§849-3 [已证·★ 簇间 12 字节常量 blob 是槽计数被截断的真凶]**
  GLM 指出簇与簇之间有反复出现的 12 字节常量：`404E0000  A2529D39  3F91DF46`（如 `0x7E1EC4`/`0x7E1F14`/`0x7E1B14`）。
  按 4 字节扫时它们被当成"非代码槽"从而**提前终止槽计数**。
  - ⇒ 这正是我 §846-5 那 **230 个 `other` 终止**的主要来源。
  - 已据此实现**槽计数 v2**（`W130_atlas\atlas_v2.py`），终止判据 = 下一 dword 是合法 COL **或** 属于该常量集合 **或** 既非代码也非 0：
    | 终止原因 | v1（§846） | **v2** |
    |---|---:|---:|
    | `next-col` | 692 | **793** |
    | `sep-const`（新） | — | **155** |
    | `data` | 33 | 191 |
    | `other` | **230** | **75** |
    - ⇒ 有结构解释的终止从 692/1,214 提升到 **948/1,214（78%）**。

- **§849-4 [已证·我拟的两个不变量：一个通过，一个被数据否证]**
  | 不变量 | 结果 |
  |---|---|
  | I1 每个类恰好一张主表（`offset==0`） | **通过，0 违例**（954 类 / 954 主表） |
  | I4 不存在 0 槽虚表 | **通过，0 个** |
  | **I2 主表槽数 ≥ 子表槽数** | **被否证** —— 12 个违例，全在 `LocomotionClass` 家族 |
  | I3 ObjectClass 链单调 | **通过**（见下，我原来的判据写错了） |
  - **I2 的具体反例**：`.?AVLocomotionClass@@` 的 `offset=4` 子表 `0x007EADF4` **确有 49 个连续代码槽**
    （逐槽 dump 全部落在 `.text`），而 `offset=0` 主表 `0x007EAEC0` 只有 **10 槽**。
    且 49 槽正好填到下一张表的 COL（`0x7EAEBC` 处是合法 COL 指针）⇒ **计数没错，是我的假设错了**。
    ⇒ **结论：子表可以比主表长。I2 作废，不是数据问题。**
  - **I3 我写错了判据**：`BuildingClass` 是 `TechnoClass` 的**直接**子类，不是 `FootClass` 的子类。
    正确的单调关系（主表槽数）：`TechnoClass 309` < `FootClass 340`；`TechnoClass 309` < `BuildingClass 321`；
    `FootClass 340` < `UnitClass 345` / `InfantryClass 344` / `AircraftClass 342` —— **全部成立**。

- **§849-5 [已证·几个可直接复用的镜像事实（GLM 提供，我采纳）]**
  | 事实 | 值 |
  |---|---|
  | 全镜像结构完整 TD | **988**（= 988 个唯一类名） |
  | COL 的 pTD 是绝对 VA | **1219/1219**（无 RVA 型） |
  | COL 引用唯一性 | 除 `0x00800040`（被引 5 次）外，**每个 COL 全镜像只被 1 处引用** |
  | `_purecall` | **不在导入表**（静态 CRT），未能定位 |
  | 共享"空实现"桩 | `0x00410260`（`E_POINTER`）×300、`0x00410300/0x00410310`（`mov eax,1; ret 4`）×222、`0x00410210`（this-4 转发）×224、`0x004C9150`（`xor eax,eax; ret`） |
  | 12 槽内含 0 的候选 | 163 个 |
  | `.rdata` 文件字节 | 比 VirtualSize 多 **0x98C** 对齐 padding |
  | `.text` 文件字节 | 比 VirtualSize 多 **0xC73** 尾部 padding |
  - ⇒ **判断"某值是不是代码指针"必须以段范围（VirtualSize 端点）为准，不能用文件 raw 大小**。

- **§849-6 [未证]**
  1. `LocomotionClass` 的子表为何长达 49 槽（架构上不寻常，但与字节完全自洽）——未解释。
  2. 34 个"有 TD 无虚表"的接口是否真的没有本地实现（也可能是实现表在别处未被我的扫描覆盖）。
  3. `+0x2C` = WhatAmI 的真值 144（§848-4）与 GLM 的槽位命中率 11% 一致，但**为什么这类引擎只在
     `ObjectClass` 树用 WhatAmI 而其它类不用**，未解释。
"""

src = io.open(LEDGER, encoding="utf-8").read()
if "## §849" in src:
    sys.exit("ABORT: §849 already present")
n0 = len(src)
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (n0, len(back)))
for k in ("## §849", "988", "I2"):
    print("  %-10s %d" % (k, back.count(k)))
bad = [(hex(ord(c)), back.count(c)) for c in set(back) if ord(c) < 0x20 and c not in "\r\n\t"]
print("control chars:", bad)
