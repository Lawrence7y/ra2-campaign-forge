#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Handover: SYNC dumping excluded; ① suspect list narrowed (ledger §882)."""
import io

HAND = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\SESSION_HANDOVER_R10.md"
h = io.open(HAND, encoding="utf-8", newline="").read()

OLD = """⚠️ **`0x64DEA0`（11,242 B）是 SYNC 状态转储**（`SYNC%01d.TXT`、`COORD:...`），可达但很可能被门控
——**门控条件未查**。若未门控而每帧执行，仅它一个就是巨大开销，**这是 ① 最该优先排除的一项**。"""

NEW = """✅ **SYNC 转储已排除（§882）**：`0x647260`（每帧更新的深度 1 callee）入口即
`test [0xA8D5F8], 2` / `je 0x6474C7`，而 `[0xA8D5F8]` 在 BSS 默认 0。
两个 SYNC 写手（`0x64DEA0` 11,242 B 写 `SYNC%01d.TXT`；`0x6516F0` 2,417 B 写
`SYNC%01d_%03d.TXT`，均以 `'wt'` 打开）**受命令行开关控制**：
`-MPDEBUG` 置 `[0xB04880]`（Extra sync info ON）、`-ATTRACT` 置 `[0xA8D5F8]|=4`。
**⇒ 正常游戏下两条路径一次都不会被调用，不是每帧开销。**

**顺带拿到完整命令行开关表（23 个）**：`-MPDEBUG` `-ATTRACT` `-DROP=` `-jabber` `-str` `-nostr`
`-noaudio` `-record` `-play` `-?` `-h` `-CD` `-DESTNET` `-SOCKET` `-SPEEDCONTROL` `-DLINK1`
`-NETGEAR` `-NOROUTER` `-STEALTH` `-MESSAGES` `-%dX%d` `-WIN` `-X`。
（此前记录的"只有 3 个开关"是我早期扫描范围太窄，已更正。）

**⇒ ① 的嫌疑清单已收窄为以 `0x67D300` 为主**（4,411 B、111 回边、7 种数组），
路径 `0x55D360 → 0x67CEF0 → 0x67D300`。⚠️ 但 `0x67CEF0` 未定性，**"它每帧必跑"仍未证**；
`0x6474C7`（每帧必走的轻路径）也**未展开**。"""

n = h.count(OLD)
if n != 1:
    raise SystemExit("REFUSE: anchor found %d times" % n)
h = h.replace(OLD, NEW)

OLD2 = """⚠️ 仍 `[未证]`：没有做过任何**计时**；可达性用直接调用算，**虚调用不可见**；
`0x67D300` 的调用者 `0x67D1AF` 未定性，「它每帧必跑」未证。"""
NEW2 = """⚠️ 仍 `[未证]`：没有做过任何**计时**；可达性用直接调用算，**虚调用不可见**。
`0x67D300` 由 **`0x67CEF0`** 调用（BFS 路径已证），但 `0x67CEF0` **未定性** ⇒ 「每帧必跑」未证。
`0x6474C7`（`0x647260` 里每帧必走的轻路径）**未展开**。
`[0xA8D5F8]` 除 `-ATTRACT` 外的另外 5 个写者**未逐条定性**（不能排除运行期置位）。"""
if h.count(OLD2) == 1:
    h = h.replace(OLD2, NEW2)
    print("ok: limits block updated")
else:
    print("WARN: limits block not unique")

io.open(HAND, "w", encoding="utf-8", newline="").write(h)
bad = [(i, hex(ord(c))) for i, c in enumerate(h) if ord(c) < 32 and c not in "\n\t"]
print("handover size=%d control chars=%d" % (len(h.encode("utf-8")), len(bad)))
