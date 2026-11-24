#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix the stale §853 entry-table row in the handover (line 85)."""
import io

HAND = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\SESSION_HANDOVER_R10.md"
h = io.open(HAND, encoding="utf-8", newline="").read()

OLD = ("| **`0x006DD8B0`** | **游戏状态机分派器**（`case 1` = 游戏内逻辑） | "
       "`Sleep(1000)`、`TAction.CPP`、`switch(*(obj+0x2C))` |")
NEW = ("| ~~**`0x006DD8B0`**~~ | ~~游戏状态机分派器~~ → **§880 已证否：是 `TActionClass` 触发器动作执行器**，"
       "`[+0x2C]` 是动作码 | `Sleep(1000)`、`TAction.CPP`（**决定性**） |")

n = h.count(OLD)
if n != 1:
    raise SystemExit("REFUSE: row found %d times" % n)
h = h.replace(OLD, NEW)
io.open(HAND, "w", encoding="utf-8", newline="").write(h)
print("ok: §853 row in handover corrected")
bad = [(i, hex(ord(c))) for i, c in enumerate(h) if ord(c) < 32 and c not in "\n\t"]
print("handover size=%d control chars=%d" % (len(h.encode("utf-8")), len(bad)))
