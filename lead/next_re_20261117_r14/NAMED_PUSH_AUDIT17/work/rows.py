"""Row probe: ② all holding tables + RTTI; body disassembly; outbound calls."""
import sys
from pe import (BY, TEXT_LO, TEXT_HI, u32, u8, read, cstr, fmt, dis, win,
                find_imm32, rtti, slots, tables_holding, func_extent, in_text, MDD)

ROWS = [
    # S18 B5
    ("007B13D0", "S18", "IPXInterfaceClass::slot16"),
    ("007B1BC0", "S18", "IPXInterfaceClass::slot7"),
    ("007B2630", "S18", "IPXInterfaceClass::slot10"),
    ("007B26D0", "S18", "IPXInterfaceClass::slot17"),
    ("007B30B0", "S18", "UDPInterfaceClass::slot23"),
    ("007B31E0", "S18", "UDPInterfaceClass::slot26"),
    ("007B3450", "S18", "UDPInterfaceClass::slot15"),
    ("007B3890", "S18", "UDPInterfaceClass::slot7"),
    ("007B3AA0", "S18", "UDPInterfaceClass::slot16"),
    # S17 B1
    ("004A2CD0", "S17", "CStreamClass::slot4"),
    ("006BEF10", "S17", "T_TClassFactory_VCStreamClass__::slot3"),
    ("006BF690", "S17", "T_TClassFactory_VSuperClass__::slot3"),
]


def probe(entry_s):
    entry = int(entry_s, 16)
    print("=" * 100)
    print("ROW %s   entry in .text: %s" % (entry_s, in_text(entry)))
    th = tables_holding(entry)
    print("  [2] tables holding this entry: %d" % len(th))
    for t in th:
        r = t["rtti"]
        print("      base=%08X slot=%2d slot_at=%08X  COL=%08X TD=%08X name=%r" % (
            t["base"], t["slot"], t["slot_at"], r.get("col") or 0, r.get("td") or 0,
            r.get("name")))
        # show whole table
        sl = slots(t["base"])
        print("        slotcount=%d ; slot_values=%s" % (
            len(sl), " ".join("%d:%08X" % (k, v) for k, v in enumerate(sl[:40]))))
    print("  [1] body:")
    body = func_extent(entry)
    for i in body:
        print("      " + fmt(i))
    print()


if __name__ == "__main__":
    want = sys.argv[1:] or [r[0] for r in ROWS]
    for r in ROWS:
        if r[0] in want or not sys.argv[1:]:
            probe(r[0])
