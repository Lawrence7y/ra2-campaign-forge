#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix the two stale 'light path' statements in §882-5 (now superseded by §883)."""
import io

LED = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
s = io.open(LED, encoding="utf-8", newline="").read()

OLD1 = "  | 每帧**已确认**的直接工作 | `0x55D360` 的 44 个 callee（其中 `0x647260` 每帧必进，但走 `0x6474C7` 的轻路径） |"
NEW1 = ("  | 每帧**已确认**的直接工作 | `0x55D360` 的 44 个 callee；其中 `0x647260` 每帧必进 —— "
        "⚠️ **§883 已展开：`0x6474C7` 不是轻路径**，它是按模式分派的事件泵入口 |")
if s.count(OLD1) == 1:
    s = s.replace(OLD1, NEW1); print("ok: table row fixed")
else:
    print("WARN: row1 %d" % s.count(OLD1))

OLD2 = "  1. **`0x6474C7` 这条\"轻路径\"具体做什么，我未展开**（它每帧必走，可能本身也不轻）。"
NEW2 = ("  1. ~~`0x6474C7` 这条"轻路径"未展开~~ → **§883 已展开**：它是按 `[0xA8B238]`（模式 0..5）分派的入口，"
        "内含事件环形缓冲的**生产者**（111 字节/条 + `timeGetTime` 时间戳 + 16,384 项环），"
        "末尾**无条件**调消费者 `0x64C380`（2,474 B，遍历全环）。")
if s.count(OLD2) == 1:
    s = s.replace(OLD2, NEW2); print("ok: limits item fixed")
else:
    print("WARN: item2 %d" % s.count(OLD2))

io.open(LED, "w", encoding="utf-8", newline="\n").write(s)
bad = [(i, hex(ord(c))) for i, c in enumerate(s) if ord(c) < 32 and c not in "\n\t"]
print("ledger size=%d control chars=%d" % (len(s.encode("utf-8")), len(bad)))
