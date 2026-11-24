# -*- coding: utf-8 -*-
"""上下文反汇编：给定 VA 列表，打印每个地址前后各 N 字节的指令流（带原始字节）。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32


def dump(va, before=0x20, after=0x30, md=None):
    md = md or Cs(CS_ARCH_X86, CS_MODE_32)
    md.skipdata = True
    start = va - before
    code = R.read_va(start, before + after)
    insns = list(md.disasm(code, start))
    for i in insns:
        mark = "  <<<<<" if i.address == va else ""
        bs = " ".join("%02X" % b for b in i.bytes)
        print("%08X  %-28s %-8s %s%s" % (i.address, bs, i.mnemonic, i.op_str, mark))


def body(entry_hex):
    ea = int(entry_hex, 16)
    info = R.ATLAS.get(entry_hex)
    size = info["size"] if info else 0x60
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.skipdata = True
    code = R.read_va(ea, size)
    print("=== body %s size=%d ===" % (entry_hex, size))
    for i in md.disasm(code, ea):
        bs = " ".join("%02X" % b for b in i.bytes)
        print("%08X  %-24s %-8s %s" % (i.address, bs, i.mnemonic, i.op_str))


if __name__ == "__main__":
    if sys.argv[1] == "body":
        for e in sys.argv[2:]:
            body(e)
            print()
    else:
        for a in sys.argv[2:]:
            va = int(a, 16)
            print("--- context @ %s ---" % a)
            dump(va)
            print()
