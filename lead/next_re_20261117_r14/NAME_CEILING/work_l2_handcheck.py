# -*- coding: utf-8 -*-
"""NAME-CEILING 内部核查：手工复核 3 条 L2 样本的原始字节链。

对每条样本打印：
  vt-4 处的 COL 指针        （虚表[-1]）
  vt 起始 6 个槽的原始 dword
  COL+0x04 (col_offset)、COL+0x0C (pTD)
  TD+0x08 处的 RTTI 名字串
"""
import struct

import pefile

PROJ = r"D:\Project\ra2-campaign-forge"
EXE = PROJ + r"\ra2youli\gamemd.exe"
pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
IMG = pe.get_memory_mapped_image()


def u32(va):
    return struct.unpack("<I", IMG[va - IB: va - IB + 4])[0]


def cstr(va, n=200):
    return IMG[va - IB: va - IB + n].split(b"\x00")[0].decode("ascii", "replace")


CASES = [
    ("0040CC20", 0x007E18FC, 0),
    ("0040D280", 0x007E1964, 40),
    ("004115A0", 0x007E2104, 0),
]

for entry, vt, slot in CASES:
    target = int(entry, 16)
    col = u32(vt - 4)
    off = u32(col + 0x04)
    td = u32(col + 0x0C)
    print("entry=%s  vt=0x%08X  slot=%d" % (entry, vt, slot))
    print("   vt[-1] COL   = 0x%08X" % col)
    print("   COL+0x04 off = 0x%X   COL+0x0C pTD = 0x%08X" % (off, td))
    print("   TD+0x08 name = %s" % cstr(td + 0x08))
    head = [u32(vt + 4 * k) for k in range(6)]
    print("   slots[0..5]  = %s" % " ".join("0x%08X" % x for x in head))
    val = u32(vt + 4 * slot)
    print("   slots[%d]     = 0x%08X   %s"
          % (slot, val, "== entry OK" if val == target else "!! MISMATCH"))
    print("")
