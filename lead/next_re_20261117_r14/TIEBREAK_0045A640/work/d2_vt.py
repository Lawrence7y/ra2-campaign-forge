"""d2_vt.py — the two holding tables of 0045A640, from raw .rdata bytes.

Three independent length rules are reported so that "table length 7" does not
depend on one definition:
  R1 terminator : first slot whose dword is 0
  R2 COL-boundary: first slot whose dword is a valid COL ( -> TD -> mangled name);
                   the underlying layout is [COL][slots...][COL][slots...], so the
                   next table's COL word IS the word right after the last slot.
  R3 successor : distance to the next discovered table start in .rdata
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import open_pe

HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.join(os.path.dirname(HERE), "EVIDENCE")

VT_DV = 0x007E44F4
VT_V = 0x007E4514
TARGET = 0x0045A640


def is_col(pe, value, rdata_lo, rdata_hi):
    if not (rdata_lo <= value < rdata_hi):
        return None
    try:
        td = pe.u32(value + 0xC)
    except SystemExit:
        return None
    if not (rdata_lo <= td < rdata_hi):
        return None
    nm = pe.cstr(td + 8)
    if nm and (nm.startswith(".?AV") or nm.startswith(".?AU")):
        return dict(col=value, td=td, name=nm)
    return None


def main():
    pe = open_pe()
    rd = next(s for s in pe.sections if s["name"] == ".rdata")
    rdata_lo = pe.image_base + rd["vaddr"]
    rdata_hi = rdata_lo + rd["vsize"]

    # TypeDescriptors live in .data here, NOT in .rdata, so a COL test that
    # requires TD to be inside .rdata finds zero tables.  Build the TD set from
    # the mangled names themselves instead: TD+8 is the inline name string, so
    # every ".?AV"/".?AU" occurrence marks TD = that address - 8.
    td_set = set()
    for pat in (b".?AV", b".?AU"):
        i = -1
        while True:
            i = pe.buf.find(pat, i + 1)
            if i < 0:
                break
            va = None
            for s in pe.sections:
                if s["rawptr"] <= i < s["rawptr"] + s["rawsize"]:
                    va = pe.image_base + s["vaddr"] + (i - s["rawptr"])
                    break
            if va is not None:
                td_set.add(va - 8)      # TD+8 is the inline name -> TD = name-8
    td_va = td_set

    def col_ok(col):
        if not (rdata_lo <= col < rdata_hi):
            return None
        try:
            td = pe.u32(col + 0xC)
        except SystemExit:
            return None
        return td if td in td_va else None

    # discover every vtable start in .rdata: a 4-byte aligned address T whose
    # preceding dword [T-4] is a valid COL (COL -> TD -> mangled name).  The
    # layout is [COL][slot0..slotN][COL][slot0..], so this enumerates table
    # starts without knowing any lengths in advance.
    starts = []
    va = rdata_lo + 4
    while va < rdata_hi - 4:
        if col_ok(pe.u32(va - 4)):
            starts.append(va)
        va += 4
    starts = sorted(set(starts))

    out = []
    out.append(f"# .rdata {rdata_lo:#010x}..{rdata_hi:#010x}  discovered vtable starts = {len(starts)}")
    out.append("")

    info = {}
    for vt in (VT_DV, VT_V):
        rtti = pe.rtti_of_vtable(vt)
        r1 = r2 = None
        vals = []
        for i in range(0, 64):
            w = pe.u32(vt + 4 * i)
            colrec = col_ok(w)
            vals.append(dict(idx=i, at=vt + 4 * i, value=w, col=bool(colrec)))
            if w == 0 and r1 is None:
                r1 = i
            if colrec and r2 is None:
                r2 = i
            if r1 is not None and r2 is not None:
                break
        nxt = [s for s in starts if s > vt]
        nxt = nxt[0] if nxt else None
        r3 = ((nxt - 4 - vt) // 4) if nxt else None
        info[vt] = dict(rtti=rtti, values=vals, R1=r1, R2=r2, R3=r3, next_vt=nxt)

        out.append(f"## vtable {vt:#010x}")
        out.append(f"   RTTI : COL={rtti.get('col'):#010x} TD={rtti.get('td'):#010x}")
        out.append(f"          name = {rtti.get('name')}")
        out.append(f"   R1 terminator(0) at slot {r1}")
        out.append(f"   R2 next-COL at slot {r2}  (value {vals[r2]['value']:#010x} if r2 is not None)"
                   if r2 is not None else "   R2 next-COL : none within 64 slots")
        out.append(f"   R3 successor table {nxt and format(nxt,'#010x')} => slots = {r3}")
        out.append("   slots:")
        for v in vals:
            if v["idx"] > max(x for x in (r1 if r1 is not None else 0,
                                          r2 if r2 is not None else 0)) + 1:
                break
            mark = ""
            if v["value"] == TARGET:
                mark = "   <== 0045A640  (slot1)"
            if v["col"]:
                mark = "   <== COL of the NEXT table, not a slot"
            out.append(f"     [{v['idx']}] {v['at']:#010x} = {v['value']:#010x}{mark}")
        out.append("")

    out.append("## raw hexdump 007E44E0..007E4540")
    out.append(pe.hexdump(0x007E44E0, 0x60))
    out.append("")
    out.append("## cross-check: [007E4510] vs COL of 007E4514")
    out.append(f"   [0x007E4510]           = {pe.u32(0x007E4510):#010x}")
    out.append(f"   COL(007E4514) = [vt-4] = {pe.u32(0x007E4514 - 4):#010x}")
    out.append(f"   equal = {pe.u32(0x007E4510) == pe.u32(0x007E4514 - 4)}")
    out.append("")
    out.append("## global 0x8B3D10")
    out.append(f"   in raw .data bytes? {pe.in_raw(0x8B3D10, 4)}  "
               f"(rawsize 0x6c000 -> the object lives in the zero-filled tail; "
               f"its vptr can only be installed at run time)")

    text = "\n".join(out)
    with open(os.path.join(EV, "vtables.txt"), "w", encoding="utf-8") as f:
        f.write(text + "\n")
    with open(os.path.join(HERE, "vt.json"), "w", encoding="utf-8") as f:
        json.dump({hex(k): v for k, v in info.items()}, f, indent=1, default=str)
    print(text)


if __name__ == "__main__":
    main()
