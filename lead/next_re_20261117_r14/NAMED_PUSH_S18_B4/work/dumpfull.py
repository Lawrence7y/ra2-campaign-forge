# -*- coding: utf-8 -*-
"""按需深核指定 entry：完整函数反汇编 + 站点窗口 + 被调函数返回点。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = True; MD.skipdata = True

def dump(ea, n, tag=""):
    code = R.read_va(ea, n)
    print("--- %s @%08X len=%d ---" % (tag, ea, n))
    for i in MD.disasm(code, ea):
        mark = ""
        if i.mnemonic in ("ret",) or "eax" in i.op_str or i.mnemonic in ("cmp","test","call","jmp") or i.mnemonic.startswith("j"):
            mark = "  <<<"
        print("  %08X  %-8s %-34s | %s%s" % (i.address, i.mnemonic, i.op_str, i.bytes.hex(), mark))

for e in sys.argv[1:]:
    ea = int(e, 16)
    size = R.ATLAS.get(e, {}).get("size", 512)
    print("="*120)
    print("ENTRY %s size=%d" % (e, size))
    dump(ea, size, "FULL BODY")
