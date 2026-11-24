#!/usr/bin/env python3
"""Dump key T2 byte regions: Verses loader/ctor, damage chain, armor name table, default string."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import re_lib as R

def sec(title, va, nbytes, count=0):
    print("\n===== %s  @ 0x%08X (%s) =====" % (title, va, R.section_of(va)))
    print(R.dump(va, nbytes, count))

# Verses loader region (S13-K1/S13-F1: 0x75DE0C mov ebp,0xB, 0x75DE48 fstp qword)
sec("Verses loader loop", 0x75DDC0, 0xC0)
# Warhead type ctor (S13-K1: rep movsd 0x14, 0x3FF00000)
sec("Warhead ctor candidate", 0x75E3B0, 0x100)
# GetTotalDamage 0x489180  (fmul @0x48923D)
sec("GetTotalDamage", 0x489180, 0x100)
sec("GetTotalDamage fmul vicinity", 0x489210, 0x60)
# ReceiveDamage 0x701900 around 0x701D40 (Armor read @0x701D59, call GetTotalDamage @0x701D64)
sec("ReceiveDamage armor/damage", 0x701D40, 0x50)
# armor name table 0x7E5210
print("\n===== armor name table @ 0x7E5210 (.rdata) =====")
for i in range(12):
    a = 0x7E5210 + i*4
    v = R.u32(a)
    if v is None:
        break
    # read C string at v
    s = b""
    p = v
    for _ in range(40):
        c = R.u8(p)
        if c is None or c == 0:
            break
        s += bytes([c]); p += 1
    print(f"  [{i:2d}] @0x7E5210+{i*4:02X} -> 0x{v:08X}  '{s.decode('latin1')}'")
# Verses default string @0x847C40
print("\n===== default Verses string @ 0x847C40 (.data) =====")
p = 0x847C40
s = b""
for _ in range(160):
    c = R.u8(p)
    if c is None or c == 0:
        break
    s += bytes([c]); p += 1
print("  bytes:", s)
print("  text :", s.decode("latin1"))
