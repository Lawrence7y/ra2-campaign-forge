import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditlib import *

imp_by_addr = {}
for entry in pe.DIRECTORY_ENTRY_IMPORT:
    dll = entry.dll.decode()
    for imp in entry.imports:
        nm = imp.name.decode() if imp.name else f"ord_{imp.ordinal}"
        imp_by_addr[imp.address] = (dll, nm)

print("total imports parsed:", len(imp_by_addr))
print()
print("=== IAT slots referenced by the 0x7C89xx thunks ===")
for slot in (0x7E1548, 0x7E1574, 0x7E1584, 0x7E1580, 0x7E157C, 0x7E1554):
    if slot in imp_by_addr:
        print(f"  [{slot:08X}] -> {imp_by_addr[slot][0]}!{imp_by_addr[slot][1]}")
    else:
        print(f"  [{slot:08X}] -> NOT in parsed import table; raw u32={u32(slot):08X}")

print()
print("=== all imports with IAT in 0x7E1400..0x7E1700 ===")
for a in sorted(imp_by_addr):
    if 0x7E1400 <= a <= 0x7E1700:
        print(f"  [{a:08X}] {imp_by_addr[a][0]}!{imp_by_addr[a][1]}")
