#!/usr/bin/env python3
"""W131a: vtable MEMBERSHIP -- which function sits in which (class, slot).

This is evidence layer D for the subsystem map: a function that implements a
virtual method of class X inherits X's subsystem with high confidence.

Reads vtables_canonical.json, walks each table's slots, and writes
  vtable_members.tsv   vt, class, slot, fn_entry, fn_is_code
  fn_class.tsv         fn_entry -> class(es) it implements virtuals for
Also reports how many of the 1,966 function-pointer entries get a class.
"""
import collections
import json
import os
import struct

import pefile

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
CANON = os.path.join(HERE, "vtables_canonical.json")
V2 = os.path.join(HERE, "vtables_v2.json")

pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()
TEXT_LO, TEXT_HI = 0x00401000, 0x007E038D


def u32(va):
    return struct.unpack("<I", img[va - ib: va - ib + 4])[0]


def is_code(v):
    return TEXT_LO <= v < TEXT_HI


canon = json.load(open(CANON, encoding="utf-8"))["vtables"]
slots = {}
for r in json.load(open(V2, encoding="utf-8"))["vtables"]:
    vt = r["vt"] if isinstance(r["vt"], int) else int(r["vt"], 16)
    slots[vt] = r["slots"]

rows = []
fn_classes = collections.defaultdict(set)
fn_slots = collections.defaultdict(list)
n_tables = 0
for r in canon:
    vt = r["vt"] if isinstance(r["vt"], int) else int(r["vt"], 16)
    cls = r["class"]
    n = slots.get(vt) or 0
    n_tables += 1
    for k in range(n):
        try:
            v = u32(vt + 4 * k)
        except ValueError:
            break
        rows.append((vt, cls, k, v, 1 if is_code(v) else 0))
        if is_code(v):
            fn_classes[v].add(cls)
            fn_slots[v].append((cls, k))

print("tables walked: %d   (slot,fn) rows: %d" % (n_tables, len(rows)))
print("distinct code targets in vtables: %d" % len(fn_classes))

with open(os.path.join(HERE, "vtable_members.tsv"), "w", encoding="utf-8") as f:
    f.write("vt\tclass\tslot\tfn\tfn_is_code\n")
    for vt, cls, k, v, ok in rows:
        f.write("0x%08X\t%s\t%d\t0x%08X\t%d\n" % (vt, cls, k, v, ok))

with open(os.path.join(HERE, "fn_class.tsv"), "w", encoding="utf-8") as f:
    f.write("fn\tclasses\tn_slots\n")
    for fn in sorted(fn_classes):
        f.write("0x%08X\t%s\t%d\n" % (fn, ",".join(sorted(fn_classes[fn])),
                                       len(fn_slots[fn])))

# how many functions implement a *primary-table* slot (strongest evidence)?
prim = {r["vt"] if isinstance(r["vt"], int) else int(r["vt"], 16)
        for r in canon if (r.get("col_offset") == 0)}
prim_fns = set()
for vt, cls, k, v, ok in rows:
    if ok and vt in prim:
        prim_fns.add(v)
print("functions implementing a PRIMARY-table slot: %d" % len(prim_fns))

# classes with the most implemented slots (sanity: big hierarchies should dominate)
big = collections.Counter()
for fn, cs in fn_classes.items():
    for c in cs:
        big[c] += 1
print("\n=== classes by number of distinct implementing functions (top 15) ===")
for c, n in big.most_common(15):
    print("  %4d  %s" % (n, c))

print("\nwrote vtable_members.tsv / fn_class.tsv")
