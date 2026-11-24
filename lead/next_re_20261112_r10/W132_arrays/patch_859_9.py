#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Record the set-equality result (§859 addendum) and refresh the marker counts."""
import io

LED = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
HAND = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\SESSION_HANDOVER_R10.md"

ADD = """
- **§859-9 [已证·两项大工作的集合级交叉验证]** 本轮顺手把"二进制自带的 RTTI 类型集合"与
  §849 的类图谱做**集合比较**（不是数量比较）：
  | | 数量 | 差集 |
  |---|---|---|
  | 二进制 `.data` 中全部 TypeDescriptor | **988** | — |
  | `class_atlas_v2.json` 的类 | **988** | — |
  | **atlas 有而二进制没有** | **0** | ∅ |
  | **二进制有而 atlas 没有** | **0** | ∅ |
  - ⇒ **两个集合完全相等**。这是我这两天做的两件最大工作（类图谱 / RTTI 反查）之间的独立互证：
    图谱不是"凑出来的 988"，二进制里也确实只有这 988 个类型；**双向都没有多余项**。
  - ⇒ 也说明 §846/§848 那次"1,305 → 1,214 虚表"的清洗没有误删类型（若误删，差集不会为 0）。

"""

s = io.open(LED, encoding="utf-8", newline="").read()
if "§859-9 " in s:
    raise SystemExit("REFUSE: §859-9 already present")
anchor = "- **§859-8 [已证·产物]**"
if s.count(anchor) != 1:
    raise SystemExit("REFUSE: §859-8 anchor not unique")
s = s.replace(anchor, ADD.rstrip("\n") + "\n\n" + anchor)
io.open(LED, "w", encoding="utf-8", newline="").write(s)
print("ledger: §859-9 added, size %d" % len(s.encode("utf-8")))

# refresh the marker counts in the handover milestone table
h = io.open(HAND, encoding="utf-8", newline="").read()
OLD = "台账 [已证] 1,077 / [未证] 283"
NEW = "台账 [已证] 1,104 / [未证] 288"
if h.count(OLD) != 1:
    raise SystemExit("REFUSE: handover marker-count line not found exactly once")
h = h.replace(OLD, NEW)
io.open(HAND, "w", encoding="utf-8", newline="").write(h)
print("handover: marker counts refreshed")

# recount and report
s2 = io.open(LED, encoding="utf-8").read()
print("[已证] now:", s2.count("[已证"), " [未证] now:", s2.count("[未证"))
