import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa


def dump(va, n=200, label=""):
    print(f"--- {label} @{va:08X} ---")
    for i in dis(va, n):
        print("   " + fmt(i))
    print()


dump(0x41C8B0, 60, "obj ctor wrapper for AircraftType row")
dump(0x710AF0, 200, "its outcall")
dump(0x41C900, 120, "claimed vt writer")
print("vt 007E2868 slots:", [f"{u32(0x7E2868+4*k):08X}" for k in range(8)])
print("vt-4 =", f"{u32(0x7E2864):08X}", "bytes", hexs(0x7E2860, 16))
print("rtti:", rtti_name(0x7E2868))
