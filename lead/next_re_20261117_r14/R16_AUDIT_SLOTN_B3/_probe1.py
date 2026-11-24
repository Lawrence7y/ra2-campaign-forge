# -*- coding: utf-8 -*-
import struct, sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_AUDIT_SLOTN_B3")
from verify import Image, EXE, MD, decode_at

img = Image(EXE)

def dump(va, n=64, label=""):
    b = img.read(va, n)
    print(label, "VA=%08X" % va, b.hex(' ') if b else None)

for va, lab in ((0x517D90, "claim func row32"), (0x517D9D, "site row32"),
                (0x521960, "claim func row33"), (0x521A11, "site row33"),
                (0x6AF120, "claim func row39/40"), (0x6AF13D, "site 39/40"),
                (0x6B6C10, "claim func 41/42"), (0x6B6C2D, "site 41/42"),
                (0x6F2B40, "claim func 43"), (0x6F3130, "site 43")):
    b = img.read(va - 8, 40)
    print("%-18s VA=%08X  prev8=%s | head=%s" % (lab, va, b[:8].hex(' '), b[8:24].hex(' ')))

print()
for va, lab in ((0x517D90, "row32"), (0x521960, "row33"), (0x6AF120, "39/40"),
                (0x6B6C10, "41/42"), (0x6F2B40, "43"),
                (0x5B2DA0, "31"), (0x5B3C20, "36"), (0x652960, "37"), (0x65CA00, "38")):
    insn = decode_at(img, va)
    print(lab, "func %08X -> %s %s" % (va, insn.mnemonic if insn else None, insn.op_str if insn else None))
