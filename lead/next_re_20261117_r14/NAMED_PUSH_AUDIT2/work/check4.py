import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q, core as C, fnd

VTS = {0x7E22A4: "AircraftClass", 0x7E2868: "AircraftTypeClass", 0x7EB610: "InfantryTypeClass",
       0x7EF2D8: "ObjectTypeClass", 0x7E2000: "AbstractTypeClass", 0x7F2EC0: "SideClass",
       0x7F0F78: "ScriptClass", 0x7F1008: "ScriptTypeClass", 0x7F4680: "TaskForceClass",
       0x7F4730: "TeamClass"}

for vt, cls in VTS.items():
    print("\n== %s vt=%08X : all .text refs" % (cls, vt))
    for r in C.refs_to(vt, (".text",)):
        ins = C.disasm(r - 16, 6, nbytes=32)
        hit = None
        for i in ins:
            if i.address <= r < i.address + i.size:
                hit = i
                break
        lo, end = fnd.fn_range(r)
        print("   ref@%08X  %-46s fn~%08X" % (r, C.fmt(hit) if hit else "<noinsn>", lo))
