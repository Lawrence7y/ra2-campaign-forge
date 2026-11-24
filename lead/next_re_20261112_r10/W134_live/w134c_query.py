#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W134c: targeted reachability query from the per-frame update 0x55D360.

For each queried function, report the BFS depth at which it is reachable from
the per-frame update (or NOT REACHABLE within the depth cap), plus its shortest
call path so the claim can be checked by hand.

Read-only over the file.
"""
import bisect
from collections import deque

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
IB, TRO, TRAWSZ = 0x400000, 0x1000, 0x3E0000
FRAME = 0x0055D360
MAXD = 6

QUERY = [
    (0x00647260, "SYNC 转储调用者 (site 0x647368 所在)"),
    (0x0064C380, "SYNC 转储调用者 (site 0x64CCBA 所在)"),
    (0x0064DEA0, "SYNC 状态转储本体"),
    (0x0064DAB0, "SONG? 4 数组迭代器"),
    (0x0067D300, "7 数组 / 111 循环 协调器"),
    (0x00650A90, "5 数组迭代器 (也读 sync 标志)"),
    (0x006516F0, "sync OFF 分支调用的函数"),
    (0x0067D1AF, "0x67D300 的唯一调用者"),
]

data = open(EXE, "rb").read()

FNS = []
for ln in open(ATLAS, encoding="utf-8").read().splitlines()[1:]:
    p = ln.split("\t")
    if len(p) >= 2:
        try:
            FNS.append((int(p[0], 16), int(p[1])))
        except ValueError:
            pass
FNS.sort()
STARTS = [a for a, _ in FNS]
SIZE = dict(FNS)


def owner(va):
    i = bisect.bisect_right(STARTS, va) - 1
    if i < 0:
        return None
    a, s = FNS[i]
    return a if s and a <= va < a + s else None


md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False
md.skipdata = True

callees = {}
text = bytes(data[TRO:TRO + TRAWSZ])
for ins in md.disasm(text, IB + TRO):
    if ins.id == 0:
        continue
    home = owner(ins.address)
    if home is None:
        continue
    if ins.mnemonic == "call" and ins.op_str.startswith("0x"):
        callees.setdefault(home, set()).add(int(ins.op_str, 16))

# BFS with parent tracking
depth = {FRAME: 0}
parent = {FRAME: None}
q = deque([FRAME])
while q:
    fn = q.popleft()
    d = depth[fn]
    if d >= MAXD:
        continue
    for t in callees.get(fn, ()):
        if t in depth:
            continue
        depth[t] = d + 1
        parent[t] = fn
        q.append(t)

print("BFS from 0x%X, depth cap %d: %d functions reached" % (FRAME, MAXD, len(depth)))
print()
print("%-10s %-9s %-7s %s" % ("target", "depth", "size", "note"))
for va, note in QUERY:
    d = depth.get(va)
    if d is None:
        print("0x%06X   NOT-REACHABLE  %-7s %s"
              % (va, SIZE.get(va, "?"), note))
        continue
    print("0x%06X   %-13d %-7s %s" % (va, d, SIZE.get(va, "?"), note))
    # print path
    path = []
    cur = va
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    print("            path: " + " -> ".join("0x%X" % p for p in path))
