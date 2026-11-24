#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Correct the handover caveat: 'table' evidence is strong (ledger §872)."""
import io

HAND = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\SESSION_HANDOVER_R10.md"
h = io.open(HAND, encoding="utf-8", newline="").read()

OLD = """**91.245% 里最需要谨慎的一块**
终版 5,260 条里有 **3,910 条（135,806 B）是 `table` 证据**（"被 `.text` 内跳转表引用"）。
那能证明它是**分派目标**，但**不一定**是一个函数入口（也可能是 case 块）。
这 3,910 条我**未独立复核**，是 91.245% 的不确定来源。其余类别（`prologue` 1,008 / `vtable` 290 / `decoded` 52）
的证据强度已知且已抽验。
"""

NEW = """**91.245% 的证据结构（§872 已按实测更正）**

| 证据 | 条数 | 强度 |
|---|---:|---|
| `table` —— `.data\\0x812004` 的函数指针表 | 3,910 | **强** |
| `prologue` —— 紧跟 `CC`/`90` 填充的序言 | 1,008 | 中 |
| `vtable` —— canonical 虚表槽 | 290 | **强** |
| `decoded` —— atlas 函数内解出的 rel32 目标 | 52 | **强** |

**"`table` 是软肋"这条警告是我搞错了，已作废。** 我亲自验了那张表：**3,944 项、严格递增、
100% 16 字节对齐、全项落在 `.text`、前 400 项全部在 1 KB 内以 `ret`/`jmp` 终止**。
它不是 case 块集合，每一项都是合法函数入口。⇒ **80.8%（4,252/5,260）有强证据。**

**真正的软肋是残留的 271,058 B（6.676%）**：那只是「没有 STRONG 证据能确立入口」，
**不等于「那里没函数」**——是保守选择，不是结论。

**另外两条（子代理自述，我认同）**：那 12,916 行 atlas 本身也不能证明完整；5,260 个地址是**暂定**结论，
**不写回 `function_atlas.tsv`**（合并会改所有下游分母，且证据尚未经第二方法复核）。

**一条值得记住的方法学**：直接把 `E8`/`E9` 字节扫描当证据会产出 6,428 个"函数"（中位数 29 字节），
几乎全是指令操作数噪声。必须做 STRONG/WEAK 分级。这与 §865-5 同源：**「我扫到了」≠「它是真的」**。
"""

n = h.count(OLD)
if n != 1:
    raise SystemExit("REFUSE: caveat anchor found %d times" % n)
h = h.replace(OLD, NEW)

# overturned-table row for coverage: keep 91.245% but strengthen the basis note
OLD_ROW = "| `.text` 覆盖 **79.5%** | **低估**：终值 **91.245%**（找回 5,260 个函数 / 478,736 B）。86.39% 是中途快照 | **§864 / §871** |"
NEW_ROW = "| `.text` 覆盖 **79.5%** | **低估**：终值 **91.245%**（找回 5,260 函数 / 478,736 B，80.8% 有强证据）。86.39% 是中途快照 | **§864 / §871 / §872** |"
if h.count(OLD_ROW) == 1:
    h = h.replace(OLD_ROW, NEW_ROW)
    print("ok: overturned-table row updated")
else:
    print("WARN: row not updated")

io.open(HAND, "w", encoding="utf-8", newline="").write(h)
bad = [(i, hex(ord(c))) for i, c in enumerate(h) if ord(c) < 32 and c not in "\n\t"]
print("handover: caveat replaced; size=%d control chars=%d" % (len(h.encode("utf-8")), len(bad)))
