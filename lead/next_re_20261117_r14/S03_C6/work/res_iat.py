"""Resolve IAT slots used by the 8 card functions to imported API names (read-only)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import common as C
pe = C.get_pe()
pe.parse_data_directories()
iat = {}
for entry in pe.DIRECTORY_ENTRY_IMPORT:
    dll = entry.dll.decode('latin-1', 'replace')
    for imp in entry.imports:
        if imp.address is not None:
            iat[imp.address] = "%s!%s" % (dll, imp.name.decode('latin-1','replace') if imp.name else ("ord%d"%imp.ordinal))
slots = [0x7e11a0,0x7e1200,0x7e1120,0x7e1128,0x7e1130,0x7e112c,0x7e10e0,0x7e11e0,0x7e11c0,0x7e11bc,0x7e111c,0x7e1134,0x7e1124]
for s in slots:
    print("0x%x -> %s" % (s, iat.get(s, "NOT-IMPORT")))
