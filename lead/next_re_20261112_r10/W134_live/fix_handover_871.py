#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Propagate the §871 corrections into the handover."""
import io

HAND = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\SESSION_HANDOVER_R10.md"
h = io.open(HAND, encoding="utf-8", newline="").read()

REPL = [
    # overturned table row
    ("| `.text` 覆盖 **79.5%** | **低估**：真实 **86.39%**（找回 5,875 个函数 / 281,623 B） | **§864** |",
     "| `.text` 覆盖 **79.5%** | **低估**：终值 **91.245%**（找回 5,260 个函数 / 478,736 B）。86.39% 是中途快照 | **§864 / §871** |"),
    ("| 引擎实例数组 **49 个** | **错**：全量枚举得 **142 个**（漏 93 个） | **§867** |",
     "| 引擎实例数组 **49 个** | **错**：全量枚举 **远多于 49**（中间值 142，已被降级 `[未证]`）。`AbstractClass*` 至少 **12 个**（我亲验 3 个） | **§867 / §871** |"),
    # body item 2
    ("2. **`.text` 覆盖率 79.45% → 86.39%**（§864）。找回 5,875 个函数 / 281,623 B。",
     "2. **`.text` 覆盖率 79.45% → 91.245%**（§864 首测 86.39%，**§871 更正为终值**）。\n"
     "   终版 `c2.tsv`：5,260 个函数 / 478,736 B。"),
    ("   我方**全量验证**过：0 个与图谱重叠、0 个自重叠、0 个无法解码、98.4% 以 `ret` 结尾。",
     "   我方**全量验证**过（5,260/5,260）：0 个与图谱重叠、0 个自重叠、0 个无法解码、**99.7% 以 `ret` 结尾**。"),
    # body item 3
    ("3. **实例数组 49 → 142**（§867）。`AbstractClass*` 有 **12 个**、`ObjectClass*` 3 个、",
     "3. **实例数组远多于 49**（§867；确切总数 `[未证]`——子代理收尾时清空了 TSV）。`AbstractClass*` 有 **12 个**、`ObjectClass*` 3 个、"),
]

for old, new in REPL:
    n = h.count(old)
    if n != 1:
        print("WARN: anchor found %d times, skipped: %s" % (n, old[:48]))
        continue
    h = h.replace(old, new)
    print("ok:", old[:48])

# add the caveat about the 'table' evidence class
ANCH = "**两个必须记住的陷阱**"
CAVEAT = """**91.245% 里最需要谨慎的一块**
终版 5,260 条里有 **3,910 条（135,806 B）是 `table` 证据**（"被 `.text` 内跳转表引用"）。
那能证明它是**分派目标**，但**不一定**是一个函数入口（也可能是 case 块）。
这 3,910 条我**未独立复核**，是 91.245% 的不确定来源。其余类别（`prologue` 1,008 / `vtable` 290 / `decoded` 52）
的证据强度已知且已抽验。

"""
if h.count(ANCH) == 1:
    h = h.replace(ANCH, CAVEAT + ANCH)
    print("ok: caveat inserted")
else:
    print("WARN: caveat anchor not unique")

io.open(HAND, "w", encoding="utf-8", newline="").write(h)
bad = [(i, hex(ord(c))) for i, c in enumerate(h) if ord(c) < 32 and c not in "\n\t"]
print("handover size=%d control chars=%d" % (len(h.encode("utf-8")), len(bad)))
