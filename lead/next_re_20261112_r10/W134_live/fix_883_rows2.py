#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix the two stale statements in §882-5 using short anchors only."""
import io

LED = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
s = io.open(LED, encoding="utf-8", newline="").read()

# 1) table row: replace the fragment that calls it a light path
FRAG1 = "但走 `0x6474C7` 的轻路径）|"
NEW1 = "⚠️ **§883 已展开：`0x6474C7` 不是轻路径，是按模式分派的事件泵入口**）|"
n1 = s.count(FRAG1)
if n1 == 1:
    s = s.replace(FRAG1, NEW1)
    print("ok: table row fixed")
else:
    print("WARN: frag1 count %d" % n1)

# 2) limits item: rewrite the whole line by locating its prefix
PREFIX = "  1. **`0x6474C7` 这条"
i = s.find(PREFIX)
if i < 0:
    print("WARN: limits item not found")
else:
    eol = s.find("\n", i)
    old_line = s[i:eol]
    new_line = ("  1. \u2192 **§883 已展开**：`0x6474C7` 是按 `[0xA8B238]`（模式 0..5）分派的入口，"
                "内含事件环形缓冲的**生产者**（111 字节/条 + `timeGetTime` 时间戳 + 16,384 项环），"
                "末尾**无条件**调消费者 `0x64C380`（2,474 B，遍历全环）。")
    s = s[:i] + new_line + s[eol:]
    print("ok: limits item replaced")
    print("   was:", old_line[:70])

io.open(LED, "w", encoding="utf-8", newline="\n").write(s)
bad = [(i, hex(ord(c))) for i, c in enumerate(s) if ord(c) < 32 and c not in "\n\t"]
print("ledger size=%d control chars=%d" % (len(s.encode("utf-8")), len(bad)))
