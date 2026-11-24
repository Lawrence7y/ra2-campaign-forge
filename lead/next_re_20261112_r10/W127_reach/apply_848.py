#!/usr/bin/env python3
"""Append §848: DeepSeek audit verdicts + vtable set reconciliation (canonical 1,214)."""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

extra = r"""
## §848 · **审计裁定 + 虚表集合收敛到 1,214（三个集合逐条对账）；`+0x2C=WhatAmI` 进一步收紧到 144**（2026-11-15 23:20）

- **§848-1 [已证·DeepSeek 审计的判定与我的处置]**
  | 命题 | 判定 | 处置 |
  |---|---|---|
  | P1：87 个 `.text` 假阳性 | **CONFIRMED**，并补充关键机制 | **采纳并加强** |
  | P2：8 字节间隔 = "地址捕获 bug / 系统偏移" | **REFUTED** | **撤回我的怀疑** |
  | P3：`+0x2C` = WhatAmI 是普遍规律 | **REFUTED** | **采纳，并进一步收紧** |
  - **P1 的机制（比我原来的说法更准）**：那 87 个地址**全部落在真实指令内部**（0/87 是指令边界；
    对照：87 个随机边界 87/87、87 个随机偏移 26/87）。造假的来源是**把立即数当指针**：
    `E8 7B 80 00 00`（`call`）、`68 80 00 00 00`（`push 0x80`）、`B8 80 00 00 00`（`mov eax,0x80`）里
    都含字节 `80 00 00 00`，按小端读成 `0x00800000`，而该处 `+0x0C` **恰好**是一个真实 TypeDescriptor
    ⇒ 生成脚本就把它当成了一个 COL。**这是"看巧合当结构"的典型案例。**
  - **P2 我错了**：1305 条**全部已经是 `COL+4`**，不存在需要减去的常量。
    `0x007E1F24 / 0x007E1F2C` 是**多继承 thunk 超级结构的内部槽位**，
    其 COL 的 `mdisp` 分别为 `0x0C / 0x08 / 0x04 / 0x00`，且**都带同一个 `.?AVAbstractClass@@`**。
    我在 §846-4 把槽 1/3 的 `.rdata` 值当成"数据"，**其实是 COL 头**。
    ⇒ **§846-4 的"交错排布"描述在字节层面成立（COL 确实紧邻下一张表），但"这是异常"的暗示作废。**

- **§848-2 [已证·★ 三个虚表集合的对账（结论：canonical = 1,214）]**
  工具 `W130_atlas\reconcile_vtables.py`。严格判据 C = `[vt-4]` 在 `.rdata/.data` ∧ `COL.signature ∈ {0,-1}`
  ∧ `COL+0x0C` 是合法 TD ∧ 虚表不在 `.text/.rsrc` ∧ **槽 0 是代码指针**。
  | 集合 | 数量 |
  |---|---:|
  | A 继承表 `_lead_rtti_map.json` | 1,305 |
  | B 我的重建（§846） | 1,219 |
  | **C 严格判据（canonical）** | **1,214** |
  - **A − C = 93**：**87 在 `.text`** + **1 在 `.rsrc`（`0x00B8E0D4`，审计点名）** + 5 其它
  - **B − C = 5**（我的重建多收了 5 个"槽 0 不是代码"的条目）
  - **C − B = 0、C − A ≈ 2**
  - **B ∩ C = 1,214，类名分歧 = 0** ⇒ 我的类名提取正确
  - **统计：1,214 虚表 / 954 类 / 954 主虚表**
  - ⇒ **★ 结构不变量：主虚表数 == 类数 == 954（完全相等）** —— 每个类恰好一张 `COL.offset==0` 的主表。
    这个等式只有在集合干净时才成立，是"1,214 是正确集合"的**独立结构证据**（不依赖任何外部权威）。

- **§848-3 [未证·一处未收敛的数字（如实）]** 审计报"严格重建得 **1,274** 个键"，
  但我按**它自己写的判据**实现只得 **1,214**（差 **60**）。
  - `[未证]` 差在哪：可能它扫描时未要求"槽 0 是代码"，或把 `pos` 的搜索范围放宽到段尾填充之外，
    或对 `.data` 尾部（BSS 边界）的处理不同。**未复现，故不采纳 1,274。**
  - ⇒ 这不影响结论：1,214 满足"主表数 == 类数"与"零类名分歧"两个结构不变量。

- **§848-4 [已证·`+0x2C = WhatAmI()` 进一步收紧：真值 144，不是 185]**
  审计对 1,305 个虚表的 `+0x2C` 做了完整分类：
  | 类别 | 数量 |
  |---|---:|
  | 普通方法（正常 prologue） | 638 |
  | **真正的 `mov eax, smallN; ret`** | **144** |
  | `mov eax, <.data 指针>; ret`（**指针 getter，不是 WhatAmI**） | 41 |
  | 邻近表的 COL 头 | 295 |
  | BSS 区 | 134 |
  | NULL | 31 |
  | 仅 `ret` | 3 |
  | `xor eax,eax`（恒 0） | 19 |
  - ⇒ 我 §846-7 报的"185 个解析成功"里，**41 个是假阳性**（getter 返回 `.data` 指针，
    类编号高达 8,551,228 这种不可能的值）。**真值 144。**
  - ⇒ 审计还做了**槽位扫描对照**：`+0x2C` 命中率 **11%**，而 `+0x04`(6.7%)、`+0x08`(6.7%)、`+0x24`(6.6%) 紧随其后；
    **348 个键在 2–4 个不同槽位都能产出 `mov eax,N;ret`** ⇒ **单看"某槽返回常数"不足以认定那是 WhatAmI**。
  - ⇒ **§846-8 的结论不变但更强**：WhatAmI 反查只在 `ObjectClass` 继承树上可靠
    （本项目 5 个已知类 ID 6/11/36/8/15 全部复核通过），**不可外推**。

- **§848-5 [已证·两个边缘事实]**（审计提供，我采纳）
  1. `.rsrc` 假阳性 `0x00B8E0D4`：COL 链看着有效，但整个是资源字节巧合，其"槽"是 `0x0017006C`、`0xFFFF0521` 之类。
  2. `.data` 尾部：`raw_end = 0x0087E000` 之后是 BSS（3,128,292 字节无文件字节）；
     但 `.data` **最后 16 个文件字节全为 0**，所以读到尾部填充的人看到的是 0 而不是"没有字节" —— 容易误判。

- **§848-6 [已证·canonical 产物]** `W130_atlas\vtables_canonical.json`（1,214 条，含 vt / col / class / sig / col_offset / section / primary）。
  ⇒ **后续所有工作一律以此为准**；`_lead_rtti_map.json` 与 `vtables_rebuilt.json` 降级为历史对照。
"""

src = io.open(LEDGER, encoding="utf-8").read()
if "## §848" in src:
    sys.exit("ABORT: §848 already present")
n0 = len(src)
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (n0, len(back)))
for k in ("## §848", "1,214", "144"):
    print("  %-10s %d" % (k, back.count(k)))
bad = [(hex(ord(c)), back.count(c)) for c in set(back) if ord(c) < 0x20 and c not in "\r\n\t"]
print("control chars:", bad)
