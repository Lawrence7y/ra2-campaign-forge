# -*- coding: utf-8 -*-
"""B3 终核：① 007A5290 完整函数流（③b① 判定）；② 全 18 行循环+循环体内非栈写扫描（③b④）。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import (X86_INS_JMP, X86_INS_JA, X86_INS_JAE, X86_INS_JB, X86_INS_JBE,
                          X86_INS_JG, X86_INS_JGE, X86_INS_JL, X86_INS_JLE,
                          X86_INS_CALL, X86_OP_MEM, X86_OP_REG, X86_REG_EBP, X86_REG_ESP)
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = True; MD.skipdata = True
WORK = os.path.dirname(os.path.abspath(__file__))
def hx(x): return "%08X" % (x & 0xFFFFFFFF)
data = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))
by = {r["entry"]: r for r in data}

# ---- A. 007A5290 全函数反汇编 ----
print("########## A. 007A5290 全函数流 (size=823) ##########")
r = by["007A5290"]
ea = 0x7A5290; size = r["atlas"]["size"]
insns = list(MD.disasm(R.read_va(ea, size), ea))
for i in insns:
    tag = ""
    if i.id == X86_INS_CALL:
        tag = "  <CALL>"
    print("  %08X %-7s %-34s | %s%s" % (i.address, i.mnemonic, i.op_str, i.bytes.hex(), tag))

# ---- B. 全批循环+非栈写扫描 ----
print("\n\n########## B. 全 18 行：后向跳(循环) + 循环体内非栈写 扫描 ##########")
JCC = {X86_INS_JA,X86_INS_JAE,X86_INS_JB,X86_INS_JBE,X86_INS_JG,X86_INS_JGE,
       X86_INS_JL,X86_INS_JLE}
def mem_nonstack_write(ins):
    # 写内存且基址不是 esp/ebp（栈）
    if not ins.operands: return False
    op0 = ins.operands[0]
    if op0.type != X86_OP_MEM: return False
    wr = False
    try:
        _, w = ins.regs_access()
        # 判写：mov/xor/cmp 类看 mnemonic 方向；用 capstone groups 简化看 mnemonic
    except Exception:
        w = []
    text = ins.mnemonic
    if text not in ("mov","xor","or","and","add","sub","inc","dec","movzx","movsx","stosd","stosb","sete","setne","setz","setnz"):
        return False
    mem = op0.mem
    if mem.base in (X86_REG_ESP, X86_REG_EBP): return False
    return True

for r in data:
    e = r["entry"]; ea = int(e,16); size = r["atlas"]["size"]
    insns = list(MD.disasm(R.read_va(ea, size), ea))
    idx = {ins.address:i for i,ins in enumerate(insns)}
    loops = []
    for j,ins in enumerate(insns):
        if ins.id not in JCC and ins.id != X86_INS_JMP: continue
        if not ins.operands or ins.operands[0].type != 2: continue  # X86_OP_IMM=2
        tgt = ins.operands[0].imm & 0xFFFFFFFF
        if tgt < ins.address and ea <= tgt:  # 后向跳=循环
            nonstack_w = []
            for k in range(idx.get(tgt,j), j+1):
                if mem_nonstack_write(insns[k]):
                    nonstack_w.append("%08X:%s %s" % (insns[k].address, insns[k].mnemonic, insns[k].op_str))
            loops.append((ins.address, ins.mnemonic, tgt, len(nonstack_w), nonstack_w[:4]))
    if loops:
        print("%s %-24s loops=%d" % (e, r["hint_name"][:24], len(loops)))
        for la,lm,tgt,nw,samples in loops[:6]:
            print("    backjmp %08X %s -> %08X  nonstack_writes_in_loop=%d %s" % (la,lm,tgt,nw,samples))
    else:
        print("%s %-24s NO_BACKWARD_JUMP (无循环)" % (e, r["hint_name"][:24]))
