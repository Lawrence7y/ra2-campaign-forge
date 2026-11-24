import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q, core as C

pairs = [(0x8872B0, 0x7E1B24, 0x7E1B44), (0x8B41C8, 0x7EA124, 0x7EA144),
         (0x8B4120, 0x7EA024, 0x7EA044), (0xA8E8D0, 0x7EA0A4, 0x7EA0C4),
         (0xA8E968, 0x7EA524, 0x7EA544), (0xA8B218, 0x7EA264, 0x7EA284)]
for g, a, b in pairs:
    print("== global %08X" % g)
    for vt in (a, b):
        ri = C.rtti_of_vt(vt)
        nm = ri["name"] if ri else None
        print("   vt %08X name=%s" % (vt, nm))
        print("      slots: " + " ".join("+%#04x=%08X" % (i * 4, v) for i, v in enumerate(C.slots_of_vt(vt, 8))))
    print()
