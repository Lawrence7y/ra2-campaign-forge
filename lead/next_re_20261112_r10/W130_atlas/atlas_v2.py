#!/usr/bin/env python3
"""W130j: class atlas v2 -- fix slot counting using the two rules the GLM audit
established, and verify structural invariants.

Rule set (evidence from W130_atlas/glm/vtable_audit_report.md):
  A table terminates when the NEXT dword is
     (a) a valid COL pointer  (next table's [vt-4]), or
     (b) one of the inter-cluster separator constants that recur in this image
         (0x404E0000 / 0xA2529D39 / 0x3F91DF46 ...), or
     (c) a value that is neither code nor 0.
  Sub-tables are emitted in DESCENDING COL.offset order with the primary
  (offset==0) LAST, so "the class's first vtable" is NOT its primary.

Invariants to check (these are what make the numbers trustworthy):
  I1  every class has exactly one primary vtable
  I2  primary slot count >= every sub-table slot count of the same class
  I3  along the ObjectClass chain, slot counts are non-decreasing
  I4  no vtable has slot count 0
"""
import collections
import json
import os
import struct

import pefile

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
CANON = os.path.join(HERE, "vtables_canonical.json")

pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()
SECS = []
for s in pe.sections:
    SECS.append((s.Name.rstrip(b"\x00").decode(), ib + s.VirtualAddress,
                 ib + s.VirtualAddress + s.Misc_VirtualSize,
                 ib + s.VirtualAddress + s.SizeOfRawData))
TEXT_LO, TEXT_HI = 0x00401000, 0x007E038D

# separator constants observed between vtable clusters (GLM audit item 5)
SEPARATORS = {0x404E0000, 0xA2529D39, 0x3F91DF46, 0x3F91DF46}


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


def is_code(v):
    return TEXT_LO <= v < TEXT_HI


def col_valid(v):
    """is v a plausible COL pointer?"""
    if sec_of(v) not in (".rdata", ".data"):
        return False
    try:
        sig = u32(v)
        ptd = u32(v + 0x0C)
    except ValueError:
        return False
    if sig not in (0, 0xFFFFFFFF):
        return False
    if sec_of(ptd) not in (".rdata", ".data"):
        return False
    nm = img[ptd + 0x08 - ib: ptd + 0x08 - ib + 8]
    return nm.startswith(b".?AV") or nm.startswith(b".?AU")


def slot_count(vt, cap=600):
    """Count slots with the combined terminator rule."""
    k = 0
    why = None
    while k < cap:
        try:
            v = u32(vt + 4 * k)
        except ValueError:
            why = "no-bytes"
            break
        if is_code(v) or v == 0:
            # terminator check on the NEXT dword
            try:
                nxt = u32(vt + 4 * (k + 1))
            except ValueError:
                k += 1
                why = "no-bytes"
                break
            if k > 0 and col_valid(nxt):
                why = "next-col"
                break
            if k > 0 and nxt in SEPARATORS:
                why = "sep-const"
                break
            k += 1
            continue
        why = "data" if sec_of(v) in (".rdata", ".data") else "other"
        break
    return k, why


def main():
    canon = json.load(open(CANON, encoding="utf-8"))
    rows = canon["vtables"]
    print("canonical vtables: %d" % len(rows))

    out = []
    for r in rows:
        vt = r["vt"] if isinstance(r["vt"], int) else int(r["vt"], 16)
        k, why = slot_count(vt)
        out.append({**{kk: vv for kk, vv in r.items() if kk != "vt"},
                    "vt": vt, "slots": k, "term": why})

    print("=== terminator distribution (v2) ===")
    for t, n in collections.Counter(x["term"] for x in out).most_common():
        print("  %-10s %d" % (t, n))

    print("\n=== slot-count buckets (primary only) ===")
    prim = [x for x in out if x.get("col_offset") == 0]
    b = collections.Counter()
    for x in prim:
        s = x["slots"]
        b["1-9" if s < 10 else ("10-29" if s < 30 else ("30-99" if s < 100
                                                        else ("100-199" if s < 200 else "200+")))] += 1
    print("  ", dict(b))

    # ---- invariants ----
    byclass = collections.defaultdict(list)
    for x in out:
        byclass[x["class"]].append(x)
    print("\n=== invariants ===")
    i1 = [c for c, xs in byclass.items() if sum(1 for y in xs if y.get("col_offset") == 0) != 1]
    print("  I1 exactly one primary per class : %s (%d violations)"
          % ("OK" if not i1 else "VIOLATED", len(i1)))
    i4 = [x for x in out if x["slots"] == 0]
    print("  I4 no zero-slot vtable            : %s (%d)" % ("OK" if not i4 else "VIOLATED", len(i4)))
    i2viol = []
    for c, xs in byclass.items():
        ps = [y["slots"] for y in xs if y.get("col_offset") == 0]
        if not ps:
            continue
        others = [y["slots"] for y in xs if y.get("col_offset") != 0]
        if others and max(others) > ps[0]:
            i2viol.append((c, ps[0], max(others)))
    print("  I2 primary >= sub-tables         : %s (%d violations)"
          % ("OK" if not i2viol else "VIOLATED", len(i2viol)))
    for c, p, m in i2viol[:5]:
        print("       %-40s primary=%d max_sub=%d" % (c[:40], p, m))

    # I3: ObjectClass chain monotonicity
    CHAIN = ["TechnoClass", "FootClass", "BuildingClass", "UnitClass",
             "InfantryClass", "AircraftClass"]
    print("\n  I3 ObjectClass chain (primary slot counts):")
    got = {}
    for name in CHAIN:
        for c, xs in byclass.items():
            if c.endswith("AV" + name + "@@"):
                p = [y for y in xs if y.get("col_offset") == 0]
                if p:
                    got[name] = p[0]["slots"]
                    break
    for name in CHAIN:
        print("     %-14s %s" % (name, got.get(name)))
    mono = (got.get("TechnoClass", 0) < got.get("FootClass", 0) and
            all(got.get("FootClass", 0) < got.get(n, 0)
                for n in ("BuildingClass", "UnitClass", "InfantryClass", "AircraftClass")))
    print("     monotonic (base < derived) : %s" % ("OK" if mono else "CHECK"))

    json.dump({"vtables": out}, open(os.path.join(HERE, "vtables_v2.json"), "w"), indent=1)
    print("\nwrote vtables_v2.json")


if __name__ == "__main__":
    main()
