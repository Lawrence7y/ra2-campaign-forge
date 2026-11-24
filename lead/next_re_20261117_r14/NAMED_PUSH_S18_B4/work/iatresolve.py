# -*- coding: utf-8 -*-
import os, sys, pefile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
pe = R._pe
# map IAT VA -> (dll, func)
iatmap = {}
for desc in pe.DIRECTORY_ENTRY_IMPORT:
    dll = desc.dll.decode("latin1")
    for imp in desc.imports:
        if imp.address:
            iatmap[imp.address] = (dll, imp.name.decode("latin1") if imp.name else ("ord%d"%imp.ordinal))
for va in range(0x7e1540, 0x7e1590, 4):
    print("IAT %08X -> %s" % (va, iatmap.get(va, "???")))
print()
# also thunk VA -> target IAT
for tva in range(0x7C8968, 0x7C89BC, 6):
    code = R.read_va(tva, 6)
    if len(code)>=6 and code[0:2]==b'\xff\x25':
        import struct
        iat = struct.unpack("<I", code[2:6])[0]
        print("thunk %08X -> IAT %08X -> %s" % (tva, iat, iatmap.get(iat,"???")))
