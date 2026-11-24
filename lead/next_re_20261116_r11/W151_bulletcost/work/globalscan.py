# -*- coding: utf-8 -*-
"""W151: framing-independent 'who references this global' scan.
Searches raw bytes for the little-endian dword of each target address in every
section, and additionally decodes the surrounding bytes so the access width/kind
can be judged. Works inside code that Ghidra never turned into a function.

Usage: python globalscan.py 0xA8ED50 0xA8ED44 0xA8ED40
"""
import os, sys, struct

ROOT = r"D:\Project\ra2-campaign-forge"
img = open(os.path.join(ROOT, r"ra2youli\gamemd.exe"), "rb").read()
IB = 0x400000
SEC = [(".text", 0x001000, 0x3DF38D, 0x001000),
       (".rdata", 0x3E1000, 0x030074, 0x3E1000),
       (".data", 0x412000, 0x367BE4, 0x412000),
       (".rsrc", 0x47E000, 0x018128, 0x47E000),
       (".detour", 0x497000, 0x002718, 0x497000)]


def sec_of(va):
    rva = va - IB
    for name, rva0, vsz, raw in SEC:
        if rva0 <= rva < rva0 + vsz:
            return name
    return "?"


for arg in sys.argv[1:]:
    tgt = int(arg, 16)
    pat = struct.pack("<I", tgt)
    print("=" * 90)
    print("### references to %08x" % tgt)
    n = 0
    for name, rva0, vsz, raw in SEC:
        blob = img[raw:raw + vsz]
        j = 0
        while True:
            j = blob.find(pat, j)
            if j < 0:
                break
            va = IB + rva0 + j
            # show 8 bytes of leading context so the opcode can be recognised
            ctx_off = max(0, j - 8)
            ctx = blob[ctx_off:j + 4]
            print("   %-8s operand_at=%08x  kind=%s  ctx=%s" % (
                name, va,
                "disp32(memory operand)" if va < IB + 0x3E1000 + 0x30074 and name == ".text" else name,
                " ".join("%02x" % c for c in ctx)))
            n += 1
            j += 1
    print("   total=%d" % n)
