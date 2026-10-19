#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/re_gap_details.py
Detailed analysis of Gap Generator methods, vtable slots, and CellClass shroud logic.
"""
import sys, os, struct, json
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\tools")
from xref_scan import Scanner, classify_names
from re_gap_spysat_deep import read_bytes, read_u32, disasm_func, names, md, base, image

sc = Scanner()
sc.scan()
f2n = classify_names()[1]

def fn_name(a):
    return f2n.get(a, names.get(a, ''))

print("=== VTABLE ENTRIES IN BuildingClass (0x007E3EBC) ===")
# Check vtable around slot 212 and 315-325
bld_vt = 0x007E3EBC
for slot in [211, 212, 213, 315, 316, 317, 318, 319, 320, 321, 322]:
    target = read_u32(bld_vt + slot * 4)
    print(f"  Slot [{slot:3d}] (+0x{slot*4:03X}) = 0x{target:08X} {fn_name(target)}")

print("\n=== XREFS TO GAP METHODS ===")
targets = [
    (0x004555D0, "IsGeneratingGap"),
    (0x004556D0, "v[318]"),
    (0x00455820, "v[317]"),
    (0x00455980, "v[320]"),
    (0x00455A80, "v[319]"),
    (0x00487150, "Cell::inc_7C"),
    (0x00487160, "Cell::dec_7C"),
    (0x00487170, "Cell::inc_AC"),
    (0x00487180, "Cell::dec_AC"),
    (0x00487690, "Cell::sub_487690"),
]
for t, label in targets:
    refs = sc.xrefs.get(t, set())
    print(f"\nXrefs to 0x{t:08X} ({label}): total {len(refs)}")
    for r in sorted(refs):
        # find enclosing function
        import bisect
        idx = bisect.bisect_right(sc.fstart_list, r) - 1
        fn = sc.fstart_list[idx] if idx >= 0 else 0
        print(f"  at 0x{r:08X} inside 0x{fn:08X} {fn_name(fn)}")
