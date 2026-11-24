#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T1 A/B/C: direct E8 call sites, jmp tail branches, and LE-dword pointer
occurrences of 0x47C620 (byte scan, instruction-boundary checked).
T1-D (disassembly equivalent forms) is in t1_d_equiv.py (skipdata-safe).
"""
import struct, sys
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_GATE_B\work')
import peutil
from peutil import *
SECTIONS = peutil._SECTIONS

TARGET = 0x47C620
TEXT_VA = 0x401000
TEXT_END = 0x7E1000

print("=" * 78)
print("T1-A: direct E8 rel32 call to 0x%08X (byte scan whole .text)" % TARGET)
print("=" * 78)
text_bytes = read(TEXT_VA, TEXT_END - TEXT_VA)
e8_sites = []
for i in range(len(text_bytes) - 5):
    if text_bytes[i] == 0xE8:
        rel = struct.unpack_from('<i', text_bytes, i+1)[0]
        addr = TEXT_VA + i
        if addr + 5 + rel == TARGET:
            e8_sites.append(addr)
print("direct E8 count = %d" % len(e8_sites))
for a in e8_sites:
    print("  call @ 0x%08X" % a)

print()
print("=" * 78)
print("T1-B: jmp rel32(E9)/rel8(EB) tail branch to 0x%08X" % TARGET)
print("=" * 78)
jmp_sites = []
for i in range(len(text_bytes) - 5):
    a = TEXT_VA + i
    b = text_bytes[i]
    if b == 0xE9:
        rel = struct.unpack_from('<i', text_bytes, i+1)[0]
        if a + 5 + rel == TARGET:
            jmp_sites.append((a, 'E9 rel32'))
    elif b == 0xEB and i+1 < len(text_bytes):
        rel = struct.unpack_from('<b', text_bytes, i+1)[0]
        if a + 2 + rel == TARGET:
            jmp_sites.append((a, 'EB rel8'))
print("jmp-to-target count = %d" % len(jmp_sites))
for a, k in jmp_sites:
    print("  %s @ 0x%08X" % (k, a))

print()
print("=" * 78)
print("T1-C: all 4-byte LE occurrences of pointer/immediate 0x%08X in whole image" % TARGET)
print("=" * 78)
pat = struct.pack('<I', TARGET)
occ = []
for secname, sva, vsz, praw, rsz in SECTIONS:
    sec = read(sva, max(vsz, rsz))
    idx = 0
    while True:
        j = sec.find(pat, idx)
        if j < 0: break
        occ.append((secname, sva + j))
        idx = j + 1
print("total LE dword occurrences = %d" % len(occ))
for secname, va in occ:
    print("  [%s] 0x%08X  ctx: %s" % (secname, va, read(va-8,24).hex(' ')))
print()
print("NOTE: T1-D equivalent forms (FF/2 indirect, lea/mov+call, imm operands)")
print("      are in work/t1_d_equiv.py -> EVIDENCE/t1_d_equiv.txt (skipdata-safe).")
