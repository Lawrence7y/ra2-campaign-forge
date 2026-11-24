#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze function attribution for the 179 write sites under 3 function models:
 M1: atlas interval containment [entry, entry+atlas_size)
 M2: entry_at_or_before on atlas entries (nearest earlier entry)
 M3: reconstructed intervals [entry_i, entry_{i+1}) using union(atlas entries, call-rel32 targets)
Also: compare with the lead's EVIDENCE_0x80_enum.txt function set.
"""
import os, sys, json, bisect, re
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r"D:\Project\ra2-campaign-forge"
sys.path.insert(0, os.path.join(ROOT, "lead", "next_re_20261116_r12", "_lead_audit"))
import audit_lib

with open(os.path.join(HERE, "..", "EVIDENCE", "w174_writes.json"), "r", encoding="utf-8") as f:
    D = json.load(f)
writes = D["writesA"]
vas = [d["va"] for d in writes]

# atlas rows
rows, header = audit_lib.load_func_atlas()
atlas_entries = sorted([e for e, _ in rows])
atlas_map = {}
for e, rec in rows:
    try:
        atlas_map[e] = e + int(rec["size"])
    except Exception:
        atlas_map[e] = e

# M1: interval containment using atlas sizes (from writes.json fn field, which used M1)
# but recompute cleanly
def m1(va):
    i = bisect.bisect_right(atlas_entries, va) - 1
    for j in range(i, max(-1, i-256), -1):
        e = atlas_entries[j]
        if e <= va < atlas_map[e]:
            return e
    return None

# M2: entry_at_or_before
def m2(va):
    i = bisect.bisect_right(atlas_entries, va) - 1
    return atlas_entries[i] if i >= 0 else None

# M3: call targets (full .text sweep) union atlas, intervals = consecutive entries
b = audit_lib.Bin()
calls, jmps, stats = audit_lib.sweep_calls(b)
call_targets = sorted([t for t in calls if 0x400000 <= t < 0x500000])
union_entries = sorted(set(atlas_entries) | set(call_targets))
def m3(va):
    i = bisect.bisect_right(union_entries, va) - 1
    return union_entries[i] if i >= 0 else None

# compute distinct function counts and per-site assignments
for name, fn in [("M1 atlas-interval", m1), ("M2 entry_at_or_before", m2), ("M3 union-call-interval", m3)]:
    assigns = [fn(v) for v in vas]
    distinct = sorted(set(a for a in assigns if a is not None))
    none_ct = sum(1 for a in assigns if a is None)
    print("%-24s distinct_fns=%d  unassigned=%d" % (name, len(distinct), none_ct))
    with open(os.path.join(HERE, "..", "EVIDENCE", "w174_attrib_" + name[:2] + ".txt"), "w", encoding="utf-8") as f:
        for d, a in zip(writes, assigns):
            f.write("%08X -> %s\n" % (d["va"], ("%08X" % a) if a else "NONE"))

# parse lead's enumeration for its function set + site set
lead_enum = os.path.join(ROOT, "lead", "next_re_20261116_r12", "_lead_audit", "EVIDENCE_0x80_enum.txt")
lead_fns = set()
lead_sites = set()
with open(lead_enum, "r", encoding="utf-8", errors="replace") as f:
    for line in f:
        m = re.match(r"\s*([0-9A-Fa-f]{6,8})\s+(\d+)\s+\(", line)
        if m:
            lead_fns.add(int(m.group(1), 16))
        m2x = re.match(r"\s*([0-9A-Fa-f]{8})\s+fn=([0-9A-Fa-f]{8})", line)
        if m2x:
            lead_sites.add(int(m2x.group(1), 16))
print("lead enum: distinct_fns=%d  listed_sites=%d" % (len(lead_fns), len(lead_sites)))

# M2 function set
m2fns = set(m2(v) for v in vas)
print("M2 fns == lead fns?", m2fns == lead_fns, " M2-only=%d lead-only=%d" % (
    len(m2fns - lead_fns), len(lead_fns - m2fns)))
if m2fns - lead_fns:
    print("  M2-only:", " ".join("%08X" % x for x in sorted(m2fns-lead_fns)))
if lead_fns - m2fns:
    print("  lead-only:", " ".join("%08X" % x for x in sorted(lead_fns-m2fns)))

# site set equality
setW = set(vas)
print("site set W == lead sites?", setW == lead_sites, " W-only=%d lead-only=%d" % (
    len(setW-lead_sites), len(lead_sites-setW)))
if setW - lead_sites:
    print("  W-only:", " ".join("%08X" % x for x in sorted(setW-lead_sites)))
if lead_sites - setW:
    print("  lead-only:", " ".join("%08X" % x for x in sorted(lead_sites-setW)))

# write stats: total call targets, atlas entries
print("call targets (text range)=%d atlas entries=%d union=%d" % (
    len(call_targets), len(atlas_entries), len(union_entries)))
print("sweep stats:", stats)
