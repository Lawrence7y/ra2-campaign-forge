# -*- coding: utf-8 -*-
"""W151: framing-independent byte-pattern scan of .text.

Find every `call dword ptr [reg+0x5c]` (vtable slot 23 = AI) and
`call dword ptr [reg+0x114]` (slot 69 = Draw), including in code regions that
Ghidra never made into functions.

Encodings covered:
  FF /2 mod=01 rm      -> FF 5x 5C                (disp8, no SIB)
  FF /2 mod=01 rm=100  -> FF 54 24 5C etc (SIB)   -> FF 54 <sib> 5C
  FF /2 mod=10 rm      -> FF 9x 5C 00 00 00       (disp32)
  FF /2 mod=10 rm=100  -> FF 94 <sib> 5C 00 00 00
"""
import os, sys, struct, collections

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, r"ra2youli\gamemd.exe")
IB = 0x400000
TEXT_VA, TEXT_OFF, TEXT_LEN = IB + 0x1000, 0x1000, 0x3DF38D
img = open(EXE, "rb").read()
text = img[TEXT_OFF:TEXT_OFF + TEXT_LEN]

DISP = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x5C
d8 = bytes([DISP & 0xFF])
d32 = struct.pack("<I", DISP)
rm_regs = [0, 1, 2, 3, 6, 7]          # eax ecx edx ebx esi edi
names = {0: "eax", 1: "ecx", 2: "edx", 3: "ebx", 6: "esi", 7: "edi"}

hits = []
# --- disp8, no SIB ---
for rm in rm_regs:
    pat = bytes([0xFF, 0x50 | rm]) + d8
    i = 0
    while True:
        i = text.find(pat, i)
        if i < 0:
            break
        hits.append((TEXT_VA + i, "FF %02X %02X" % (0x50 | rm, DISP), "call [%s+%s]" % (names[rm], hex(DISP))))
        i += 1
# --- disp8, with SIB (FF 54 sib 5C) ---
i = 0
pat = bytes([0xFF, 0x54])
while True:
    i = text.find(pat, i)
    if i < 0:
        break
    if i + 3 < len(text) and text[i + 3] == DISP:
        sib = text[i + 2]
        base = sib & 0x7
        idx = (sib >> 3) & 0x7
        hits.append((TEXT_VA + i, text[i:i + 4].hex().upper(),
                     "call [sib base=%d index=%d scale=%d +%s]" % (base, idx, sib >> 6, hex(DISP))))
    i += 1
# --- disp32, no SIB ---
for rm in rm_regs:
    pat = bytes([0xFF, 0x90 | rm]) + d32
    i = 0
    while True:
        i = text.find(pat, i)
        if i < 0:
            break
        hits.append((TEXT_VA + i, pat.hex().upper(), "call [%s+%s] (disp32)" % (names[rm], hex(DISP))))
        i += 1
# --- disp32 with SIB ---
i = 0
pat = bytes([0xFF, 0x94])
while True:
    i = text.find(pat, i)
    if i < 0:
        break
    if text[i + 2:i + 6] == d32:
        hits.append((TEXT_VA + i, text[i:i + 6].hex().upper(), "call [sib +%s] (disp32)" % hex(DISP)))
    i += 1

hits.sort()
print("### pattern disp=%s  total=%d" % (hex(DISP), len(hits)))
for va, enc, txt in hits:
    print("%08x  %-18s %s" % (va, enc, txt))
