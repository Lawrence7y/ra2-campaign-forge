import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q, core as C, fnd

print("### Find for InfantryTypeClass (0x4EE410)")
print(C.show_range(0x4EE410, 0x4EE440, "Find"))

def peek(lo, n=14, label=""):
    print("\n--- %s fn~%08X" % (label, lo))
    for i in C.disasm(lo, n, nbytes=n * 8):
        extra = ""
        if i.mnemonic == "call":
            t = q.callee_at(i.address)
            if t:
                extra = "  ; -> %08X" % t
        print("   " + C.fmt(i) + extra)

# AircraftClass 候选构造点所在函数
peek(0x413D58, 16, "AircraftClass site 0x413D87 host")
peek(0x414071, 16, "AircraftClass site 0x41408A host")
# AircraftTypeClass
peek(0x41C8A7, 16, "AircraftTypeClass site 0x41C900 host")
# InfantryTypeClass
peek(0x5237B0, 14, "InfantryTypeClass site 0x5237E8 host")
# ObjectTypeClass
peek(0x5F7088, 12, "ObjectTypeClass site 0x5F7251 host")
# AbstractTypeClass
peek(0x410954, 14, "AbstractTypeClass site 0x410975 host")
# SideClass
peek(0x6A455E, 12, "SideClass site 0x6A4597 host")
