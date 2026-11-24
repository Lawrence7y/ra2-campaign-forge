#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final handover propagation for §873 (case 1) and §874 (140 arrays)."""
import io

HAND = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\SESSION_HANDOVER_R10.md"
h = io.open(HAND, encoding="utf-8", newline="").read()

REPL = [
    # overturned table: arrays row -> 140 lower bound
    ("| 引擎实例数组 **49 个** | **错**：全量枚举 **远多于 49**（中间值 142，已被降级 `[未证]`）。`AbstractClass*` 至少 **12 个**（我亲验 3 个） | **§867 / §871** |",
     "| 引擎实例数组 **49 个** | **错**：终值 **140 个真独立全局（下界）**。`AbstractClass*` 恰好 **12 个**（独立枚举确认） | **§867 / §874** |"),
    # body item 3
    ("3. **实例数组远多于 49**（§867；确切总数 `[未证]`——子代理收尾时清空了 TSV）。`AbstractClass*` 有 **12 个**、`ObjectClass*` 3 个、",
     "3. **实例数组 49 → 140（下界）**（§874）。`AbstractClass*` 有 **12 个**、`ObjectClass*` 3 个、"),
]

for old, new in REPL:
    n = h.count(old)
    if n != 1:
        print("WARN: anchor %d times: %s" % (n, old[:46]))
        continue
    h = h.replace(old, new)
    print("ok:", old[:46])

# ---- add the case-1 correction, which invalidates the ① anchor ----
ANCH = "**91.245% 的证据结构（§872 已按实测更正）**"
CASE1 = """**⚠️ ① 卡顿这条线的锚点是错的（§873）**

`0x006DD8B0` 的 `case 1` **不是每帧模拟**。它是**胜负判定**：只有 14 条指令，做一次比较
（`[obj+0x90]` vs `[edx+0xB8]`），然后调 `0x004FC9E0`（字符串 `TXT_SCENARIO_WON` /
`EVA_MissionAccomplished`）或 `0x004FCBD0`（`TXT_SCENARIO_LOST` / `EVA_MissionFailed`），再 `ret 0x10`。

⇒ **此前所有"基于 `case 1` 是主循环"的推断都建立在错误锚点上。**
⇒ 每帧模拟在分派器的**其它** `state` 值里。唯一的重入点是
`0x006DF0FF`（Trigger 循环）→ `0x007265C0` → 对每个 `[+0x28]` 链表节点**再次调用整个分派器**，静态深度 2。
⇒ **① 至今没有任何可信的静态成本定位**：虚拟调用 11/12 解析不到单一地址；循环体内有数据依赖分支
（`[obj+0x90]`/`[obj+0x74]`/`[obj+0x81]`/`[obj+0x34]`），**看似最重的调用对多数对象可能从不执行**。
这与 §707/§723/§725 一连串"代理指标测 N 测错"是同一机制。

"""
if h.count(ANCH) == 1:
    h = h.replace(ANCH, CASE1 + ANCH)
    print("ok: case-1 correction inserted")
else:
    print("WARN: case-1 anchor not unique")

# ---- add T1's unit-vs-20-dwords trap note ----
TRAP_ANCH = "**两个必须记住的陷阱**"
TRAP_ADD = """**第三条陷阱（§874-4）**：有人在枚举报告里写过「`0x008B4108…0x008B417C` 这 20 个 dword 持有
`VectorClass<ObjectClass*>`」。**实测否掉**：全镜像只有 **3 处** `0x007E192C` 存储
（`0x0087F778`/`0x00A8E360`/`0x00A8ECB8`），`0x008B4108` 收到的是 `0x007E9EA4`（`DynamicVectorClass<UnitClass*>`）。
**`0x008B4108` = `UnitClass::Array` 不受影响。**

"""
if h.count(TRAP_ANCH) == 1:
    h = h.replace(TRAP_ANCH, TRAP_ADD + TRAP_ANCH)
    print("ok: third trap inserted")
else:
    print("WARN: trap anchor not unique")

io.open(HAND, "w", encoding="utf-8", newline="").write(h)
bad = [(i, hex(ord(c))) for i, c in enumerate(h) if ord(c) < 32 and c not in "\n\t"]
print("handover size=%d control chars=%d" % (len(h.encode("utf-8")), len(bad)))
