#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A14: the N>=200 outliers of the 'genuine WhatAmI' set.  Real WhatAmI returns a
small ordinal; N in the 8.5M range suggests the target is NOT WhatAmI."""
from __future__ import annotations
import json
from collections import Counter
import capstone
from ds_img import BASE, IMG, SECS, in_raw, is_exec, u32, rd, secname

J = json.loads(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\_lead_rtti_map.json",
                    encoding="utf-8").read())
vt = {int(k, 16): v for k, v in J["vt2name"].items()}
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

big = []
for k, n in vt.items():
    fn = u32(k + 0x2C)
    if fn is None or not is_exec(fn):
        continue
    b = rd(fn, 6)
    if b[0] == 0xB8 and b[5] in (0xC3, 0xC2):
        nv = int.from_bytes(b[1:5], "little")
        if nv >= 200:
            big.append((k, n, fn, nv))

print("=== mov eax,N;ret with N>=200:", len(big), "===")
d = Counter((f, n) for k, nm, f, n in big)
print("  distinct (fn,N) pairs:", len(d))
for (f, nv), c in d.most_common(10):
    print(f"    fn=0x{f:08X} N={nv:<10} (0x{nv:08X})  count={c}")

print()
print("=== are these real function entries? disassemble in context ===")
for (f, nv), c in d.most_common(3):
    print(f"  --- 0x{f:08X}  bytes={rd(f-8,24).hex()} ---")
    for ins in md.disasm(rd(f - 8, 28), f - 8):
        mark = "  <<< slot+0x2C target" if ins.address == f else ""
        print(f"     0x{ins.address:08X} {ins.bytes.hex():<20}{ins.mnemonic} {ins.op_str}{mark}")

print()
print("=== are those N values actually POINTERS (i.e. the 'ret' is a coincidence)? ===")
for (f, nv), c in d.most_common(8):
    print(f"  fn=0x{f:08X} N=0x{nv:08X} -> section of N = {secname(nv)}  "
          f"readable={in_raw(nv)}")

print()
print("=== whose vtables are they? ===")
for (f, nv), c in d.most_common(6):
    ks = [nm for k, nm, ff, nn in big if ff == f and nn == nv]
    print(f"  fn=0x{f:08X} N=0x{nv:08X}: ", sorted(set(ks))[:6])

print()
print("=== so do these keys have a REAL WhatAmI elsewhere in the table? scan all slots ===")
cnt = Counter()
for (f, nv), c in list(d.most_common(3)):
    k0 = [k for k, nm, ff, nn in big if ff == f and nn == nv][0]
    print(f"\n  key=0x{k0:08X} {vt[k0]} full slot scan:")
    for i in range(0, 0x3C, 4):
        v = u32(k0 + i)
        s = secname(v) if v else "-"
        note = ""
        if v and is_exec(v):
            b = rd(v, 6)
            if b[0] == 0xB8 and b[5] in (0xC3, 0xC2):
                note = f"  mov eax,{int.from_bytes(b[1:5],'little')}"
        print(f"    +0x{i:02X} 0x{v:08X} {s:<10}{note}")

print()
print("=== FINAL: restrict 'genuine WhatAmI' to N<200 and recount ===")
g = [(k, n, u32(k + 0x2C)) for k, n in vt.items()
     if (u32(k + 0x2C) is not None and is_exec(u32(k + 0x2C))
         and (rd(u32(k + 0x2C), 6)[0] == 0xB8)
         and (rd(u32(k + 0x2C), 6)[5] in (0xC3, 0xC2)))]
small = [x for x in g if int.from_bytes(rd(x[2] + 1, 4), "little") < 200]
print(f"  mov-eax-ret total={len(g)}   with N<200={len(small)}")
print(f"  => the ledger's 185 mixes in {len(g) - len(small)} false 'mov eax,IMM32;ret' "
      f"where IMM32 is a POINTER, not a class ordinal")
