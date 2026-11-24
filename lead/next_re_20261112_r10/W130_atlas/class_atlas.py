#!/usr/bin/env python3
"""W130a: full CLASS ATLAS for gamemd.exe.

For every RTTI-known vtable produce:
  vtable VA | class name | COL addr | COL.offset | is_primary | slot_count |
  whatami (from slot +0x2C when it is `mov eax,N; ret`) | whatami_impl

MSVC CompleteObjectLocator layout (verified against known vtables):
    +0x00 signature
    +0x04 offset            <- 0 => this is the PRIMARY vtable of the class
    +0x08 cdOffset
    +0x0C pTypeDescriptor   -> +0x08 inline char[] ".?AV<Class>@@"
    +0x10 pClassDescriptor
(An earlier scratch script printed +0x10 as "offset"; that is pClassDescriptor.)

Slot count: vtables are emitted contiguously in .rdata/.data, so a vtable's extent
runs to the next vtable start (or to the first non-code dword). Both are computed
and the conservative min is reported, flagged when they disagree.

Outputs (in this dir):
  class_atlas.tsv    one row per vtable
  class_atlas.json   class -> {vtables:[{vt,primary,slots,whatami}], ...}
  class_atlas.log    summary + self-checks
"""
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
SECTIONS = [(s.Name.rstrip(b"\x00").decode(), ib + s.VirtualAddress,
             ib + s.VirtualAddress + s.Misc_VirtualSize) for s in pe.sections]


def in_image(va):
    return any(lo <= va < hi for _n, lo, hi in SECTIONS)


def sec_of(va):
    for n, lo, hi in SECTIONS:
        if lo <= va < hi:
            return n
    return None


def u32(va):
    off = va - ib
    if off < 0 or off + 4 > len(img):
        raise ValueError("out of image 0x%08X" % va)
    return struct.unpack("<I", img[off:off + 4])[0]


def is_code(va):
    return 0x00401000 <= va < 0x007E038D


def is_data_ptr(va):
    s = sec_of(va)
    return s in (".rdata", ".data")


def col_fields(col):
    return {
        "signature": u32(col + 0x00),
        "offset": u32(col + 0x04),
        "cd_offset": u32(col + 0x08),
        "p_td": u32(col + 0x0C),
        "p_chd": u32(col + 0x10),
    }


def td_name(p_td):
    """TypeDescriptor: +0x00 vftable ptr, +0x04 spare, +0x08 inline name."""
    if not in_image(p_td):
        return None
    raw = img[p_td + 0x08 - ib: p_td + 0x08 - ib + 256]
    name = raw.split(b"\x00")[0]
    try:
        return name.decode("ascii")
    except UnicodeDecodeError:
        return None


def whatami_of(vt):
    """slot +0x2C; implementation `B8 imm32 C3` => imm32 (at fn+1)."""
    try:
        fn = u32(vt + 0x2C)
    except ValueError:
        return None, None
    if not is_code(fn):
        return None, fn
    b = img[fn - ib: fn - ib + 8]
    if len(b) >= 6 and b[0] == 0xB8:
        # `mov eax, imm32` ; accept ret (C3) or `ret imm16` (C2) right after
        if b[5] in (0xC3, 0xC2):
            return struct.unpack("<I", b[1:5])[0], fn
    return None, fn


def main():
    rtti = json.load(open(RTTI, encoding="utf-8"))
    vt2name = {}
    for k, v in rtti["vt2name"].items():
        vt2name[int(k, 16) if str(k).lower().startswith("0x") else int(k)] = v

    vts = sorted(vt2name)
    print("RTTI-known vtables: %d" % len(vts))

    rows = []
    for i, vt in enumerate(vts):
        col = u32(vt - 4)
        try:
            cf = col_fields(col) if in_image(col) else {}
        except ValueError:
            cf = {}
        name = td_name(cf["p_td"]) if cf.get("p_td") else vt2name[vt]
        offset = cf.get("offset")
        primary = (offset == 0)

        # slot count: (a) distance to next vtable, (b) run of code/data pointers
        nxt = vts[i + 1] if i + 1 < len(vts) else None
        by_next = ((nxt - vt) // 4) if nxt else None
        run = 0
        while run < 200:
            try:
                v = u32(vt + 4 * run)
            except ValueError:
                break
            if is_code(v) or (is_data_ptr(v) and v > 0x10000):
                run += 1
            else:
                break
        slots = min(x for x in (by_next, run) if x is not None) if (by_next or run) else None
        ami, impl = whatami_of(vt)

        rows.append({
            "vt": vt, "class": name, "col": col, "col_offset": offset,
            "primary": primary, "slots": slots, "slots_by_next": by_next,
            "slots_by_run": run, "whatami": ami, "whatami_impl": impl,
            "section": sec_of(vt),
        })

    # ---------- self checks ----------
    print("\n=== self-checks ===")
    ok = True
    # 1. the three known class ids from the ledger must come out right
    for want_name, want_ami in (("BuildingClass", 6), ("CellClass", 11),
                                ("TerrainClass", 36), ("BulletClass", 8),
                                ("InfantryClass", 15)):
        hit = [r for r in rows if r["class"] and want_name in r["class"]
               and r["whatami"] == want_ami]
        good = bool(hit)
        ok &= good
        print("  WhatAmI %-3d -> %-16s : %s (%d vtables)"
              % (want_ami, want_name, "OK" if good else "MISS", len(hit)))
    # 2. BuildingClass primary vtable must be 0x007E3EBC (ledger §2.5)
    bc = [r for r in rows if r["class"] == ".?AVBuildingClass@@"]
    prim = [r["vt"] for r in bc if r["primary"]]
    print("  BuildingClass vtables=%d primary=%s (expect 0x007E3EBC) : %s"
          % (len(bc), ["0x%08X" % p for p in prim],
             "OK" if 0x007E3EBC in prim else "MISMATCH"))
    ok &= (0x007E3EBC in prim)
    # 3. classes with no primary table (should be 0 or explainable)
    by_class = {}
    for r in rows:
        by_class.setdefault(r["class"], []).append(r)
    no_prim = [c for c, rs in by_class.items() if not any(x["primary"] for x in rs)]
    print("  classes total=%d   classes without a primary vtable=%d"
          % (len(by_class), len(no_prim)))
    # 4. whatami coverage
    with_ami = sum(1 for r in rows if r["whatami"] is not None)
    print("  vtables with WhatAmI resolved: %d/%d" % (with_ami, len(rows)))

    # ---------- outputs ----------
    tsv = os.path.join(HERE, "class_atlas.tsv")
    with open(tsv, "w", encoding="utf-8") as f:
        f.write("vt\tclass\tprimary\tcol_offset\tslots\twhatami\tsec\tcol\twhatami_impl\n")
        for r in sorted(rows, key=lambda r: r["vt"]):
            f.write("0x%08X\t%s\t%d\t%s\t%s\t%s\t%s\t0x%08X\t%s\n" % (
                r["vt"], r["class"], 1 if r["primary"] else 0,
                "" if r["col_offset"] is None else "0x%X" % r["col_offset"],
                "" if r["slots"] is None else r["slots"],
                "" if r["whatami"] is None else r["whatami"],
                r["section"] or "",
                r["col"], "" if r["whatami_impl"] is None else "0x%08X" % r["whatami_impl"]))

    js = {"classes": {}, "stats": {}}
    for c, rs in by_class.items():
        js["classes"][c] = {
            "whatami": next((x["whatami"] for x in rs if x["whatami"] is not None), None),
            "vtables": [{"vt": "0x%08X" % x["vt"], "primary": x["primary"],
                         "slots": x["slots"]} for x in sorted(rs, key=lambda y: y["vt"])],
        }
    js["stats"] = {"vtables": len(rows), "classes": len(by_class),
                   "with_whatami": with_ami,
                   "classes_without_primary": len(no_prim)}
    json.dump(js, open(os.path.join(HERE, "class_atlas.json"), "w"), indent=1)

    print("\nwrote class_atlas.tsv / class_atlas.json")
    print("SELF-CHECKS:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
