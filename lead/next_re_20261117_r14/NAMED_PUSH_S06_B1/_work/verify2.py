# -*- coding: utf-8 -*-
"""Check -1 return paths of direct callees 0x7514D0 (row12) and 0x5FDD20 (row13)."""
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import recore as R
from capstone import *
from capstone.x86 import *

def ret_profile(va, cap, label):
    print("="*90)
    print("%s va=%08X cap=%s" % (label, va, cap))
    insns=R.disasm(va, R.read_va(va,cap))
    eax=None
    for ins in insns:
        if ins.id==0: continue
        if ins.id in (X86_INS_XOR,X86_INS_SUB) and len(ins.operands)==2 and R.is_eax(ins.operands[0]) and R.is_eax(ins.operands[1]):
            eax=("imm",0)
        elif ins.id==X86_INS_MOV and len(ins.operands)==2 and R.is_eax(ins.operands[0]):
            b=ins.operands[1]; eax=("imm",b.imm&0xffffffff) if b.type==X86_OP_IMM else ("reg/other",)
        elif ins.id==X86_INS_OR and len(ins.operands)==2 and R.is_eax(ins.operands[0]) and ins.operands[1].type==X86_OP_IMM:
            if eax==("imm",0): eax=("imm",ins.operands[1].imm&0xffffffff)
        elif ins.id==X86_INS_CALL: eax=("call",)
        elif ins.id==X86_INS_RET:
            print("    RET @%08X eax=%s  | %s" % (ins.address, eax, ins.bytes.hex(" ")))
            eax=None
        # print instructions around or eax,-1 / ret
        if ins.id==X86_INS_OR and len(ins.operands)==2 and R.is_eax(ins.operands[0]) and ins.operands[1].type==X86_OP_IMM:
            print("    OR eax,imm @%08X | %s" % (ins.address, ins.bytes.hex(" ")))

for va in (0x7514D0, 0x5FDD20):
    cap=R.ATLAS.get(R.hx(va),{}).get("size") or 400
    ret_profile(va,cap,"CALLEE")

# context around row12 cmp -1 @ 0x5F93BA and row13 cmp -1 @ 0x5FD1C0
for a in (0x5F93A0, 0x5FD1A0):
    print("="*90)
    print("CONTEXT around %08X" % a)
    for ins in R.disasm(a, R.read_va(a,0x50)):
        print("  %08X: %-8s %-30s | %s" % (ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex(" ")))
