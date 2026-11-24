"""d6_tables.py — emit the two machine-readable deliverables:
   EVIDENCE/WRITES.tsv      every memory-writing instruction in the body
   EVIDENCE/VT_SLOTS.tsv    slot-by-slot values of both holding tables
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import open_pe

HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.join(os.path.dirname(HERE), "EVIDENCE")
ENTRY = 0x0045A640


def main():
    pe = open_pe()
    with open(os.path.join(HERE, "body.json"), encoding="utf-8") as f:
        body = json.load(f)

    L = ["addr\toff\tsize\tbytes\tmnemonic\top_str\tdst_kind\tdst\tnote"]
    for r in body["rows"]:
        if not r["writes"]:
            continue
        for w in r["writes"]:
            note = ("implicit stack traffic of the instruction"
                    if w["cls"] == "implicit" else w["cls"])
            L.append(f"{r['addr']:#010x}\t{r['off']:+d}\t{r['size']}\t{r['bytes']}\t"
                     f"{r['mnemonic']}\t{r['op_str']}\t{w['kind']}\t{w['op']}\t{note}")
    open(os.path.join(EV, "WRITES.tsv"), "w", encoding="utf-8").write("\n".join(L) + "\n")

    rows = ["vt\tslot\tslot_addr\tvalue\tis_target\tkind"]
    for vt in (0x007E44F4, 0x007E4514):
        for i in range(7):
            a = vt + 4 * i
            v = pe.u32(a)
            rows.append(f"{vt:#010x}\t{i}\t{a:#010x}\t{v:#010x}\t"
                        f"{'YES' if v == ENTRY else ''}\t"
                        f"{'slot' if v else 'terminator'}")
        # the word after the last slot
        a = vt + 4 * 7
        v = pe.u32(a)
        rtti_next = pe.rtti_of_vtable(a) if pe.sec_of(v) else None
        kind = "COL-of-next-table" if rtti_next and rtti_next.get("name") else "not-a-slot"
        rows.append(f"{vt:#010x}\t(7)\t{a:#010x}\t{v:#010x}\t\t{kind}")
    open(os.path.join(EV, "VT_SLOTS.tsv"), "w", encoding="utf-8").write("\n".join(rows) + "\n")
    print("\n".join(rows))
    print()
    print("\n".join(L[:8]))


if __name__ == "__main__":
    main()
