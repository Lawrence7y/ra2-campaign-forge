"""Deep evidence pack for all 7 rows of NAMED_PUSH_AUDIT19 (single sweep)."""
import sys, bisect
from re_lib import Bin, IMAGEBASE, TEXT_LO, TEXT_HI, fmt_ins
from row import Atlas

ENTRIES = [0x005FEAF0, 0x006B5850, 0x0071CDA0, 0x00432050, 0x0046D000, 0x0046D090, 0x0071B1B0]


def classify(b, fn):
    """Classify a function that writes some vtable."""
    ate, p, ev = b.is_atexit_dtor(fn)
    dele, dev = b.is_delete_dtor(fn, scan=0x160)
    if ate:
        shape = "atexit_global_dtor"
    elif dele:
        shape = "delete_dtor"
    else:
        # deleting dtor that only tests flag differently? look for operator delete + ret 4
        ins = b.func(fn, 0x160)
        has_del = any(i.mnemonic == "call" and i.op_str.replace("0x", "").lower() in ("7c8b3d", "7c8b3c") for i in ins)
        rets = [i.op_str.strip() for i in ins if i.mnemonic == "ret"]
        shape = f"plain(has_free={has_del},rets={rets})"
    return {"fn": fn, "atexit": ate, "atexit_ev": ev, "del": dele, "del_ev": dev, "shape": shape}


def report(b, atl, entry):
    out = []
    W = out.append
    W("#" * 118)
    W(f"# ENTRY {entry:08X}")
    W("#" * 118)
    a = atl.at(entry)
    own = b.func_start_of(entry)
    W(f"[atlas] {a}")
    W(f"[independent func_start_of(entry)] {own:#x} {'MATCH' if own == entry else 'MISMATCH'}")
    size = a["size"] if (a and a.get("offset") == 0) else 0x200
    W(f"[body {size} bytes]")
    for ins in b.func(entry, size):
        W("    " + fmt_ins(ins))
    W(f"[direct callers of entry] {[f'{x:08X}' for x in b.callers_direct(entry)]}")
    W(f"[push/imm occurrences of entry] {[f'{x:08X}({b.secname(x)})' for x in b.find_imm32(entry)]}")
    W(f"[entry is atexit-registered?] {b.is_atexit_dtor(entry)}")
    W(f"[entry is delete-dtor?] {b.is_delete_dtor(entry)}")

    vts, cols, spans = b.build_vtables()
    holds = b.tables_holding(entry, vts, spans)
    W(f"\n[tables holding entry] {len(holds)}")
    for vt, slot, col, name, n in holds:
        W(f"   vt={vt:08X} slot{slot} (+0x{4*slot:03X}) slotaddr={vt+4*slot:08X} COL={col:08X} name={name!r} nslots={n}")
        ptd = b.u32(col + 0xC)
        pchd = b.u32(col + 0x10)
        W(f"      COL[{col:08X}]: sig={b.u32(col):#x} off={b.u32(col+4):#x} cd={b.u32(col+8):#x}")
        W(f"      pTD={ptd:#010x} (abs VA {ptd >= IMAGEBASE})  pCHD={pchd:#010x} (abs VA {pchd >= IMAGEBASE})")
        W(f"      TD+8 u32={b.u32(ptd+8):#x}  TD+8 str={b.cstr(ptd+8)!r}")
        slots = b.table_slots(vt, spans.get(vt))
        W(f"      vt[0]={slots[0]:08X} (main-table marker 00410260? {slots[0]==0x410260})   slot count={len(slots)}")
        W(f"      write points (whole-image imm32 == vt):")
        w = b.vt_writers(vt)
        for rec in w:
            if rec["ins_va"] is None:
                W(f"        - imm@{rec['imm_at']:08X} <undecodable> bytes[{rec['bytes']}]")
                continue
            st = b.func_start_of(rec["ins_va"])
            c = classify(b, st) if st else {"shape": "?"}
            callers = b.callers_direct(st) if st else []
            rel = ""
            if st == entry:
                rel = "  <<<< THIS ROW'S OWN BODY (cannot self-certify)"
            elif st == holds[0][0]:
                rel = ""
            W(f"        - ins@{rec['ins_va']:08X} {rec['text']} bytes[{rec['bytes']}]")
            W(f"            in_func={st:08X}(+{rec['ins_va']-st:#x}) shape={c['shape']}  callers={[f'{x:08X}' for x in callers]}{rel}")
            if c.get("atexit"):
                W(f"            ATEXIT-EV: {c['atexit_ev']}")
            if c.get("del"):
                W(f"            DELDTOR-EV: {c['del_ev']}")
    W(f"\n[callees of entry]")
    for ins in b.func(entry, size):
        if ins.mnemonic == "call" and ins.op_str.startswith("0x"):
            t = int(ins.op_str, 16)
            ca = atl.at(t)
            W(f"    {ins.address:08X}: call {t:08X}  atlas_size={ca['size'] if ca and ca.get('offset')==0 else '?'} n_callers={ca['n_callers'] if ca and ca.get('offset')==0 else '?'}")
    return "\n".join(out)


if __name__ == "__main__":
    b = Bin()
    atl = Atlas()
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    ents = [int(arg, 16)] if arg else ENTRIES
    chunks = []
    for e in ents:
        chunks.append(report(b, atl, e))
        chunks.append("")
    txt = "\n".join(chunks)
    open("deep_all.txt", "a", encoding="utf-8").write(txt + "\n")
    print(txt)
