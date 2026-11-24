import struct
from core import *

# 1) all imm32 occurrences of 007F6218 family in .text
def find_bytes(pat, sec=".text"):
    out = []
    for nm, sva, rva, vs, rs, rp in SECS:
        if nm != sec:
            continue
        blob = DATA[rp:rp + rs]
        i = blob.find(pat)
        while i != -1:
            out.append((sva + i, i))
            i = blob.find(pat, i + 1)
    return [va for va, _ in out]

for tgt in (0x007F6218, 0x007F61FC, 0x007F61F4, 0x007F61EC):
    pat = struct.pack("<I", tgt)
    hits = find_bytes(pat)
    print("imm32 %08X in .text: %d hits" % (tgt, len(hits)))
    for va in hits:
        print("   site %08X" % va)
    print()
