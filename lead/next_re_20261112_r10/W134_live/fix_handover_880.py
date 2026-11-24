#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Handover: 0x006DD8B0 is TActionClass, not the per-frame state machine (ledger §880)."""
import io

HAND = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\SESSION_HANDOVER_R10.md"
h = io.open(HAND, encoding="utf-8", newline="").read()

# 1) replace the whole "① 的结构答案" block with the corrected finding
START = "**✅ ① 的结构答案已拿到（§879）**"
END = "**⚠️ ① 卡顿这条线的锚点是错的（§873）**"
i = h.find(START)
j = h.find(END)
if i < 0 or j < 0 or j < i:
    raise SystemExit("REFUSE: block markers not found")

NEW = """**❌ ① 的整个框架已被推翻（§880）—— `0x006DD8B0` 是 `TActionClass`，不是主循环**

`0x006DD8B0`（9,530 字节）函数体内**唯一**的源文件字符串是 **`D:\\ra2mdpost\\TAction.CPP`**
⇒ 它是 **`TActionClass`（触发器动作）执行器**，**不是游戏状态机、也不是每帧模拟调度器**。

```asm
006DD8D7  mov  edx,[esi+0x2C]        ; TAction 动作码（不是 WhatAmI）
006DD8DA  dec  edx                   ; 码值 = 表索引 + 1
006DD8DB  cmp  edx,0x90              ; 144 个动作分支
006DD8E7  jmp  [edx*4 + 0x006DFDEC]  ; 跳转表
```

**为什么不是 WhatAmI**：`WhatAmI` 实测值域 **1..73**（YRpp `AbstractType` 枚举止于 73），
而这里上界 **144**。⚠️ 台账 §846-7 说「WhatAmI 真值 **144** 个类」——那是**类的数量**，
不是值域上界，**两个 144 毫无关系**，别被这个巧合骗到。

**`this` 的来路**：唯一调用者 `0x007265C0` 沿 `+0x28` 遍历一条**动作链表**，对每个动作调一次执行器。

**§879 那 15 个「遍历数组」的分支**：数字有效，但含义是
**某些 TAction 动作需要「对全场某一类对象操作」**（如「销毁所有建筑」），
`Building ×5`、`Trigger ×3`、`Foot ×2`、`Infantry`/`Techno`/`ParticleSystem`/`House` 各 1
**是动作种类数，不是每帧更新轮次**。

⇒ **① 卡顿的锚点从 §853 起就错了。此前所有基于「`0x006DD8B0` 是主循环」的逐帧推断全部作废。**
⇒ **真正的每帧模拟入口：仍未知。** 本轮只能确定「不是它」。
§853-2 的其它入口（初始化/载入类）定性来自字符串与导入，与此错误无关，大概率仍成立。

"""
h = h[:i] + NEW + h[j:]
print("ok: ① block replaced")

# 2) overturned table: add the TAction row
ROW_ANCHOR = "| `AbstractClass` 只有 1 个 vptr | **错**：**4 个**（`+0/+4/+8/+0xC`），4 基类多继承 | **§862** |\n"
ROW_NEW = ROW_ANCHOR + (
    "| `0x006DD8B0` 是「游戏状态机分派器 / 主循环」 | **错**：是 **`TActionClass` 触发器动作执行器**"
    "（体内唯一字符串 `TAction.CPP`）；`[+0x2C]` 是**动作码**不是 WhatAmI。① 的锚点作废 | **§880** |\n")
if h.count(ROW_ANCHOR) == 1:
    h = h.replace(ROW_ANCHOR, ROW_NEW)
    h = h.replace("推翻的旧结论（14 条）", "推翻的旧结论（15 条）")
    print("ok: overturned row added (15 条)")
else:
    print("WARN: table anchor not unique")

# 3) open item 5: ① is now "anchor destroyed, unknown"
OLD5 = """5. ~~① 的每帧入口仍无锚点~~ → **§879 已解**：15 个 state 各遍历一种数组，不存在单一主循环。
   **剩下未证的只是**「某一帧实际有哪几个 state 在跑」（运行时数据）。"""
NEW5 = """5. **① 的每帧入口仍然未知**（§880）。`0x006DD8B0` 是 TAction 执行器，**已排除**。
   §853-2 其余入口未逐条复审。**这是本项目最老的未解问题，现在回到「无锚点」状态。**"""
if h.count(OLD5) == 1:
    h = h.replace(OLD5, NEW5)
    print("ok: open item 5 rewritten")
else:
    print("WARN: open item 5 not unique")

io.open(HAND, "w", encoding="utf-8", newline="").write(h)
bad = [(i, hex(ord(c))) for i, c in enumerate(h) if ord(c) < 32 and c not in "\n\t"]
print("handover size=%d control chars=%d" % (len(h.encode("utf-8")), len(bad)))
