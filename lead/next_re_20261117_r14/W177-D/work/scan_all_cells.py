#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全图扫描：统计所有 CellClass 的两条链链长分布；找链长>=2 的格；
并列出 vptr->RTTI 名及对象 +0x8C 分布。只读。"""
import sys
from collections import Counter
import w177_core as W
import wb_probe as P
import dsnap as D

pid = W.pid_of()
m = W.Mem(pid)
base = m.u32(P.CELL_ARRAY)
print("pid", pid, "frame", m.u32(W.A_FRAME), "cellArray", hex(base) if base else None)

# map size from S06-K1: width @MapClass+0x14C, height +0x150, count +0x154
mapc = P.MAP_SINGLETON
w = m.u32(mapc + 0x14C)
h = m.u32(mapc + 0x150)
cnt = m.u32(mapc + 0x154)
print("map w,h,count", w, h, cnt)

if not base or not w or not h or w > 512 or h > 512:
    print("bad dims, abort")
    sys.exit(2)

lendist = Counter()
multi = []
for cy in range(h):
    rowbase = base + ((cy << 9) + 0) * 4
    # read row (w dwords) in one shot
    import ctypes
    buf = ctypes.create_string_buffer(w * 4)
    got = ctypes.c_size_t(0)
    if not W.k32.ReadProcessMemory(m.h, ctypes.c_void_p(rowbase), buf, w * 4, ctypes.byref(got)):
        continue
    for cx in range(w):
        cell = int.from_bytes(buf.raw[cx*4:cx*4+4], "little")
        if not cell or cell == P.INVALID_CELL:
            continue
        hA = m.u32(cell + P.CELL_E4)
        hB = m.u32(cell + P.CELL_E8)
        # walk A
        la = 0; seen = set(); p = hA
        while p and la < 32 and (p & 3) == 0 and 0x100000 <= p <= 0x70000000:
            if p in seen: break
            seen.add(p); la += 1; p = m.u32(p + 0x30)
        lb = 0; seen = set(); p = hB
        while p and lb < 32 and (p & 3) == 0 and 0x100000 <= p <= 0x70000000:
            if p in seen: break
            seen.add(p); lb += 1; p = m.u32(p + 0x30)
        lendist[(la, lb)] += 1
        if la >= 2 or lb >= 2:
            multi.append((cx, cy, hex(cell), hex(hA) if hA else None, la, hex(hB) if hB else None, lb))

print("chain length distribution (lenA,lenB):")
for k, v in sorted(lendist.items()):
    print("  ", k, v)
print("cells with any chain >=2:", len(multi))
for r in multi[:40]:
    print("  ", r)
