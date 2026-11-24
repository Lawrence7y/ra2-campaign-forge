#!/usr/bin/env python3
"""W150: map vtable VAs to class names using the milestone canonical vtable set."""
import json
import sys

VT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\vtables_canonical.json"
CLS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\class_atlas_v2.tsv"

TARGETS = [0x007EAB58, 0x007EAB3C, 0x007EAB34, 0x007EAB2C,
           0x007EAC08, 0x007EABE8, 0x007EABC8,
           0x007EA6FC, 0x007EA5FC, 0x007EA604, 0x007EA690, 0x007F0064,
           0x007EAB00, 0x007E9E00]

data = json.load(open(VT, encoding="utf-8", errors="replace"))
# figure out the shape
if isinstance(data, dict):
    print("# json top-level keys:", list(data.keys())[:8])
    recs = data.get("vtables", data.get("rows", None))
    if recs is None:
        # maybe mapping va -> info
        recs = []
        for k, v in data.items():
            if isinstance(v, dict):
                d = dict(v)
                d.setdefault("va", k)
                recs.append(d)
else:
    recs = data
print(f"# records = {len(recs)}")
if recs:
    print("# sample record keys:", list(recs[0].keys()))

by_va = {}
for r in recs:
    va = r.get("vt") or r.get("va") or r.get("address") or r.get("vtable")
    if va is None:
        continue
    if isinstance(va, str):
        va = int(va, 16)
    by_va[int(va)] = r

print()
for t in TARGETS:
    r = by_va.get(t)
    if r is None:
        print(f"0x{t:08X}\t<not in canonical vtable set>")
        continue
    print(f"0x{t:08X}\tclass={r.get('class')}\tcol={r.get('col')} "
          f"col_offset={r.get('col_offset')}\tsig={r.get('sig')}")

print()
print("# --- reverse: which vtables share the same 'col' (i.e. same class) ---")
for t in TARGETS:
    r = by_va.get(t)
    if not r:
        continue
    col = r.get("col")
    same = [rec for rec in recs if rec.get("col") == col]
    print(f"0x{t:08X} class={r.get('class')} n_vt_same_col={len(same)} "
          f"vts={[hex(int(x['vt'],16)) for x in same][:8]}")
