#!/usr/bin/env python3
"""W130i: reconcile three vtable sets and pick the canonical one, with evidence.

Sets:
  A = inherited  _lead_rtti_map.json            (1,305)
  B = my rebuild vtables_rebuilt.json           (1,219)
  C = strict per the DeepSeek audit:
        [vt-4] points into .rdata/.data
        COL.signature in {0, -1}
        COL.pTypeDescriptor (+0x0C) in .rdata/.data and [+8..] starts .?AV/.?AU
        vtable itself NOT in .text and NOT in .rsrc
        at least the first slot is a code pointer
Report pairwise diffs with reasons so the canonical count is justified, not voted.
"""
import json
import os
import struct

import pefile

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OLD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\_lead_rtti_map.json"

pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()
SECS = []
for s in pe.sections:
    SECS.append((s.Name.rstrip(b"\x00").decode(), ib + s.VirtualAddress,
                 ib + s.VirtualAddress + s.Misc_VirtualSize,
                 ib + s.VirtualAddress + s.SizeOfRawData))
TEXT_LO, TEXT_HI = 0x00401000, 0x007E038D


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
        raise ValueError("no bytes at 0x%08X" % va)
    return struct.unpack("<I", img[va - ib: va - ib + 4])[0]


def is_code(v):
    return TEXT_LO <= v < TEXT_HI


def td_name(ptd):
    raw = img[ptd + 0x08 - ib: ptd + 0x08 - ib + 256]
    s = raw.split(b"\x00")[0]
    try:
        return s.decode("ascii")
    except UnicodeDecodeError:
        return None


def strict_scan():
    """Set C: scan for COL pointers with the strict two-condition test."""
    out = {}
    stats = {"scanned": 0, "ptr_in_data": 0, "sig_ok": 0, "td_ok": 0,
             "slot0_code": 0, "reject_text": 0, "reject_rsrc": 0}
    for sname in (".rdata", ".data"):
        n, lo, hi, raw = next(x for x in SECS if x[0] == sname)
        pos = lo
        while pos + 4 <= raw:
            stats["scanned"] += 1
            try:
                col = u32(pos)
            except ValueError:
                pos += 4
                continue
            if sec_of(col) in (".rdata", ".data"):
                stats["ptr_in_data"] += 1
                try:
                    sig = u32(col + 0x00)
                    ptd = u32(col + 0x0C)
                except ValueError:
                    pos += 4
                    continue
                if sig in (0, 0xFFFFFFFF):
                    stats["sig_ok"] += 1
                    if sec_of(ptd) in (".rdata", ".data"):
                        nm = td_name(ptd)
                        if nm and (nm.startswith(".?AV") or nm.startswith(".?AU")):
                            stats["td_ok"] += 1
                            vt = pos + 4
                            sv = sec_of(vt)
                            if sv == ".text":
                                stats["reject_text"] += 1
                            elif sv == ".rsrc":
                                stats["reject_rsrc"] += 1
                            elif is_code(u32(vt)):
                                stats["slot0_code"] += 1
                                out[vt] = {"col": col, "class": nm, "sig": sig,
                                           "col_offset": u32(col + 0x04),
                                           "section": sv}
            pos += 4
    return out, stats


mine = {v["vt"]: v for v in json.load(open(os.path.join(HERE, "vtables_rebuilt.json"),
                                           encoding="utf-8"))["vtables"]}
old = {}
for k, v in json.load(open(OLD, encoding="utf-8"))["vt2name"].items():
    old[int(k, 16) if str(k).lower().startswith("0x") else int(k)] = v

C, stats = strict_scan()
print("=== strict scan stats ===")
for k, v in stats.items():
    print("  %-14s %d" % (k, v))
print("\nset sizes:  A(inherited)=%d   B(my rebuild)=%d   C(strict)=%d"
      % (len(old), len(mine), len(C)))

print("\n=== A vs C ===")
print("  A only: %d   (in .text: %d, in .rsrc: %d, other: %d)"
      % (len(set(old) - set(C)),
         sum(1 for v in set(old) - set(C) if sec_of(v) == ".text"),
         sum(1 for v in set(old) - set(C) if sec_of(v) == ".rsrc"),
         sum(1 for v in set(old) - set(C)
             if sec_of(v) not in (".text", ".rsrc"))))
print("  C only: %d" % len(set(C) - set(old)))
print("\n=== B vs C ===")
print("  B only: %d   C only: %d" % (len(set(mine) - set(C)), len(set(C) - set(mine))))
for v in sorted(set(C) - set(mine))[:10]:
    print("     C-only 0x%08X %s (sec=%s)" % (v, C[v]["class"][:44], C[v]["section"]))

# name agreement on the common set
both = set(mine) & set(C)
diff = [(v, mine[v]["class"], C[v]["class"]) for v in both if mine[v]["class"] != C[v]["class"]]
print("\n  B∩C = %d, class-name disagreements = %d" % (len(both), len(diff)))
for v, b, c in diff[:5]:
    print("     0x%08X B=%s C=%s" % (v, b[:40], c[:40]))

# canonical = C
canon = {"vtables": [{"vt": vt, **C[vt]} for vt in sorted(C)],
         "stats": {"count": len(C), "classes": len({x["class"] for x in C.values()}),
                   "primary": sum(1 for x in C.values() if x["col_offset"] == 0)}}
json.dump(canon, open(os.path.join(HERE, "vtables_canonical.json"), "w"), indent=1)
print("\nwrote vtables_canonical.json  (count=%d classes=%d primary=%d)"
      % (canon["stats"]["count"], canon["stats"]["classes"], canon["stats"]["primary"]))
