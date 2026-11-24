# -*- coding: utf-8 -*-
"""Probe the exact structure of factory slot3 rows (single-row detailed dump)."""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C
from capstone.x86 import *

def dump_body(va, size, label):
    print("=== %s @%s size=%s ===" % (label, R.hx(va), size))
    for i in R.disasm_body(va, size):
        if i.id == 0:
            print("  %08X  %-24s (skipdata)" % (i.address, i.bytes.hex(" ")))
            continue
        print("  %08X  %-24s %s" % (i.address, i.bytes.hex(" "), i.mnemonic + " " + i.op_str))

if __name__ == "__main__":
    ea = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x6C1010
    sz = R.ATLAS.get(R.hx(ea), {}).get("size") or 128
    dump_body(ea, sz, "factory body")
    # direct calls in factory body
    print("\n--- direct calls in body ---")
    for i in R.disasm_body(ea, sz):
        if i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_IMM:
            print("  call imm %s @%s" % (R.hx(i.operands[0].imm & 0xFFFFFFFF), R.hx(i.address)))
        elif i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_MEM:
            m = i.operands[0].mem
            print("  call [base=%s idx=%s disp=%s] @%s" % (
                i.reg_name(m.base) if m.base else "-", i.reg_name(m.index) if m.index else "-",
                hex(m.disp & 0xFFFFFFFF), R.hx(i.address)))
    # presumed factory ctor = entry - 0xD0
    fc = ea - 0xD0
    print("\n--- presumed factory ctor = %s ---" % R.hx(fc))
    dump_body(fc, 32, "factory ctor")
    print("  ctor callers:", [R.hx(x) for x in C.find_direct_calls(fc)])
    print("  ctor atexit:", C.is_atexit_registered(fc))
