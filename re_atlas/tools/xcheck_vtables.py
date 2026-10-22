"""R1: independent cross-check of vtable addresses cited in the corpus.

The ATLAS quotes a master vtable table. This script re-derives each vtable VA
straight from RTTI output and from the bytes, then reports agreement, so the
knowledge base seeds are not merely copied from prose.

Read-only; prints a report.
"""

import json
import re
import struct

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"
SYMS = ROOT + r"\re_atlas\evidence\rtti\symbols.json"
ATLAS = ROOT + r"\docs\re\ARCHITECTURE_ATLAS.md"


def load_pe(path):
    with open(path, "rb") as fh:
        blob = fh.read()
    e = struct.unpack_from("<I", blob, 0x3C)[0]
    nsec = struct.unpack_from("<H", blob, e + 6)[0]
    opt_size = struct.unpack_from("<H", blob, e + 20)[0]
    opt = e + 24
    image_base = struct.unpack_from("<I", blob, opt + 28)[0]
    tab = opt + opt_size
    secs = []
    for i in range(nsec):
        o = tab + i * 40
        name = blob[o:o + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", blob, o + 8)
        secs.append((name, vaddr, rawsize, rawptr))
    return blob, image_base, secs


BLOB, IB, SECS = load_pe(EXE)


def u32_at(va):
    rva = va - IB
    for name, vaddr, rawsize, rawptr in SECS:
        if vaddr <= rva < vaddr + rawsize:
            return struct.unpack_from("<I", BLOB, rawptr + (rva - vaddr))[0]
    return None


def in_text(va):
    rva = va - IB
    for name, vaddr, rawsize, rawptr in SECS:
        if name == ".text" and vaddr <= rva < vaddr + rawsize:
            return True
    return False


def hx(v):
    if v is None:
        return None
    return int(v, 16) if isinstance(v, str) else int(v)


def main():
    d = json.load(open(SYMS, encoding="utf-8"))
    classes = {}
    for key, c in d["classes"].items():
        c = dict(c)
        c["vtable_va"] = hx(c.get("vtable_va"))
        classes[c["name"]] = c
    print(f"# rtti classes={len(classes)}  image_base={d['image_base']}")

    # structural sanity: every vtable[0] must point into .text
    ok = bad = 0
    for c in classes.values():
        vt = c.get("vtable_va")
        if not vt:
            continue
        f0 = u32_at(vt)
        if f0 is not None and in_text(f0):
            ok += 1
        else:
            bad += 1
    print(f"# vtable[0] resolves into .text: {ok}/{ok + bad}")

    # cross-check the ATLAS master table (name -> vtable VA)
    atlas_pairs = {}
    pat = re.compile(r"\|\s*\*\*`([A-Za-z_][A-Za-z0-9_]*)`\*\*\s*\|\s*\*\*`0x([0-9A-Fa-f]{8})`\*\*\s*\|")
    for line in open(ATLAS, encoding="utf-8", errors="replace"):
        m = pat.search(line)
        if m:
            atlas_pairs[m.group(1)] = int(m.group(2), 16)
    print(f"# atlas vtable rows parsed: {len(atlas_pairs)}")

    agree = disagree = missing = 0
    for name, va in sorted(atlas_pairs.items()):
        c = classes.get(name)
        if not c or not c.get("vtable_va"):
            missing += 1
            print(f"  MISS  {name:22s} atlas=0x{va:08X}  (no rtti vtable)")
            continue
        rva_vt = c["vtable_va"]
        if rva_vt == va:
            agree += 1
        else:
            disagree += 1
            print(f"  DIFF  {name:22s} atlas=0x{va:08X}  rtti=0x{rva_vt:08X}")
    print(f"# ATLAS vs RTTI vtable: agree={agree} differ={disagree} missing={missing}")


main()
