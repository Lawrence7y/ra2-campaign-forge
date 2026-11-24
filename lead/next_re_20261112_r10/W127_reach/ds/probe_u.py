# -*- coding: utf-8 -*-
"""C2: are the six cluster entries ever taken by RELOCATED (runtime) pointers?
Check .reloc coverage for .rdata/.data."
"""
import pefile
from base import pe, SECTIONS, IB
print("=== .reloc present? ===")
print("  HAS_RELOC:", hasattr(pe,"DIRECTORY_ENTRY_BASERELOC"))
try:
    n=0; covered=[]
    for blk in pe.DIRECTORY_ENTRY_BASERELOC:
        n+=len(blk.entries)
        covered.append((blk.struct.VirtualAddress, len(blk.entries)))
    print("  relocation blocks:", len(covered), " total entries:", n)
    print("  first blocks:", covered[:10])
    print("  IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE set?",
          bool(pe.OPTIONAL_HEADER.DllCharacteristics & 0x40))
except Exception as e:
    print("  no reloc dir:", e)
