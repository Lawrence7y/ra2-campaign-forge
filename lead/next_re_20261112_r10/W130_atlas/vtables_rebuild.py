#!/usr/bin/env python3
"""W130d: rebuild the vtable list from the image (no inherited map).

Why: the inherited `_lead_rtti_map.json` puts 87 "vtables" inside .text and has
8-byte-spaced entries claiming to be separate vtable starts for the same class,
which is impossible. Milestone (1) of the atlas needs a self-derived list.

Method (standard MSVC):
  for each 4-aligned address `pos` in .rdata/.data:
      cand = u32(pos)                      # candidate COL pointer
      if cand in .rdata/.data and COL looks sane:
          pTD = u32(cand+0x0C)
          name starts with ".?AV" or ".?AU"
      => vtable_start = pos + 4  (because vtable[-1] holds the COL pointer)
  then validate: slots from 0 upward must be code pointers (or 0 / purecall).

Output: vtables_rebuilt.tsv  (vt, col, class, col_offset, primary, slots, name_ok)
        vtables_rebuilt.json
Also diffs against the inherited map and prints the disagreement classes.
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
    SECS.append({
        "name": s.Name.rstrip(b"\x00").decode(),
        "va": ib + s.VirtualAddress,
        "vend": ib + s.VirtualAddress + s.Misc_VirtualSize,
        "raw_end": ib + s.VirtualAddress + s.SizeOfRawData,
    })
TEXT_LO, TEXT_HI = 0x00401000, 0x007E038D


def blk(va):
    for s in SECS:
        if s["va"] <= va < s["vend"]:
            return s
    return None


def sec_of(va):
    s = blk(va)
    return s["name"] if s else None


def has_bytes(va, n=4):
    """True when va..va+n-1 are backed by file bytes (not BSS)."""
    s = blk(va)
    return bool(s) and (va + n) <= s["raw_end"]


def u32(va):
    if not has_bytes(va):
        raise ValueError("no file bytes at 0x%08X" % va)
    return struct.unpack("<I", img[va - ib: va - ib + 4])[0]


def is_code(v):
    return TEXT_LO <= v < TEXT_HI


def col_ok(col):
    """Return (ok, pTD, cname, offset) for a candidate COL."""
    try:
        if sec_of(col) not in (".rdata", ".data"):
            return False, None, None, None
        offset = u32(col + 0x04)
        ptd = u32(col + 0x0C)
        if sec_of(ptd) not in (".rdata", ".data"):
            return False, None, None, None
        nm = img[ptd + 0x08 - ib: ptd + 0x08 - ib + 8]
        if not (nm.startswith(b".?AV") or nm.startswith(b".?AU")):
            return False, ptd, None, offset
        raw = img[ptd + 0x08 - ib: ptd + 0x08 - ib + 256]
        s = raw.split(b"\x00")[0]
        try:
            return True, ptd, s.decode("ascii"), offset
        except UnicodeDecodeError:
            return False, ptd, None, offset
    except (ValueError, IndexError):
        return False, None, None, None


def slot_run(vt, cap=400):
    """(#slots, first_bad_value, first_bad_kind).

    Terminator rule for THIS image: tables are emitted interleaved as
    {COL, vtable, COL, vtable, ...}, so a table ends at the slot BEFORE a dword
    that is a valid COL pointer (that dword is the next table's [-1]).
    A slot also terminates the table when it is neither code nor 0.
    """
    k = 0
    while k < cap:
        try:
            v = u32(vt + 4 * k)
        except ValueError:
            return k, None, "no-bytes"
        if is_code(v) or v == 0:
            # look ahead: if the NEXT dword is a COL pointer, the table ends here
            try:
                nxt = u32(vt + 4 * (k + 1))
            except ValueError:
                nxt = 0
            ok_col, _p, _n, _o = col_ok(nxt) if sec_of(nxt) in (".rdata", ".data") else (False, None, None, None)
            if ok_col and k > 0:
                return k, nxt, "next-col"
            k += 1
            continue
        kind = "data" if sec_of(v) in (".rdata", ".data") else "other"
        return k, v, kind
    return k, None, "cap"


def main():
    cands = {}
    scanned = 0
    for sname in (".rdata", ".data"):
        s = next(x for x in SECS if x["name"] == sname)
        pos = s["va"]
        end = s["raw_end"]          # only where file bytes exist
        while pos + 4 <= end:
            scanned += 1
            try:
                col = u32(pos)
            except ValueError:
                pos += 4
                continue
            if sec_of(col) in (".rdata", ".data"):
                ok, ptd, name, offset = col_ok(col)
                if ok:
                    cands[pos + 4] = {"col": col, "class": name, "col_offset": offset}
            pos += 4
    print("scanned %d dwords in .rdata/.data; candidate vtables: %d" % (scanned, len(cands)))

    rows = []
    for vt in sorted(cands):
        c = cands[vt]
        run, first_bad, kind = slot_run(vt)
        rows.append({"vt": vt, "col": c["col"], "class": c["class"],
                     "col_offset": c["col_offset"],
                     "primary": c["col_offset"] == 0,
                     "slots": run, "first_bad": first_bad, "bad_kind": kind,
                     "section": sec_of(vt)})

    good = [r for r in rows if r["slots"] >= 2]
    print("vtables with >=2 leading code/null slots: %d" % len(good))
    print("classes: %d" % len({r["class"] for r in rows}))
    print("primary (COL.offset==0): %d" % sum(1 for r in rows if r["primary"]))

    # ---- diff vs inherited map ----
    old = {}
    for k, v in json.load(open(OLD, encoding="utf-8"))["vt2name"].items():
        old[int(k, 16) if str(k).lower().startswith("0x") else int(k)] = v
    new = {r["vt"]: r["class"] for r in rows}
    both = set(old) & set(new)
    only_old = set(old) - set(new)
    only_new = set(new) - set(old)
    print("\n=== diff vs inherited map ===")
    print("  inherited: %d   rebuilt: %d" % (len(old), len(new)))
    print("  common   : %d" % len(both))
    print("  only-in-inherited: %d   (of which in .text: %d)"
          % (len(only_old), sum(1 for v in only_old if sec_of(v) == ".text")))
    print("  only-in-rebuilt  : %d" % len(only_new))
    mismatch = [(v, old[v], new[v]) for v in sorted(both) if old[v] != new[v]]
    print("  same vt, different class: %d" % len(mismatch))
    for v, o, n in mismatch[:10]:
        print("     0x%08X inherited=%-34s rebuilt=%s" % (v, o, n))

    tsv = os.path.join(HERE, "vtables_rebuilt.tsv")
    with open(tsv, "w", encoding="utf-8") as f:
        f.write("vt\tclass\tprimary\tcol_offset\tslots\tbad_kind\tsection\tcol\n")
        for r in rows:
            f.write("0x%08X\t%s\t%d\t0x%X\t%d\t%s\t%s\t0x%08X\n"
                    % (r["vt"], r["class"], 1 if r["primary"] else 0,
                       r["col_offset"], r["slots"], r["bad_kind"] or "",
                       r["section"], r["col"]))
    json.dump({"vtables": [dict(r) for r in rows],
               "stats": {"rebuilt": len(rows), "classes": len({r["class"] for r in rows}),
                         "primary": sum(1 for r in rows if r["primary"]),
                         "inherited": len(old), "common": len(both)}},
              open(os.path.join(HERE, "vtables_rebuilt.json"), "w"), indent=1)
    print("\nwrote vtables_rebuilt.tsv / .json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
