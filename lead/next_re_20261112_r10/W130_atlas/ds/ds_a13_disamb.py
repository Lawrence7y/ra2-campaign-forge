#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A13: disambiguate the 185.  A 'mov eax,N; ret' hit is only a real WhatAmI if
the target is a genuine FUNCTION ENTRY, not a COL pointer / data dword."""
from __future__ import annotations
import json
from collections import Counter
from ds_img import BASE, IMG, SECS, in_raw, is_exec, u32, rd, secname

J = json.loads(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\_lead_rtti_map.json",
                    encoding="utf-8").read())
vt = {int(k, 16): v for k, v in J["vt2name"].items()}
keys = set(vt)
cols = {u32(k - 4) for k in keys}

# which .text addresses are real function entries? use the CDG: a .text VA referenced
# as a slot elsewhere is a function entry; a COL pointer is not.
slot_refs = Counter()
for k in keys:
    a = k
    for i in range(0, 0x80, 4):
        v = u32(k + i)
        if v is None or not is_exec(v):
            break
        slot_refs[v] += 1

print("=== the 185: separate genuine fn entries from COL-pointer coincidences ===")
gen, colref = [], []
for k, n in vt.items():
    fn = u32(k + 0x2C)
    if fn is None or not is_exec(fn):
        continue
    b = rd(fn, 6)
    if not (b[0] == 0xB8 and b[5] in (0xC3, 0xC2)):
        continue
    (colref if fn in cols else gen).append((k, n, fn))

print("  parse as mov eax,N;ret AND target is NOT a COL :", len(gen))
print("  parse as mov eax,N;ret BUT target IS a COL ptr :", len(colref))
print()
print("=== the 'target IS a COL' ones: what is really at key+0x2C? ===")
for k, n, fn in colref[:12]:
    b = rd(fn, 6)
    n_ = int.from_bytes(b[1:5], "little")
    print(f"  key=0x{k:08X} {n[:38]:<38} +2C=0x{fn:08X} (=COL of {vt.get(fn+4, '?')[:28]})"
          f"  bytes={b.hex()}  'mov eax,0x{n_:X}'")
print()
print("  => the .text dword 0x0080xxxx is ALSO a legitimate `mov eax,0x80xxxx` opcode")
print("     pattern because 0x80 is the LEA/imm signature. Show 3 of them in context:")
for k, n, fn in colref[:3]:
    print(f"  --- 0x{fn:08X} ---")
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    for ins in md.disasm(rd(fn - 6, 24), fn - 6):
        print(f"      0x{ins.address:08X} {ins.bytes.hex():<18}{ins.mnemonic} {ins.op_str}")

print()
print("=== genuine WhatAmI (target not a COL): N distribution ===")
vals = Counter()
for k, n, fn in gen:
    vals[int.from_bytes(rd(fn + 1, 4), "little")] += 1
print("  distinct N:", len(vals), "min", min(vals), "max", max(vals))
print("  N < 200 :", sorted(x for x in vals if x < 200))
print("  N >= 200:", sorted(x for x in vals if x >= 200)[:20], "...")

print()
print("=== does +0x2C give the SAME fn for all sub-object tables of one class? ===")
# group by name among genuine
byname = {}
for k, n, fn in gen:
    byname.setdefault(n, set()).add(fn)
multi = {n: f for n, f in byname.items() if len(f) > 1}
print("  class names with >1 distinct WhatAmI fn among genuine:", len(multi))
for n, f in list(multi.items())[:12]:
    print(f"    {n[:44]:<44} {[hex(x) for x in sorted(f)]}")

print()
print("=== final P3 tally (disambiguated) ===")
tally = Counter()
for k, n in vt.items():
    fn = u32(k + 0x2C)
    if fn is None: tally["unreadable"] += 1
    elif fn == 0: tally["NULL"] += 1
    elif not in_raw(fn): tally["BSS (no file bytes)"] += 1
    elif not is_exec(fn):
        s = secname(fn)
        # is it a header COL?
        tally[f"data-{s} (COL header of next table)"] += 1
    else:
        b = rd(fn, 6)
        if b[0] == 0xB8 and b[5] in (0xC3, 0xC2) and fn not in cols:
            tally["GENUINE WhatAmI (mov eax,N;ret)"] += 1
        else:
            tally["ordinary method / not WhatAmI"] += 1
for c, v in tally.most_common():
    print(f"  {c:<46}{v}")
