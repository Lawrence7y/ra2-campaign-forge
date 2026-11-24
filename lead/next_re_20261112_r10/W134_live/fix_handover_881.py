#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Handover: the real per-frame chain is found (ledger §881)."""
import io

HAND = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\SESSION_HANDOVER_R10.md"
h = io.open(HAND, encoding="utf-8", newline="").read()

OLD_HDR = "**❌ ① 的整个框架已被推翻（§880）—— `0x006DD8B0` 是 `TActionClass`，不是主循环**"
NEW_HDR = "**✅ ① 的真锚点已找回（§881）：`0x6BB9A0` → `0x48CCC0`（Conquer.CPP 主循环）→ `0x55D360`（每帧更新）**"

if h.count(OLD_HDR) != 1:
    raise SystemExit("REFUSE: ① header not found")
h = h.replace(OLD_HDR, NEW_HDR)

ANCHOR = "⇒ **① 卡顿的锚点从 §853 起就错了。此前所有基于「`0x006DD8B0` 是主循环」的逐帧推断全部作废。**"
ADD = """⇒ **① 卡顿的锚点从 §853 起就错了。此前所有基于「`0x006DD8B0` 是主循环」的逐帧推断全部作废。**

---

**但真锚点已经找到（§881）——三环链条闭合**

| 环节 | 地址 | 证据 |
|---|---|---|
| 引擎初始化 | `0x6BB9A0`（10,256 B） | 直接调用主循环两次：`0x6BE041`、`0x6BE061` |
| **游戏主循环** | **`0x48CCC0`**（780 B） | 体内唯一源字符串 **`D:\\ra2mdpost\\Conquer.CPP`** |
| **每帧更新** | **`0x55D360`**（2,940 B） | 在内层循环 `0x48CE8A←0x48CEA8` 被调用；**全镜像唯一 `inc` 型帧推进**（`0xA8ED84`）|

主循环内层（每帧）顺序（我亲自反汇编）：
`0x7241A0`(**②-a 受害例程**, 见 `0x48CE5D`) → `0x69BAB0` → **`0x55D360`(推进一帧)** →
`0x55CFD0` → `0x48C8B0`(Conquer.CPP) → `0x55CFD0` → `je 0x48CE8A`（while !谓词）

⇒ **②-a 的崩溃点就在主循环内层**，与真机 25/26 的现场统计一致。

**每帧成本结构（§881-4）**：全镜像 181 个"引数组+含循环"的函数中，**30 个**从 `0x55D360` 可达
（BFS 深度 ≤4，共 913 个可达函数）。最强候选是 **`0x67D300`**（4,411 B、**111 个回边**、
遍历 7 种数组、无字符串、开头依次驱动 `[0xA8B230]` / `0x8A38E0` / `[0x8871E0]` 单例 + 虚调用）。

⚠️ **`0x64DEA0`（11,242 B）是 SYNC 状态转储**（`SYNC%01d.TXT`、`COORD:...`），可达但很可能被门控
——**门控条件未查**。若未门控而每帧执行，仅它一个就是巨大开销，**这是 ① 最该优先排除的一项**。

⚠️ 仍 `[未证]`：没有做过任何**计时**；可达性用直接调用算，**虚调用不可见**；
`0x67D300` 的调用者 `0x67D1AF` 未定性，「它每帧必跑」未证。
"""
if h.count(ANCHOR) != 1:
    raise SystemExit("REFUSE: 作废 anchor not found")
h = h.replace(ANCHOR, ADD)

# open item 5 refresh
OLD5 = """5. **① 的每帧入口仍然未知**（§880）。`0x006DD8B0` 是 TAction 执行器，**已排除**。
   §853-2 其余入口未逐条复审。**这是本项目最老的未解问题，现在回到「无锚点」状态。**"""
NEW5 = """5. **① 的每帧入口已找到**（§881）：`0x6BB9A0` → `0x48CCC0`(Conquer.CPP) → `0x55D360`(每帧)。
   剩下未证的是**成本排序**（无计时数据、虚调用不可见）与 `0x64DEA0` 的门控条件。"""
if h.count(OLD5) == 1:
    h = h.replace(OLD5, NEW5)
    print("ok: open item 5 refreshed")
else:
    print("WARN: open item 5 not unique")

io.open(HAND, "w", encoding="utf-8", newline="").write(h)
bad = [(i, hex(ord(c))) for i, c in enumerate(h) if ord(c) < 32 and c not in "\n\t"]
print("handover size=%d control chars=%d" % (len(h.encode("utf-8")), len(bad)))
