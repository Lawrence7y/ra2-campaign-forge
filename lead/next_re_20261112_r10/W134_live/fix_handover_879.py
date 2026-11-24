#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Handover: 0x8871E0 verdict + the 15-state per-frame structure."""
import io

HAND = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\SESSION_HANDOVER_R10.md"
h = io.open(HAND, encoding="utf-8", newline="").read()

ANCH = "**⚠️ ① 卡顿这条线的锚点是错的（§873）**"
NEW = """**✅ ① 的结构答案已拿到（§879）**

`0x006DD8B0` 的 `switch` 是**跳转表**：`mov edx,[esi+0x2C]` / `cmp edx,0x90` /
`jmp [edx*4 + 0x006DFDEC]`。表长 **145**（state 0..144），145 项全部有效，**143 个不同目标**。

**其中 15 个 state 各自遍历一种实例数组**：

| state | 遍历 | | state | 遍历 |
|---|---|---|---|---|
| 90 | Infantry | | 51 / 59 / 60 / 61 / 110 | Building |
| 81 / 82 | Foot | | 11 / 21 / 53 | Trigger |
| 83 | Techno | | 88 | ParticleSystem |
| | | | 105 | House |

**没有 `UnitClass`、没有 `AircraftClass`**（载具属 `FootClass`，已被 Foot 覆盖）。

⇒ **不存在"一个每帧主循环"。每帧模拟是 15 路按类型分工、由 `[obj+0x2C]` 运行时选择。**
这正是 ① 调查反复失败的原因——所有努力都预设了单一入口。
⇒ 加上循环体内的数据依赖分支，**静态分析能给的最强结论只到「15 路分工 + 各路遍历谁」，给不出成本排序。**

**调用拓扑**：分派器只有 **1 个**直接调用者 `0x00726605`（在 `0x007265C0` 内）；
`0x007265C0` 有 **5** 个调用者，其中 `0x006DF119` 落在 **Trigger 循环体**内
⇒ **分派器是被逐触发节点重入的，"每帧"由 Trigger 的迭代次数间接实现。**

"""
if h.count(ANCH) == 1 and "① 的结构答案已拿到" not in h:
    h = h.replace(ANCH, NEW + ANCH)
    print("ok: ① structural answer inserted")
else:
    print("WARN: anchor not unique or already present")

# update the open-items entry about 0x6CD8CD
OLD4 = "4. **`0x006CD8CD` 能否真被触发未知**（需知道 `[0x8871E0]` 何时为 0）——决定它算不算真补丁缺口。"
NEW4 = ("4. ~~`0x006CD8CD` 能否真被触发未知~~ → **§878 已定谳**：`[0x8871E0]` 有两条真实 NULL 路径"
        "（`Init.CPP` 创建失败 `0x52BAFA`、关闭时 `0x6BEABD` 置空），站点无守卫 ⇒ **真缺陷**；\n"
        "   但它属**超级武器**路径（`0x6CC390` 内有 `EVA_Chronosphere*`/`EVA_IronCurtain*`/`EVA_NuclearMissile*` 等字符串），\n"
        "   **非常规玩法可触发** ⇒ **不加入本批补丁**，记为已知潜在缺陷。")
if h.count(OLD4) == 1:
    h = h.replace(OLD4, NEW4)
    print("ok: open item 4 resolved")
else:
    print("WARN: open item 4 not unique")

# open item 5 (①) is now answered
OLD5 = "5. **① 的每帧入口仍无锚点**：`case 1` 已排除，真实每帧模拟所在的 `state` 值未定（§873）。"
NEW5 = ("5. ~~① 的每帧入口仍无锚点~~ → **§879 已解**：15 个 state 各遍历一种数组，不存在单一主循环。\n"
        "   **剩下未证的只是**「某一帧实际有哪几个 state 在跑」（运行时数据）。")
if h.count(OLD5) == 1:
    h = h.replace(OLD5, NEW5)
    print("ok: open item 5 resolved")
else:
    print("WARN: open item 5 not unique")

io.open(HAND, "w", encoding="utf-8", newline="").write(h)
bad = [(i, hex(ord(c))) for i, c in enumerate(h) if ord(c) < 32 and c not in "\n\t"]
print("handover size=%d control chars=%d" % (len(h.encode("utf-8")), len(bad)))
