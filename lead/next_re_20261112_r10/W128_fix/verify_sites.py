#!/usr/bin/env python3
"""W128i: verify the 3 defect sites against the on-disk image, pre and post patch.

pre  : the 12 bytes at each site must be the known sequence
post : (needs a live process) entry must be `E8 rel32 -> helper` + NOP padding
"""
import json
import os
import struct
import sys

import pefile

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

# the full 12-byte original sequences (computed from the image; asserted below)
EXPECT = {
    "0x006F409C": "8b91ac0000008a8255010000",
    "0x006F4124": "8b91ac0000008a8259010000",
    "0x006F4173": "8b88ac0000008a815a010000",
}

pe = pefile.PE(EXE, fast_load=True)
ib = pe.OPTIONAL_HEADER.ImageBase
img = open(EXE, "rb").read()


def file_off(va):
    return pe.get_offset_from_rva(va - ib)


ok = True
print("%-12s %-26s %-26s %s" % ("site", "expected", "on disk", "verdict"))
print("-" * 92)
for site, exp in EXPECT.items():
    va = int(site, 16)
    got = img[file_off(va): file_off(va) + 12].hex()
    good = got == exp
    ok &= good
    print("%-12s %-26s %-26s %s" % (site, exp, got, "OK" if good else "MISMATCH"))
print("\nSITE PRE-FLIGHT:", "PASS" if ok else "FAIL")

# show what the patch will look like (helper offsets unknown until runtime)
print("\nPatch shape at each site: E8 <rel32->helper> then 7 x 0x90")
print("  (site length 12, resumes exactly at `test al,al`)")
for site in EXPECT:
    va = int(site, 16)
    after = img[file_off(va) + 12: file_off(va) + 15].hex()
    print("  %s  bytes after site: %s   (%s)"
          % (site, after, "test al,al" if after.startswith("84c0") else "??"))
sys.exit(0 if ok else 1)
