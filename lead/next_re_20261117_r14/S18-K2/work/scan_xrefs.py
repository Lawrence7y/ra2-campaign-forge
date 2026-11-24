#!/usr/bin/env python3
"""Scan whole .text for E8 (call rel32) / E9 (jmp rel32) targeting a set of addresses."""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S18-K2\work")
import peutil as p

TARGETS = set(int(x, 16) for x in sys.argv[1:]) if len(sys.argv) > 1 else set()

# .text RVA 0x1000, raw 0x1000, size 0x3E0000 -> VA 0x401000..0x7E0000
lo = 0x401000
hi = 0x7E0000
data = p.DATA
out = []
for va in range(lo, hi):
    off = p.va2off(va)
    if off is None or off+5 > len(data):
        continue
    if data[off] in (0xE8, 0xE9):
        rel = int.from_bytes(data[off+1:off+5], 'little', signed=True)
        tgt = va + 5 + rel
        if tgt in TARGETS:
            out.append((va, 'call' if data[off]==0xE8 else 'jmp', tgt))
for va, kind, tgt in out:
    print("%08X  %s -> %08X" % (va, kind, tgt))
print("total xrefs:", len(out))
