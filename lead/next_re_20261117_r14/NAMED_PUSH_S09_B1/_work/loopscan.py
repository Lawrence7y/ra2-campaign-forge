# -*- coding: utf-8 -*-
"""检测每个 entry 体内的回边(向后跳转)循环，并报告循环体内的非栈写指令。
用于判断 ③b④（完整循环 I/O + 边界检查 + 循环体内非栈写）。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone.x86 import *

ROWS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"b1_rows.json"),encoding="utf-8"))

def is_nonstack_write(ins):
    if ins.id not in (X86_INS_MOV, X86_INS_MOVSB, X86_INS_MOVSD, X86_INS_STOSD, X86_INS_STOSB,
                      X86_INS_INC, X86_INS_DEC, X86_INS_ADD, X86_INS_SUB, X86_INS_AND, X86_INS_OR,
                      X86_INS_XOR, X86_INS_SHL, X86_INS_SHR):
        return False
    for op in ins.operands:
        if op.type == X86_OP_MEM:
            base = op.mem.base
            if base not in (X86_REG_ESP, X86_REG_EBP):
                return True
    return False

for r in ROWS:
    ea=int(r["entry"],16)
    sz=R.ATLAS.get(r["entry"],{}).get("size") or 256
    insns=R.disasm(ea, R.read_va(ea,sz))
    addrs=[i.address for i in insns]
    idx={a:i for i,a in enumerate(addrs)}
    loops=[]
    for j,ins in enumerate(insns):
        tgt=None
        if ins.id==X86_INS_JMP and ins.operands and ins.operands[0].type==X86_OP_IMM:
            tgt=ins.operands[0].imm
        elif ins.id in R.JCC_IDS and ins.operands and ins.operands[0].type==X86_OP_IMM:
            tgt=ins.operands[0].imm
        if tgt is not None and tgt in idx and idx[tgt] < j:
            # backward branch: loop body [tgt .. ins]
            body=insns[idx[tgt]:j+1]
            writes=[b for b in body if is_nonstack_write(b)]
            loops.append((ins.address, tgt, len(body), len(writes),
                          [(b.address,b.mnemonic+' '+b.op_str) for b in writes[:3]]))
    if loops:
        print("="*90)
        print("%s %s loops=%d" % (r["entry"], r["name"], len(loops)))
        for la,tgt,n,nw,ws in loops:
            print("   backjmp@%08X -> %08X bodylen=%d nonstack_writes=%d" % (la,tgt,n,nw))
            for a,s in ws: print("       %08X %s" % (a,s))
    else:
        print("%s %s: NO backward-branch loop" % (r["entry"],r["name"]))
