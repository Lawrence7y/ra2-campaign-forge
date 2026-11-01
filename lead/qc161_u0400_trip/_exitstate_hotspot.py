#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""0x777800..0x777830 邻域逐字节解码（对齐钉界）—— 钉死 exitstate=2 写点是不是真指令。"""
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

GAME_SRC = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\_src_L1_sf8_20261020")
GAMEMD = GAME_SRC / "gamemd.exe"
BASE_IMAGE = 0x400000


def off_of(va):
    return va - 0x401000  # 本仓已证 FileOffset=VA−0x401000（.text）


def main():
    data = GAMEMD.read_bytes()
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    start = 0x7777F8
    raw = data[off_of(start):off_of(start) + 0x48]
    print("bytes %08X..:" % start)
    print("  ", " ".join("%02X" % b for b in raw))
    print("== 从 0x777800（已知块头附近）对齐解码 ==")
    for ins in md.disasm(raw[0x777800 - start:], 0x777800):
        print("  %08X  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))
        if ins.address > 0x777830:
            break
    print("== 反查函数头：从 0x777800 向前找 ret/c3+填充 ==")
    back = data[off_of(0x777700):off_of(0x777800)]
    last_cc = max(i for i, b in enumerate(back) if b in (0xCC,))
    print("  最近 0xCC 填充止于 %08X" % (0x777700 + last_cc + 1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
