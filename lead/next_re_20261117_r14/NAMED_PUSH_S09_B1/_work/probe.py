# -*- coding: utf-8 -*-
"""探针：按给定 VA 列表反汇编函数体（含字节），显示所有 ret 前的 eax 赋值，用于判定返回约定可伪证性。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone.x86 import *

def probe(va_str, size=None):
    va = int(va_str, 16)
    sz = size if size else R.ATLAS.get(R.hx(va), {}).get("size")
    if not sz:
        # infer next atlas
        nxt = min((int(k,16) for k in R.ATLAS if int(k,16) > va), default=None)
        sz = (nxt - va) if nxt else 64
    print("---- 0x%08X (atlas_size=%s, using=%d) ----" % (va, R.ATLAS.get(R.hx(va),{}).get('size'), sz))
    insns = R.disasm(va, R.read_va(va, sz))
    for i in insns:
        if i.id == 0:
            print("  %08X  db %s  (skipdata)" % (i.address, i.bytes.hex()))
            continue
        mark = ""
        if i.id == X86_INS_RET:
            mark = "  <<< RET"
        if i.id in (X86_INS_MOV, X86_INS_XOR, X86_INS_OR, X86_INS_CMP, X86_INS_TEST, X86_INS_CALL) or i.id in R.JCC_IDS:
            mark = mark or "  *"
        print("  %08X  %-20s %-40s%s" % (i.address, i.bytes.hex(), (i.mnemonic + " " + i.op_str), mark))

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("usage: python probe.py <va1> [va2 ...]")
        sys.exit(0)
    for a in args:
        probe(a)
