# -*- coding: utf-8 -*-
"""独立复核 Q2 §2.2 的 6 个序言候选表（只读）。"""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine

def hx(b):
    return b.hex(" ").upper()

e = Engine()
by = e.by()
T, WIN_LO = 0x7CFC9F, 0x7CF000
PROS = [(b"\x55\x8B\xEC\x83\xEC", "push ebp; mov ebp,esp; sub esp,imm8"),
        (b"\x55\x8B\xEC", "push ebp; mov ebp,esp")]
cands = []
for va in range(T, WIN_LO - 1, -1):
    if va not in by:
        continue
    b5 = e.rd(va, 5)
    for sig, desc in PROS:
        if b5[:len(sig)] == sig:
            cands.append((va, desc, hx(e.rd(va, 8)), T - va))
            break
print("[CAND] count =", len(cands))
for va, desc, b8, delta in cands:
    print("[CAND] 0x%08X  %-45s  bytes=%s  delta=0x%X" % (va, desc, b8, delta))
print("[CAND] nearest =", hex(cands[0][0]) if cands else None)
