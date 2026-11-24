#!/usr/bin/env python3
"""Append §837: withdraw the 'Terrain dangling node' over-claim and downgrade §836."""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

extra = r"""
## §837 · **再次更正（自我推翻 §836）：`EDI=0x24` 是"要找的类型"，不是"坏节点的类型" ⇒ "两条独立成因"没有证据**（2026-11-15 15:00）

- **§837-1 [已证·原推理的错误]** §829-4/-5 我写："`EDI` 恒为 `0x24`=TerrainClass ⇒
  崩溃发生在'在格链上查找 TerrainClass 对象'的遍历里，链上出现了**已释放的 Terrain 节点**"。
  **后半句是错的。**
  - 崩溃时 `EAX`（节点首 dword，被当虚表）= `0x10FDCA08`，**落在映像所有段之外** ⇒ 节点内存已被释放/复用
    ⇒ **节点的 vptr 已不是有效虚表** ⇒ **该节点原本属于哪个类，从这份日志里根本读不出来**。
  - `EDI=0x24` 只说明**调用方想找 Terrain 对象**，与"撞到的死节点是什么类"**无关**。
  - ⇒ 正确表述：**"在按类型 0x24 线性查找格链的过程中，撞到了一个已释放的节点（类型不可知）"**。

- **§837-2 [已证·因此 §836 的"两条独立成因"作废（降级为未证推测）]**
  - §836 的核心论据是"TerrainClass 是 1×1，不可能走多格建筑的 `next` 单值复写机制 ⇒ 必有第二成因"。
  - 该论据**依赖 §837-1 那个错误前提**（即坏节点是 Terrain）。前提撤销 ⇒ 论据作废。
  - ⇒ **当前证据只支持一条成因：成因 A（多格建筑重叠 + 被摧毁 ⇒ 链上残留死建筑节点）**，
    它与 §630-3（零交战对照全绿）、§1.3（step=2 vs step=3）、§646/§632-3（坏节点是 BuildingClass）
    **以及本次 20 份 `EIP=0` 日志全部相容**。
  - ⇒ **"成因 B（绕过摘链的销毁路径）"降级为 `[未证·推测]`**：它在架构上可能存在（见 §837-3），
    但**本项目目前没有任何证据要求它存在**。**不得**据此改动 ②-b 的修法结论。

- **§837-3 [已证·架构事实（这部分是硬的，与上面推测无关）]**
  | 事实 | 值 |
  |---|---|
  | `AddObject`（每格挂链）`0x0047E8A0` 的调用者 | **仅 1 个**：`0x005683C0`（footprint 挂链包装） |
  | `RemoveObject`（每格摘链）`0x0047EA90` 的调用者 | **仅 1 个**：`0x005687F0`（footprint 摘链包装） |
  | `0x005687F0` 的调用者 | 4 处：`0x004D37F5`、`0x0071C053`、`0x0041552E`、`0x0043F1D5` |
  | `0x005683C0` 的调用者 | 4 处：`0x004D37DD`、`0x0071BFF8`、`0x00415565`、`0x0043F691` |
  - 其中 `0x0071C053` / `0x0071BFF8` 落在 **TerrainClass** 的占用切换虚函数（`0x0071BFB0`）内；
    `0x0043F1D5` / `0x0043F691` 落在 **BuildingClass** 的占用切换虚函数（`0x0043F180`）内
    —— 与 §2.3 的表**完全吻合**。
  - ⇒ **挂链/摘链是高度中心化的：所有对象都只能经"footprint 包装 → 每格 Add/Remove"这一条路。**
    这对修复是好消息：**若要做链结构校验，只需在这 2 个函数上做，而不是在所有类上做。**
  - ⇒ 也说明"成因 B 若存在，必然是某处**直接 delete 对象而未触发其占用切换虚函数**"——
    这给出了一条明确的（但目前未被证据要求的）查找方向。

- **§837-4 [已证·副产品：`TerrainClass` 在 RTTI 表里是 4 个 COM 接口虚表，不是主表]**
  | 虚表 | `[vt-4]` COL | slot 0 | 判读 |
  |---|---|---|---|
  | `0x007F5200` | `0x0080C370` | `0x004105E0` = `sub dword [esp+4],4; jmp 0x410260` | **adjustor thunk**（调整 this 偏移） |
  | `0x007F521C` | `0x0080C340` | `0x00410590` = `ret 4` | 空实现 |
  | `0x007F5224` | `0x0080C358` | `0x00410580` = `xor al,al; ret 8` | 返回 false |
  | `0x007F522C` | `0x0080C3E0` | `0x00410260` = 返回 `0x80004003`(`E_POINTER`) | **COM 风格接口方法** |
  - ⇒ 这 4 个都是**接口/调整 thunk 表**，`0x00410260` 返回 `0x80004003` 是 COM 的 `E_POINTER`，**不是析构函数**。
  - ⇒ **可复用教训**：`+0x2C` 恰好是 WhatAmI 这条规则在这些接口表上也成立
    （`0x7F522C` 的 `+0x2C` = `0x0071D300` = `mov eax,0x24; ret`），所以**用 WhatAmI 反查类名是可靠的**；
    但**不要**把这些表当成主虚表去读"槽 0 = 析构"，MSVC 的多重继承/COM 接口会让槽 0 变成 thunk。

- **§837-5 [未证·下一步若真要做 ②-b 代码层兜底]** 需要先拿到各类的**主虚表**与其标量删除析构
  （形态：`mov dword [ecx], <vt>; ...; ret N`），本轮的 4 个表都不是。这属新工作量，未开工。
"""

src = io.open(LEDGER, encoding="utf-8").read()
if "## §837" in src:
    sys.exit("ABORT: §837 already present")
n0 = len(src)
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (n0, len(back)))
for k in ("## §837", "类型不可知", "降级"):
    print("  %-12s %d" % (k, back.count(k)))
bad = [(hex(ord(c)), back.count(c)) for c in set(back) if ord(c) < 0x20 and c not in "\r\n\t"]
print("control chars:", bad)
