# -*- coding: utf-8 -*-
"""A03 probe1: 0xA8B230 全量引用普查 + 写点定位。只读 gamemd.exe。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("== coverage ==", eng.coverage)
print("== sha ==", eng.sha[:16], "...")
print("== .text ==", hex(eng.TLO), "-", hex(eng.THI))

GL = 0x00A8B230
hits = eng.disp_hits(GL)
print("== disp_hits(0xA8B230) total ==", len(hits))
writes = [h for h in hits if h[1] == "W"]
print("== writes ==", len(writes))
for w in writes:
    print("  W @ %08X  %s %s" % (w[0], w[2], w[3]))

# 每个写点前后 6 条指令的窗口
byva = eng.by()
def ctx(va, back=8, fwd=4):
    addrs = sorted(a for a in byva if va - 0x80 <= a <= va + 0x40)
    out = []
    for a in addrs:
        ins = byva[a]
        out.append((a, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    return out

for w in writes:
    print("---- ctx @ %08X ----" % w[0])
    for a, bh, mn, ops in ctx(w[0]):
        mark = " >>>" if a == w[0] else "    "
        print("%s %08X  %-20s %s %s" % (mark, a, bh, mn, ops))
