#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Correct the §865 severity claim in the handover (see ledger §870)."""
import io

HAND = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\SESSION_HANDOVER_R10.md"
h = io.open(HAND, encoding="utf-8", newline="").read()

OLD = (
    "1. **②-a 修复面 50 → 54，且 `0x7241A0` 从 1 个调用点变成 14 个**（§865）。\n"
    "   **这是唯一有安全后果的修正**：按旧清单打补丁会漏 6 条未守卫路径。\n"
)

NEW = (
    "1. **`0x7241A0` 有 14 个调用点，不是我原先说的 1 个**（§865）。\n"
    "   ⚠️ **但 §870 已自我更正：这不造成补丁缺口。** 补丁是**每函数入口挂钩**\n"
    "   （`entries.json` 6 条 = 6 个函数入口），入口守卫覆盖该函数的**每一次**调用。\n"
    "   所以 `entries.json` / `stubs.json` / `sites.json` **不需要因这条重建**。\n"
    "   错的只是我的**统计口径**（把「调用点数」当「补丁面」讨论），不是补丁本身。\n"
    "   真正待解的仍是两条语义风险：NULL 守卫对**悬空指针**无效；`ecx=0` 时静默返回的后果。\n"
)

n = h.count(OLD)
if n != 1:
    raise SystemExit("REFUSE: anchor found %d times" % n)
h = h.replace(OLD, NEW)
io.open(HAND, "w", encoding="utf-8", newline="").write(h)
print("handover: §865 severity corrected (points at §870)")
bad = [(i, hex(ord(c))) for i, c in enumerate(h) if ord(c) < 32 and c not in "\n\t"]
print("control chars:", len(bad))
