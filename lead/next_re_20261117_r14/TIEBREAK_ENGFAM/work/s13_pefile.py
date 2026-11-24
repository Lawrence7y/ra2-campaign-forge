"""s13: independent cross-check of the import directory with pefile.

The ole32 descriptor in this image has its ILT in .detour and IAT values that
look like .text addresses, which is unusual; pefile parses the same directory
with its own logic, so comparing the two tells us whether our slot->name
mapping is right.
"""
import pefile

import pe

EXE = pe.EXE
SLOT = 0x007E15F4


def main():
    p = pe.open_pe()
    print("self sha256", p.sha256)
    print(f"own dd[1] rva/size: 0x{p.dd[1][0]:X}/0x{p.dd[1][1]:X}")
    pef = pefile.PE(EXE, fast_load=False)
    print("pefile base", hex(pef.OPTIONAL_HEADER.ImageBase))
    for i, d in enumerate(pef.OPTIONAL_HEADER.DATA_DIRECTORY):
        if d.VirtualAddress:
            print(f"  dir[{i}] {d.name:<28} rva 0x{d.VirtualAddress:X} size 0x{d.Size:X}")
    print()
    for entry in pef.DIRECTORY_ENTRY_IMPORT:
        dll = entry.dll.decode()
        if "ole32" not in dll.lower():
            continue
        print(f"module {dll}  iat base 0x{entry.struct.FirstThunk + pef.OPTIONAL_HEADER.ImageBase:X}")
        for imp in entry.imports[:20]:
            va = imp.address
            print(f"   slot 0x{va:08X}  {imp.name.decode() if imp.name else 'ord'}")
    print()
    # which imported function does the slot resolve to?
    found = None
    for entry in pef.DIRECTORY_ENTRY_IMPORT:
        for imp in entry.imports:
            if imp.address == SLOT:
                found = (entry.dll.decode(), imp.name.decode() if imp.name else None)
    print("slot 0x%08X ->" % SLOT, found)
    print("raw dword at slot 0x%08X = 0x%08X" % (SLOT, pef.get_dword_at_rva(SLOT - pef.OPTIONAL_HEADER.ImageBase)))


if __name__ == "__main__":
    main()
