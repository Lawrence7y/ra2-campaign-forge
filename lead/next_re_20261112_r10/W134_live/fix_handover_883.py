#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Handover: the per-frame event pump (ledger §883)."""
import io

HAND = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\SESSION_HANDOVER_R10.md"
h = io.open(HAND, encoding="utf-8", newline="").read()

OLD = """**⇒ ① 的嫌疑清单已收窄为以 `0x67D300` 为主**（4,411 B、111 回边、7 种数组），
路径 `0x55D360 → 0x67CEF0 → 0x67D300`。⚠️ 但 `0x67CEF0` 未定性，**"它每帧必跑"仍未证**；
`0x6474C7`（每帧必走的轻路径）也**未展开**。"""

NEW = """**每帧至少有三类工作（§883 已展开）**

| # | 环节 | 规模 | 说明 |
|---|---|---|---|
| 1 | **帧推进** `0x55D360` | 2,940 B / 90 调用 | 唯一 `inc` 型帧计数器写入 |
| 2 | **事件泵** `0x647260` | 885 B | 按 `[0xA8B238]`（模式 0..5）分派；`0x6474C7` **不是轻路径** |
| 3 | **子系统协调** `0x67CEF0` → `0x67D300` | 4,411 B / 111 回边 / 7 种数组 | 依次驱动 `[0xA8B230]`/`0x8A38E0`/`[0x8871E0]` + 虚调用 |

**事件泵的机制（§883-2/3）**：`0x6474C7` 里有一对**生产者/消费者**共用同一个环形缓冲：
- **生产者**：每条事件 **111 字节** + **`WINMM.dll!timeGetTime`** 时间戳，写入 **16,384 项环**
  （索引 `and 0x3FFF`，步长 37 dword；旁表 `0xA70204` 存时间戳）。该循环由 `[0xA802C8]` 门控。
- **消费者**：`0x64C380`（2,474 B、42 调用、9 循环）**无条件**每帧执行，
  以 `[0x8B41F8]`（事件计数）为循环上界**遍历整个环**，按记录类型（如 `0x1C`）分派。

⚠️ 环形缓冲**有排空路径**（`0x64D990`/`0x652230`/`0x5C46E0`/`0x52D9A0` 等会重置计数与读指针），
所以不会退化成"永久 16,384 次扫描"。但**运行时实际占用率未知** ⇒ 每帧真实成本**未证**。

**⇒ ① 现在有两个并列候选**：事件泵（`0x64C380`，成本 ∝ 事件条数）与
子系统协调器（`0x67D300`，4,411 B / 111 回边）。⚠️ `0x67CEF0` 仍未定性，
**"`0x67D300` 每帧必跑"仍未证**；`0x6474C7` 的 6 个 case 只展开了 1 个。"""

n = h.count(OLD)
if n != 1:
    raise SystemExit("REFUSE: anchor found %d times" % n)
h = h.replace(OLD, NEW)

io.open(HAND, "w", encoding="utf-8", newline="").write(h)
bad = [(i, hex(ord(c))) for i, c in enumerate(h) if ord(c) < 32 and c not in "\n\t"]
print("handover size=%d control chars=%d" % (len(h.encode("utf-8")), len(bad)))
