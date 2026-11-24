#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remove the two stale lines that contradict the §870 correction."""
import io

HAND = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\SESSION_HANDOVER_R10.md"
h = io.open(HAND, encoding="utf-8", newline="").read()

STALE = (
    "   - **`W128_fix\\entries.json`/`stubs.json`/`sites.json` 是按旧清单生成的，必须重建。**\n"
    "   - 务实建议：**在函数入口守卫**（`ecx==0` 直接返回），而不是逐调用点守卫——\n"
    "     这样 14 个点全覆盖，也避免 §825 的\"崩溃点平移\"。\n"
)

n = h.count(STALE)
if n != 1:
    raise SystemExit("REFUSE: stale block found %d times" % n)
h = h.replace(STALE, "")
io.open(HAND, "w", encoding="utf-8", newline="").write(h)
print("removed the two stale lines")
bad = [(i, hex(ord(c))) for i, c in enumerate(h) if ord(c) < 32 and c not in "\n\t"]
print("control chars:", len(bad))
