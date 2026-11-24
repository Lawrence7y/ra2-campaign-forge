import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

cases = [
    ("006C3410 UnitClass", 0x7353C0, 0x735794),
    ("006C3590 BuildingClass", 0x43B740, 0x43BCFD),
    ("006C3B90 AnimTypeClass", 0x427530, 0x42785D),
]
for label, ctor, site in cases:
    print("=" * 100)
    print(f"{label}: ctor={ctor:08X} second_write={site:08X} delta=+{site-ctor:#x}")
    # walk from ctor, find first ret followed by padding -> function end
    end = None
    for i in dis(ctor, 0x1200):
        if i.mnemonic.startswith("ret"):
            nxt = dis(i.address + i.size, 4)
            if nxt and nxt[0].mnemonic in ("nop", "int3"):
                end = i.address + i.size
                break
    print(f"   first ret+pad at {end:08X}" if end else "   no clean end found")
    # does a ret+pad exist between ctor and site?
    bounds = []
    for i in dis(ctor, site - ctor + 8):
        if i.mnemonic.startswith("ret"):
            nxt = dis(i.address + i.size, 4)
            if nxt and nxt[0].mnemonic in ("nop", "int3"):
                bounds.append((i.address, i.address + i.size))
    print(f"   ret+pad boundaries in [{ctor:08X},{site:08X}]: {[f'{a:08X}..{b:08X}' for a,b in bounds]}")
    print(f"   => second write is {'OUTSIDE (another function)' if bounds and bounds[-1][1] <= site else 'INSIDE same function (alt path)'}")
    print("   context around second write:")
    for i in dis(site - 24, 48):
        print("      " + fmt(i))
    print()
