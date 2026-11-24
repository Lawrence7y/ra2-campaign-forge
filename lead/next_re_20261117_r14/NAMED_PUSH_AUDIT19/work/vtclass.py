"""Compact ㉓ write-point categorisation for one vtable."""
import sys
from re_lib import Bin, fmt_ins

def summarize(b, vt, row_entry, show_limit=400):
    w = b.vt_writers(vt)
    cats = {}
    rows = []
    for rec in w:
        ins = b.instr_containing(rec["imm_at"])
        if ins is None:
            cats["undecodable"] = cats.get("undecodable", 0) + 1
            continue
        st = b.func_start_of(ins.address)
        kind = "stack_template" if "[esp" in ins.op_str else "object_write"
        ate, _, aev = b.is_atexit_dtor(st)
        dele, dev = b.is_delete_dtor(st, scan=0x180)
        tag = []
        if st == row_entry:
            tag.append("ROW_SELF")
        if ate:
            tag.append("ATEXIT")
        if dele:
            tag.append("DELETE_DTOR")
        if not tag:
            tag.append("ctor_or_other")
        key = kind + ":" + ",".join(tag)
        cats[key] = cats.get(key, 0) + 1
        rows.append((ins.address, st, kind, ",".join(tag), ins.mnemonic + " " + ins.op_str, ins.bytes.hex(" ")))
    print(f"TABLE {vt:08X}: {len(w)} write points")
    for k, v in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"   {v:5d}  {k}")
    print(f"\n  object-write points (mov [reg], vt) detail:")
    for r in rows:
        if r[2] == "object_write":
            callers = b.callers_direct(r[1])
            print(f"   ins@{r[0]:08X} in_func={r[1]:08X} tag={r[3]:<22} {r[4]:<45} bytes[{r[5]}] n_callers={len(callers)}")
    print(f"\n  Atexit-registered writers (must be 0 to be safe):")
    for r in rows:
        if "ATEXIT" in r[3]:
            print(f"   !! ins@{r[0]:08X} in_func={r[1]:08X} {r[4]}")

if __name__ == "__main__":
    b = Bin()
    vt = int(sys.argv[1], 16)
    row = int(sys.argv[2], 16)
    summarize(b, vt, row)
