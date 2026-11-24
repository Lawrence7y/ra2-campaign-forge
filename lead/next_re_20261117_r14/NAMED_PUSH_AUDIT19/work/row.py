"""Thorough per-row analysis for NAMED_PUSH_AUDIT19."""
import sys, os, bisect
from re_lib import Bin, IMAGEBASE, TEXT_LO, TEXT_HI, fmt_ins

ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"


class Atlas:
    def __init__(self, path=ATLAS):
        self.starts = []
        self.info = {}
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            next(f)
            for line in f:
                p = line.rstrip("\n").split("\t")
                if len(p) < 6:
                    continue
                e = int(p[0], 16)
                self.starts.append(e)
                self.info[e] = {"entry": e, "size": int(p[1]), "n_instr": int(p[2]),
                                "n_callers": int(p[3]), "n_callees": int(p[4]), "is_fnptr": int(p[5])}
        self.starts.sort()

    def at(self, va):
        i = bisect.bisect_right(self.starts, va) - 1
        if i < 0:
            return None
        e = self.starts[i]
        rec = dict(self.info[e])
        rec["offset"] = va - e
        rec["contains"] = rec["offset"] < rec["size"]
        return rec


def classify_writer(b, atl, rec):
    info = {"text": rec["text"], "ins_va": rec["ins_va"], "imm_at": rec["imm_at"], "bytes": rec["bytes"]}
    if rec["ins_va"] is None:
        info["kind"] = "undecodable"
        return info
    f = atl.at(rec["ins_va"])
    info["enclosing"] = f
    info["in_section"] = b.secname(rec["ins_va"])
    ate, p, ins = b.is_atexit_dtor(f["entry"]) if f else (False, None, [])
    info["atexit_registered"] = ate
    if ate:
        info["atexit_evidence"] = ins
    dele, dev = b.is_delete_dtor(f["entry"]) if f else (False, {})
    info["delete_dtor"] = dele
    info["delete_evidence"] = dev
    if ate:
        info["kind"] = "atexit_global_dtor_vt"
    elif dele:
        info["kind"] = "delete_dtor_vt"
    else:
        info["kind"] = "ctor_or_plain_fn"
    return info


def row(b, atl, entry):
    print("#" * 110)
    print(f"# ENTRY {entry:08X}")
    print("#" * 110)
    a = atl.at(entry)
    print(f"[0] atlas: {a}")
    size = a["size"] if (a and a["offset"] == 0) else 0x200
    print(f"\n[1] BODY ({size} bytes, independent linear disasm skipdata=True):")
    for ins in b.func(entry, size):
        print("    ", fmt_ins(ins))
    print(f"\n[2] direct callers (E8): {[f'{x:08X}' for x in b.callers_direct(entry)]}")
    occ = b.find_imm32(entry)
    print(f"[3] entry as dword occurrences ({len(occ)}):")
    for va in occ:
        print(f"    @{va:08X} [{b.secname(va)}]  before={b.u32(va-4):#010x}  after={b.u32(va+4):#010x}")
    vts, cols, spans = b.build_vtables()
    holds = b.tables_holding(entry, vts, spans)
    print(f"\n[4] vtable registry: {len(vts)} tables / {len(cols)} COLs / holding entry: {len(holds)}")
    for vt, slot, col, name, n in holds:
        print(f"    vt={vt:08X} slot{slot} slotaddr={vt+4*slot:08X} COL={col:08X} name={name!r} nslots={n}")
    return {"size": size, "vts": vts, "spans": spans, "cols": cols, "holds": holds, "atlas": a}


def table_report(b, atl, vt, entry, coldump=64):
    print("=" * 110)
    print(f"TABLE {vt:08X}")
    print("=" * 110)
    vts, cols, spans = b.build_vtables()
    col = b.u32(vt - 4)
    print(f"[RTTI] [vt-4] = {col:08X}   (COL ptr stored at {vt-4:08X})")
    print(f"       COL sig={b.u32(col):#x} offset={b.u32(col+4):#x} cd={b.u32(col+8):#x}")
    ptd = b.u32(col + 0xC)
    pchd = b.u32(col + 0x10)
    print(f"       COL+0xC  pTD ={ptd:#010x}  (abs VA? {ptd >= IMAGEBASE})")
    print(f"       COL+0x10 pCHD={pchd:#010x}  (abs VA? {pchd >= IMAGEBASE})")
    print(f"       TD+8 u32={b.u32(ptd+8):#x}  TD+8 str={b.cstr(ptd+8)!r}")
    slots = b.table_slots(vt, spans.get(vt))
    print(f"\n[SLOTS] {len(slots)} slots, span end={hex(spans.get(vt)) if spans.get(vt) else None}")
    for i, v in enumerate(slots):
        mark = "   <<== ENTRY" if v == entry else ""
        print(f"    slot{i:2d} (+0x{4*i:03X}) {v:08X}{mark}")
    w = b.vt_writers(vt)
    print(f"\n[WRITE POINTS] whole-image imm32=={vt:08X} : {len(w)} site(s)")
    for rec in w:
        c = classify_writer(b, atl, rec)
        en = c.get("enclosing")
        enstr = f"in_func={en['entry']:08X}(+{en['offset']:#x})" if en else "in_func=?"
        print(f"  - imm@{rec['imm_at']:08X} ins@{rec['ins_va'] if rec['ins_va'] is not None else 0:08X}  {rec['text']}")
        print(f"      bytes[{rec['bytes']}]  {enstr}  kind={c['kind']}")
        if c["atexit_registered"]:
            print(f"      ATEXIT: {c.get('atexit_evidence')}")
        if c["delete_dtor"]:
            print(f"      DELDTOR: {c.get('delete_evidence')}")
    return w


if __name__ == "__main__":
    b = Bin()
    atl = Atlas()
    for a in sys.argv[1:]:
        e = int(a, 16)
        r = row(b, atl, e)
        for vt, slot, col, name, n in r["holds"]:
            table_report(b, atl, vt, e)
