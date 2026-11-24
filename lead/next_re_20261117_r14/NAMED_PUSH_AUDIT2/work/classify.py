import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q, core as C, fnd

regfns = set(t for t, s in q.atexit_targets())
CAND = {
    "00691EE0": [(0x6913DD, "ScriptClass")],
    "00691FA0": [(0x6916D1, "ScriptTypeClass")],
    "006A48A0": [(0x6A4597, "SideClass"), (0x6A47E1, "SideClass")],
    "006A4930": [(0x6A4597, "SideClass"), (0x6A47E1, "SideClass")],
    "006E87F0": [(0x6E7EAD, "TaskForceClass")],
    "006E9140": [(0x6E8B32, "TeamClass"), (0x6EC485, "TeamClass")],
    "00410C30": [(0x410975, "AbstractTypeClass"), (0x4109CD, "AbstractTypeClass"), (0x410822, "AbstractTypeClass")],
    "00414290": [(0x413D87, "AircraftClass"), (0x41408A, "AircraftClass"), (0x41B4E1, "AircraftClass")],
    "0041CFE0": [(0x41C900, "AircraftTypeClass"), (0x41CE44, "AircraftTypeClass")],
    "00524D70": [(0x5237E8, "InfantryTypeClass"), (0x5239A8, "InfantryTypeClass")],
    "005F9950": [(0x5F7251, "ObjectTypeClass"), (0x5F73D9, "ObjectTypeClass")],
}

for e, cands in CAND.items():
    print("\n########## entry %s" % e)
    for site, cls in cands:
        lo, end = fnd.fn_range(site)
        size = (end - lo) if end else 0
        inside = [a for a, x in q.CALLS if lo <= a < (end or lo + 0x400)]
        freec = [a for a in inside if q.callee_at(a) == 0x7C8B3D]
        basedt = [a for a in inside if q.callee_at(a) in (0x4101F0, 0x4109C0, 0x7258D0)]
        insts = [(a, imm) for a, imm, m in q.VINST if lo <= a < (end or lo + 0x400)]
        print("  site %08X cls=%s  fn %08X..%08X size %d" % (site, cls, lo, end or 0, size))
        print("     atexit_self=%s  free=%s  basector/dtor_calls=%s" % (
            lo in regfns, ["%08X" % a for a in freec], ["%08X->%08X" % (a, q.callee_at(a)) for a in basedt]))
        print("     installs_in_fn=%d: %s" % (len(insts), " ".join("%08X:%08X" % (a, i) for a, i in insts)))
        ins = C.disasm(lo, 6, nbytes=min(64, (end or lo + 64) - lo))
        tail = C.disasm((end or lo + 64) - 24, 4, nbytes=24)
        print("     head: " + " | ".join("%s %s" % (i.mnemonic, i.op_str) for i in ins))
        print("     tail: " + " | ".join("%s %s" % (i.mnemonic, i.op_str) for i in tail))
