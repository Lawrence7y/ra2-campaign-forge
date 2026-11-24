import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21-F1\work")
import ra2 as R

print("=== strings around 0x81B180-0x81B1F0 (campaign section keys) ===")
for va in range(0x81B180, 0x81B1F0, 4):
    # try ascii string starting exactly here
    try:
        s = R.cstr(va, 60)
    except Exception:
        s = None
    if s and len(s) >= 1 and all(32 <= ord(c) < 127 for c in s):
        print(f"  {va:08X}: {s!r}")
    elif s == "":
        pass
    else:
        # show raw dword
        try:
            v = R.u32(va)
            print(f"  {va:08X}: dword {v:08X}")
        except Exception:
            pass

print("\n=== explicitly referenced key string addresses in slot25 ===")
for va in [0x81B1D4, 0x81B1C8, 0x81B1BC, 0x81B1B0, 0x81B1A4, 0x81B18C, 0x81B1D8]:
    try:
        print(f"  {va:08X}: {R.cstr(va, 80)!r}")
    except Exception as e:
        print(f"  {va:08X}: ERR")

print("\n=== read helper functions ===")
for va, name in [(0x5276D0, "GetInteger?"), (0x4757D0, "?"), (0x528A10, "GetString?"),
                 (0x5295F0, "GetBool?"), (0x529160, "GetString2?"), (0x526B00, "?"),
                 (0x410A60, "base Load?"), (0x7DCFC4, "?"), (0x735060, "?")]:
    print(f"\n--- {name} @ {va:08X} ---")
    R.dump(va, 0x50)
