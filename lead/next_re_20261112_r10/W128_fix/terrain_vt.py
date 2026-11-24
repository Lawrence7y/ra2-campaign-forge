#!/usr/bin/env python3
"""W128f: find the REAL TerrainClass primary vtable + its scalar deleting destructor.

0x7F522C turned out to be an interface vtable (slot0 -> 0x410260 returns 0x80004003,
a COM-style E_POINTER), not the primary table. For ②-b 成因 B we need the object's
real destructor to see whether it unlinks from the cell chain.

Method: from the RTTI map, list every vtable whose class name is .?AVTerrainClass@@,
and for each print slots 0..3 plus the WhatAmI slot (+0x2C). A primary vtable's
slot 0 is a scalar deleting destructor whose shape is `mov dword [ecx], <vt>; ...; ret N`.
"""
import json
import struct

import capstone
import pefile

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
RTTI = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\_lead_rtti_map.json"

pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

rtti = json.load(open(RTTI, encoding="utf-8"))
vt2name = {}
for k, v in rtti["vt2name"].items():
    try:
        vt2name[int(k, 16) if str(k).lower().startswith("0x") else int(k)] = v
    except ValueError:
        pass


def u32(va):
    return struct.unpack("<I", img[va - ib:va - ib + 4])[0]


def explain(va, n=6):
    out = []
    for ins in md.disasm(img[va - ib:va - ib + 24], va):
        out.append("%s %s" % (ins.mnemonic, ins.op_str))
        if len(out) >= n:
            break
    return " | ".join(out)


targets = sorted(vt for vt, nm in vt2name.items() if nm == ".?AVTerrainClass@@")
print("vtables named .?AVTerrainClass@@ : %d" % len(targets))
for vt in targets:
    print("\n=== vtable 0x%08X" % vt)
    col = u32(vt - 4)
    print("   [vt-4] COL = 0x%08X" % col)
    try:
        print("   COL+0x10 (offset) = 0x%X" % u32(col + 0x10))
    except Exception:
        pass
    for slot in (0, 1, 2, 3, 11):
        v = u32(vt + 4 * slot)
        tag = "  WhatAmI" if slot == 11 else ""
        print("   slot %2d (+0x%02X) = 0x%08X%s   %s"
              % (slot, 4 * slot, v, tag, explain(v) if 0x400000 <= v < 0x7E038D else "<not code>"))

    # does slot0 look like a scalar deleting dtor? (writes a vtable ptr into [ecx])
    v0 = u32(vt)
    if 0x400000 <= v0 < 0x7E038D:
        first = explain(v0, 4)
        looks = ("mov dword ptr [ecx]" in first) or ("mov dword ptr [eax]" in first) \
                or ("mov dword ptr [esi]" in first) or ("mov dword ptr [edi]" in first)
        print("   slot0 looks like ctor/dtor writing a vptr: %s" % looks)
