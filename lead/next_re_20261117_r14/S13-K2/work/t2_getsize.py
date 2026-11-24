#!/usr/bin/env python3
"""T2 GetSize double-point closure for 4 S13 classes + constant reads.
Channel A: vtable slot bytes B8 imm32 C3 (imm = size).
Channel B: ctor push<size> -> operator new 0x7C8E17.
Do NOT assume slot 12; report all B8-imm32-C3 slots (WhatAmI vs size).
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
import re_lib as R

# (name, vftable_base, n_slots, whatami_expected, size_expected)
CLASSES = [
    ("WeaponTypeClass",   0x7F73B8, 27,  0x31, 0x160),
    ("WarheadTypeClass",  0x7F6B30, 27,  0x32, 0x1D0),
    ("BulletTypeClass",   0x7E4948, 40,  0x09, 0x2F8),
    ("BulletClass",       0x7E46E4,125,  0x08, 0x160),
]

print("=== constants ===")
for va in (0x7e3808, 0x7e2224, 0x7e2800):
    b = R.read(va, 8)
    d = struct.unpack("<d", b)[0]
    print(f"  @0x{va:08X}: bytes={b.hex()} double={d!r}")

print("\n=== operator new call sites 0x7C8E17 (E8 rel32) ===")
new_addr = 0x7C8E17
# find E8 rel32 targeting new_addr across .text
text_start, text_end = 0x401000, 0x401000+0x3DF38D
o0 = R.va_to_off(text_start); o1 = R.va_to_off(text_end)
data = R.DATA
hits = []
for i in range(o0, o1-4):
    if data[i] == 0xE8:
        rel = struct.unpack("<i", data[i+1:i+5])[0]
        cs = R.IB + 0x1000 + (i - o0)  # call site VA
        if cs + 5 + rel == new_addr:
            hits.append(cs)
print("  E8->0x7C8E17 call sites:", len(hits))

# For each call site, look backwards up to 12 bytes for push size (6A imm8 / 68 imm32 / C7 04 24 imm32)
def push_before(cs):
    res = []
    for back in range(1, 16):
        va = cs - back
        b = R.read(va, back+5)
        # try to decode push at 'va' such that it ends at cs (or before with padding)
        # 6A xx (push imm8)
        if R.u8(va) == 0x6A and va+2 == cs:
            res.append((va, "push imm8", R.u8(va+1)))
        if R.u8(va) == 0x68 and va+5 == cs:
            res.append((va, "push imm32", R.u32(va+1)))
        if R.read(va,3) == b"\xc7\x04\x24" and va+7 == cs:
            res.append((va, "mov [esp],imm32", R.u32(va+3)))
    return res

# Collect all push immediates that equal any expected size
expected_sizes = {0x160:"Weapon/Bullet",0x1D0:"Warhead",0x2F8:"BulletType"}
print("\n  push-immediate -> operator new, grouped by size (expected sizes highlighted):")
from collections import defaultdict
by_size = defaultdict(list)
for cs in hits:
    for va, kind, imm in push_before(cs):
        if imm is not None:
            by_size[imm].append((cs, va, kind))
for imm in sorted(by_size):
    mark = " <== EXPECTED "+expected_sizes[imm] if imm in expected_sizes else ""
    locs = by_size[imm]
    sample = ", ".join(f"cs0x{c:X}({k}@0x{v:X})" for c,v,k in locs[:6])
    print(f"    size 0x{imm:X} ({imm}) x{len(locs)}{mark}: {sample}")

print("\n=== vtable slot scan: all B8 imm32 C3 slots ===")
for name, vt, ns, wa, sz in CLASSES:
    print(f"\n-- {name} vftable=0x{vt:08X} n={ns} expected WhatAmI=0x{wa:X} size=0x{sz:X}")
    found = []
    for i in range(ns):
        fva = R.u32(vt + i*4)
        if fva is None: continue
        b = R.read(fva, 5)
        if len(b)==5 and b[0]==0xB8 and b[4]==0xC3:
            imm = struct.unpack("<I", b[1:5])[0]
            found.append((i, fva, imm))
    for i, fva, imm in found:
        tag=[]
        if imm==wa: tag.append("WhatAmI")
        if imm==sz: tag.append("SIZE")
        print(f"    slot{i:3d} (+0x{i*4:X}) func=0x{fva:08X} imm=0x{imm:X}({imm})  {'/'.join(tag)}")
    # slot12 explicitly
    f12 = R.u32(vt+12*4)
    b12 = R.read(f12,5) if f12 else b""
    print(f"    slot12 func=0x{f12:08X} bytes={b12.hex()}")
