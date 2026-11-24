# -*- coding: utf-8 -*-
# P02 probe6: 泵队列模式 [0xAA0444] 写者普查 + 写点上下文 —— 判定 WM_ACTIVATEAPP 能否到达 WndProc
import sys, bisect
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
TARGETS = {0xAA0444: "QUEUE_MODE", 0xA8EDA0: "A8EDA0", 0xABFC94: "DLG_FILTER_TBL", 0xABFD34: "CB_PTR"}
hits = {va: [] for va in TARGETS}
for ins in eng.stream:
    try:
        ops = ins.operands
    except Exception:
        continue
    for op in ops:
        if op.type == 3 and op.mem.base == 0 and op.mem.index == 0 and op.mem.disp in hits:
            hits[op.mem.disp].append((ins.address, "W" if (op.access & 2) else "R",
                                      ins.mnemonic, ins.op_str))
            break

for va, name in TARGETS.items():
    print("== %s (%08X): %d refs ==" % (name, va, len(hits[va])))
    for h in hits[va]:
        print("  %08X %s  %s %s" % h)

# 写点上下文
addrs = [i.address for i in eng.stream]
def ctx(va, back=10, fwd=6):
    k = bisect.bisect_right(addrs, va) - 1
    for i in stream_slice(k - back, k + fwd + 1):
        mark = " ->" if i.address == va else "   "
        print("  %s %08X  %-18s %s %s" % (mark, i.address, i.bytes.hex(), i.mnemonic, i.op_str))

def stream_slice(lo, hi):
    lo = max(0, lo); hi = min(len(eng.stream), hi)
    return eng.stream[lo:hi]

print("\n== QUEUE_MODE 写点上下文 ==")
for h in hits[0xAA0444]:
    if h[1] == "W":
        print(" -- writer %08X (%s %s):" % (h[0], h[2], h[3]))
        ctx(h[0])
