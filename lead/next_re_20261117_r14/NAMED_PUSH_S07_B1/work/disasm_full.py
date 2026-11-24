# -*- coding: utf-8 -*-
"""逐行完整反汇编 + 站点上下文：手动核 ③b② / ③b①。用法: python disasm_full.py <entry> [entry...]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail=True; MD.skipdata=True

def dump(e, maxbytes=None):
    ea=int(e,16); info=R.ATLAS.get(e,{}); size=info.get("size",0)
    code=R.read_va(ea, size if size else 512)
    if maxbytes: code=code[:maxbytes]
    print("="*100)
    print("ENTRY %s %s size=%d"%(e, info, size))
    for ins in MD.disasm(code, ea):
        mark=""
        if ins.id==0:
            print("  %08X: .byte %s"%(ins.address, ins.bytes.hex())); continue
        # call sites highlight
        if ins.mnemonic.startswith("call") or ins.mnemonic.startswith("ret") or ins.mnemonic in ("jmp",):
            mark=" <<<"
        print("  %08X: %-9s %-34s | %s%s"%(ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex(), mark))

args = sys.argv[1:]
if not args:
    args=["00414290","00410C30","0041CFE0"]
for e in args:
    dump(e)
