#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add a forward pointer at §857-5 item 6, because §859 overturns it."""
import io

P = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
s = io.open(P, encoding="utf-8", newline="").read()

OLD = "  6. §853 找到的 `DAT_00a8eb44`（疑似单位主表）**未真机验证**。"
NEW = (
    "  6. §853 找到的 `DAT_00a8eb44`（疑似单位主表）**未真机验证**。\n"
    "     - ⇒ **已被 §859 推翻**：它不是单位主表，而是 **`BuildingClass::Array.Items`**；\n"
    "       真正的单位清单是 `UnitClass::Array` @ `0x008B4108`（Count `0x008B4118`）。见 §859-1。\n"
    "       本条由「未验证」改写为「**类型已证、数值未验**」（§859-7-2）。"
)

n = s.count(OLD)
if n != 1:
    raise SystemExit("REFUSE: expected exactly 1 occurrence of the §857-5 item 6 line, found %d" % n)

s = s.replace(OLD, NEW)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("patched §857-5 item 6 -> points at §859")
print("size now %d bytes" % len(s.encode("utf-8")))
