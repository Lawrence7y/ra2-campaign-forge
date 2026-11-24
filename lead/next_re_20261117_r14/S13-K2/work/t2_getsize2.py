#!/usr/bin/env python3
"""T2 GetSize closure v2: fix B8-imm32-C3 detect to 6 bytes; verify ctor/vptr ownership."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
import re_lib as R

CLASSES = [
    ("WeaponTypeClass",  0x7F73B8, 27, 0x31, 0x160, 0x772FF6, 0x772900),
    ("WarheadTypeClass", 0x7F6B30, 27, 0x32, 0x1D0, 0x75E406, 0x75CEC0),
    ("BulletTypeClass",  0x7E4948, 40, 0x09, 0x2F8, 0x46C484, 0x46BB80),
    ("BulletClass",      0x7E46E4,125, 0x08, 0x160, 0x6C50BC, 0x466380),
]

print("=== vtable B8 imm32 C3 slots (read 6 bytes) ===")
for name, vt, ns, wa, sz, pushva, ctor in CLASSES:
    found=[]
    for i in range(ns):
        fva = R.u32(vt+i*4)
        if fva is None: continue
        b = R.read(fva,6)
        if len(b)==6 and b[0]==0xB8 and b[5]==0xC3:
            imm=struct.unpack("<I",b[1:5])[0]
            tags=[]
            if imm==wa: tags.append("WhatAmI")
            if imm==sz: tags.append("SIZE")
            found.append((i,fva,imm,"/".join(tags)))
    print(f"\n-- {name} vt=0x{vt:X} n={ns}: {len(found)} B8imm32C3 slots")
    for i,f,imm,t in found:
        print(f"    slot{i:3d}(+0x{i*4:03X}) f=0x{f:08X} imm=0x{imm:X}({imm}) {t}")

print("\n=== factory push sites ===")
for name, vt, ns, wa, sz, pushva, ctor in CLASSES:
    print(f"\n-- {name} push@0x{pushva:X} ctor=0x{ctor:X}")
    print(R.dump(pushva-8, 0x40))

print("\n=== ctor heads (vptr write C7 06/C7 07 xx vt) ===")
for name, vt, ns, wa, sz, pushva, ctor in CLASSES:
    print(f"\n-- {name} ctor=0x{ctor:X} expected vtable=0x{vt:X}")
    print(R.dump(ctor, 0x30))
