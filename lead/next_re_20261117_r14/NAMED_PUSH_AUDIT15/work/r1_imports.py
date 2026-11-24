import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditlib import *

# ---- 1) resolve import thunks in the 0x7C8xxx range ----
mine = {}
for entry in pe.DIRECTORY_ENTRY_IMPORT:
    dll = entry.dll.decode()
    for imp in entry.imports:
        if imp.address and imp.name:
            mine[imp.address] = (dll, imp.name.decode())

print("=== import thunks used by 007B10C0 ===")
for va in (0x7C8968, 0x7C897A, 0x7C8992, 0x7C8998, 0x7C899E, 0x7C89A4, 0x7C8B3D, 0x4068E0):
    if va in mine:
        print(f"  {va:08X} = {mine[va][0]}!{mine[va][1]}   bytes@thunk={hexb(va,6)}")
    else:
        b = hexb(va, 8)
        print(f"  {va:08X} = (not an IAT thunk slot) bytes={b}")
        # try disasm
        for i in disasm(va, 16, ):
            print("      ", fmt_insn(i))
            if i.mnemonic in ('jmp','ret'): break
