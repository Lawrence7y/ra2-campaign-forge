#!/usr/bin/env python3
"""Correct §829's novelty claim: §629 (2026-11-14) already established the
EIP=0 signature (S4), the 0x47C4D0 `ret 8` sibling and the +0x2C=WhatAmI method.

What is genuinely new here must be stated narrowly.
"""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
src = io.open(LEDGER, encoding="utf-8").read()
n0 = len(src)


def rep(old, new, tag):
    global src
    c = src.count(old)
    if c != 1:
        sys.exit("ABORT %s: count=%d" % (tag, c))
    src = src.replace(old, new)


# 1) heading: drop the false novelty claim
rep("## §829 · **项目内其实有 3 种崩溃签名（不是 1 种）；占多数的 `EIP=0` 已定位到格链遍历 ⇒ ②-b 首次获得指令级实证**（2026-11-15 11:00）",
    "## §829 · **三种崩溃签名的独立复现 + 三点增量（WhatAmI 36=TerrainClass、102 份日志统计、占比）；⚠️ 并非首次发现 —— §629 已定案**（2026-11-15 11:00）",
    "heading")

# 2) insert the attribution block right after the heading
old_anchor = """- **§829-1 [已证·普查范围与方法]**"""
new_anchor = """- **§829-0 [已证·⚠️ 归因更正（过程失误，登记）]**
  - 我写下本条初稿时主张"②-b **首次**获得指令级实证"，并把它当成新发现。**这是错的。**
    `§629`（2026-11-14）早已把同一个现场定案为 **S4**：
    > `EIP=0`、`Access=0`、「堆指针 `0x10D6E7A0` 的**假虚表槽值恰为 0** ⇒ "函数指针=0"，**不是**"vptr=0"」，
    > 并明确指出 **S3/S4 用的正是"`ret 8` 兄弟版 `0x47C4D0`（wanted-id=`0x24`）"** —— 与我这次反汇编出的函数**是同一个**。
    `§629-2` 也已用同样的 `mov eax,N; ret` 方法确立 **`+0x2C = WhatAmI()`**；`§629-3` 已判定"机制至少 3 个，不得合并"。
  - **失误性质**：写新节前没有先按关键字（`EIP=0` / `0x47C4D0` / `0x24`）检索台账既存结论，
    导致把旧结论当新发现。**这正是本项目反复出现的"未先查既有证据"型失误**，与 §625-2-ERR 同类。
  - **本条的真实增量**（只这三条，其余一律归 §629）：
    1. **`WhatAmI 0x24(36) = .?AVTerrainClass@@`** —— §629 只写到"wanted-id=`0x24`"，未定类；
    2. **102 份日志的去重统计与占比**（`EIP=0` 最多、`0x724737` 次之、`0x6F40A2` 第三）——
       §629 是逐现场分诊，没有做过全项目普查与占比；
    3. **寄存器同型统计**：20 份内容各异的 `EIP=0` 日志中，被当虚表的 `EAX` **全部落在映像所有段之外**，
       且节点 `ESI` 落在 `0x15B4DEE0–0x15CADEE0`、**低 16 位恒为 `DEE0`**。

- **§829-1 [已证·普查范围与方法]**"""
rep(old_anchor, new_anchor, "attribution")

io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = io.open(LEDGER, encoding="utf-8").read()
print("chars %d -> %d" % (n0, len(back)))
for k in ("§829-0", "§629 已定案", "TerrainClass", "首次获得指令级实证"):
    print("  %-20s %d" % (k, back.count(k)))
