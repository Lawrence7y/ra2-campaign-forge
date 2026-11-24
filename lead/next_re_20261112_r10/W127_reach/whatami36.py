#!/usr/bin/env python3
"""W127m: which class has WhatAmI == 0x24 (36)?

The EIP=0 crashes are a cell-chain search for a node whose WhatAmI() == 0x24
(EDI is always 0x00000024 in all 20 distinct logs). WhatAmI is vtable slot
+0x2C (handover §2.1). A WhatAmI implementation is the tiny `mov eax,N; ret`.

Method: for every known vtable, read slot +0x2C; if that address starts with
`B8 <imm32> C3` the class's WhatAmI is imm. Collect imm==0x24 class names.
Also print a few other values as a sanity check of the method.
"""
import json
import struct

import pefile

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
RTTI = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\_lead_rtti_map.json"

pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()

rtti = json.load(open(RTTI, encoding="utf-8"))
vt2name = {}
for k, v in rtti["vt2name"].items():
    try:
        vt2name[int(k, 16) if str(k).lower().startswith("0x") else int(k)] = v
    except ValueError:
        pass


def u32(va):
    return struct.unpack("<I", img[va - ib:va - ib + 4])[0]


def whatami_of(vt):
    fn = u32(vt + 0x2C)
    if not (0x00401000 <= fn < 0x007E038D):
        return None, fn
    if img[fn - ib] != 0xB8:                      # mov eax, imm32
        return None, fn
    if img[fn + 5 - ib] != 0xC3:                  # ret
        return None, fn
    return u32(fn + 1), fn


by_ami = {}
for vt in vt2name:
    ami, fn = whatami_of(vt)
    if ami is not None:
        by_ami.setdefault(ami, []).append((vt, vt2name[vt], fn))

print("vtables analysed: %d" % len(vt2name))
print("distinct WhatAmI values found: %d" % len(by_ami))
print("\n=== WhatAmI histogram (top 25) ===")
for ami in sorted(by_ami, key=lambda a: -len(by_ami[a]))[:25]:
    names = sorted({n for _vt, n, _f in by_ami[ami]})
    print("  WhatAmI %3d (0x%02X): %2d vtables  %s"
          % (ami, ami, len(by_ami[ami]), names[:4]))

print("\n=== the one we care about: WhatAmI == 0x24 (36) ===")
for vt, nm, fn in by_ami.get(0x24, []):
    print("  vtable 0x%08X  class=%-28s  WhatAmI impl @0x%08X" % (vt, nm, fn))
if 0x24 not in by_ami:
    print("  (none found via this method)")

print("\n=== sanity: BuildingClass should be 6, Infantry 15 ===")
for want in (6, 15):
    print("  WhatAmI %d -> %s" % (want, sorted({n for _v, n, _f in by_ami.get(want, [])})))
