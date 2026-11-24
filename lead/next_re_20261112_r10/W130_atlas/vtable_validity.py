#!/usr/bin/env python3
"""W130c: validate the 1305 "RTTI vtables" -- how many are real vtables?

A real MSVC vtable:
  * lives in .rdata/.data (never .text)
  * its slot 0..k are code pointers inside .text
  * [vt-4] is a COL inside .rdata/.data whose pTypeDescriptor points at a
    ".?AV" string

This quantifies the false-positive rate of the inherited RTTI map, which
matters because ledger §646-2 quotes "1,305 vtables" as an established count.
"""
import collections
import json
import os
import struct

import pefile

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
RTTI = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\_lead_rtti_map.json"

pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()
SECS = [(s.Name.rstrip(b"\x00").decode(), ib + s.VirtualAddress,
         ib + s.VirtualAddress + s.Misc_VirtualSize) for s in pe.sections]


def sec_of(va):
    for n, lo, hi in SECS:
        if lo <= va < hi:
            return n
    return None


def u32(va):
    if va < ib or va + 4 > ib + len(img):
        raise ValueError("oob")
    return struct.unpack("<I", img[va - ib:va - ib + 4])[0]


def is_code(v):
    return 0x00401000 <= v < 0x007E038D


rtti = json.load(open(RTTI, encoding="utf-8"))
vt2name = {}
for k, v in rtti["vt2name"].items():
    vt2name[int(k, 16) if str(k).lower().startswith("0x") else int(k)] = v

print("RTTI map vtables: %d" % len(vt2name))

by_sec = collections.Counter()
verdict = collections.Counter()
bad = []
for vt, name in vt2name.items():
    s = sec_of(vt)
    by_sec[s] += 1
    # sanity: first 3 slots must be code
    slots_code = 0
    for i in range(3):
        try:
            v = u32(vt + 4 * i)
        except ValueError:
            break
        if is_code(v):
            slots_code += 1
    col = None
    try:
        col = u32(vt - 4)
    except ValueError:
        pass
    col_ok = col is not None and sec_of(col) in (".rdata", ".data")
    td_ok = False
    if col_ok:
        try:
            ptd = u32(col + 0x0C)
            if sec_of(ptd) in (".data", ".rdata"):
                nm = img[ptd + 0x08 - ib: ptd + 0x08 - ib + 8]
                td_ok = nm.startswith(b".?AV") or nm.startswith(b".?AU")
        except (ValueError, IndexError):
            pass

    if s in (".rdata", ".data") and slots_code == 3 and col_ok and td_ok:
        verdict["VALID"] += 1
    elif s == ".text":
        verdict["FALSE(text)"] += 1
        if len(bad) < 8:
            bad.append((vt, name, "in .text"))
    else:
        why = []
        if s not in (".rdata", ".data"):
            why.append("sec=%s" % s)
        if slots_code < 3:
            why.append("slots_code=%d" % slots_code)
        if not col_ok:
            why.append("col_bad")
        if not td_ok:
            why.append("td_bad")
        verdict["SUSPECT"] += 1
        if len(bad) < 16:
            bad.append((vt, name, ",".join(why)))

print("\n=== by section ===")
for k, v in by_sec.most_common():
    print("  %-8s %d" % (k, v))

print("\n=== verdict ===")
for k, v in verdict.most_common():
    print("  %-14s %d" % (k, v))

print("\n=== samples of rejected entries ===")
for vt, name, why in bad:
    print("  0x%08X %-40s %s" % (vt, (name or "")[:40], why))

total = sum(verdict.values())
print("\nVALID rate: %d/%d = %.1f%%"
      % (verdict["VALID"], total, 100.0 * verdict["VALID"] / total))

json.dump({"by_section": dict(by_sec), "verdict": dict(verdict)},
          open(os.path.join(HERE, "vtable_validity.json"), "w"), indent=1)
print("\nwrote vtable_validity.json")
