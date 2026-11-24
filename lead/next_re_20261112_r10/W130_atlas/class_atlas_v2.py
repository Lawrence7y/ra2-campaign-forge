#!/usr/bin/env python3
"""W130k: finalize class atlas v2 -- 988 TD classes, 1,214 vtables, evidence tags.

Adds the 34 TD-only interface classes so the atlas count matches the documented
"988 classes = 954 with vtable + 34 interface-only" (ledger §849-2).

Outputs class_atlas_v2.tsv / .json.
"""
import collections
import json
import os
import struct

import pefile

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()
SECS = []
for s in pe.sections:
    SECS.append((s.Name.rstrip(b"\x00").decode(), ib + s.VirtualAddress,
                 ib + s.VirtualAddress + s.Misc_VirtualSize,
                 ib + s.VirtualAddress + s.SizeOfRawData))


def blk(va):
    for n, lo, hi, raw in SECS:
        if lo <= va < hi:
            return n, lo, hi, raw
    return None


def sec_of(va):
    b = blk(va)
    return b[0] if b else None


def has_bytes(va, n=4):
    b = blk(va)
    return bool(b) and (va + n) <= b[3]


def u32(va):
    if not has_bytes(va):
        raise ValueError("no bytes")
    return struct.unpack("<I", img[va - ib: va - ib + 4])[0]


# ---------- 1. every structurally complete TypeDescriptor in the image ----------
# TD: +0x00 = type_info vftable ptr (in .rdata), +0x04 spare (0), +0x08 inline name
tds = {}
for sname in (".data", ".rdata"):
    n, lo, hi, raw = next(x for x in SECS if x[0] == sname)
    pos = lo
    while pos + 0x40 <= raw:
        try:
            vt = u32(pos)
            spare = u32(pos + 4)
        except ValueError:
            pos += 4
            continue
        if sec_of(vt) == ".rdata" and spare == 0:
            nm = img[pos + 8 - ib: pos + 8 - ib + 8]
            if nm.startswith(b".?AV") or nm.startswith(b".?AU"):
                full = img[pos + 8 - ib: pos + 8 - ib + 256].split(b"\x00")[0]
                try:
                    tds.setdefault(full.decode("ascii"), pos)
                except UnicodeDecodeError:
                    pass
        pos += 4
print("structurally complete TDs: %d" % len(tds))

# ---------- 2. canonical vtables ----------
canon = json.load(open(os.path.join(HERE, "vtables_canonical.json"), encoding="utf-8"))
vts = canon["vtables"]
v2 = {v["vt"] if isinstance(v["vt"], int) else int(v["vt"], 16): v
      for v in json.load(open(os.path.join(HERE, "vtables_v2.json"), encoding="utf-8"))["vtables"]}

by_class = collections.defaultdict(list)
for v in vts:
    vt = v["vt"] if isinstance(v["vt"], int) else int(v["vt"], 16)
    by_class[v["class"]].append(vt)

# ---------- 3. build ----------
rows = []
for cls, vtset in by_class.items():
    slots = {vt: v2.get(vt, {}).get("slots") for vt in vtset}
    prim = [vt for vt in vtset if v2.get(vt, {}).get("col_offset") == 0]
    rows.append({
        "class": cls, "kind": "class_with_vtable",
        "n_vtables": len(vtset),
        "primary": prim[0] if prim else None,
        "primary_slots": slots.get(prim[0]) if prim else None,
        "max_sub_slots": max([slots[v] for v in vtset if v not in prim] or [0]),
        "vtables": " ".join("0x%08X" % v for v in sorted(vtset)),
    })
for cls in tds:
    if cls not in by_class:
        rows.append({"class": cls, "kind": "interface_only",
                     "n_vtables": 0, "primary": None, "primary_slots": None,
                     "max_sub_slots": 0, "vtables": ""})

rows.sort(key=lambda r: r["class"])
print("classes with vtable: %d" % sum(1 for r in rows if r["kind"] == "class_with_vtable"))
print("interface-only     : %d" % sum(1 for r in rows if r["kind"] == "interface_only"))
print("TOTAL classes      : %d" % len(rows))

with open(os.path.join(HERE, "class_atlas_v2.tsv"), "w", encoding="utf-8") as f:
    f.write("class\tkind\tn_vtables\tprimary\tprimary_slots\tmax_sub_slots\tvtables\n")
    for r in rows:
        f.write("%s\t%s\t%d\t%s\t%s\t%d\t%s\n"
                % (r["class"], r["kind"], r["n_vtables"],
                   "" if r["primary"] is None else "0x%08X" % r["primary"],
                   "" if r["primary_slots"] is None else r["primary_slots"],
                   r["max_sub_slots"], r["vtables"]))
json.dump({"classes": rows,
           "stats": {"classes_total": len(rows),
                     "with_vtable": sum(1 for r in rows if r["kind"] == "class_with_vtable"),
                     "interface_only": sum(1 for r in rows if r["kind"] == "interface_only"),
                     "vtables": len(vts)}},
          open(os.path.join(HERE, "class_atlas_v2.json"), "w"), indent=1)
print("wrote class_atlas_v2.tsv / .json")

print("\n=== the 34 interface-only classes (sample) ===")
iface = [r["class"] for r in rows if r["kind"] == "interface_only"]
for c in iface[:30]:
    print("   " + c)
