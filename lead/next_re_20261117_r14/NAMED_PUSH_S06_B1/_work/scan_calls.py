# -*- coding: utf-8 -*-
"""Scan all 18 bodies: classify direct call callees, find cmp/test+jcc with imm, and
check whether any directly-called callee returns a falsifiable imm sentinel (like -1/E_POINTER)."""
import os, sys, io, struct, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import recore as R
from capstone import *
from capstone.x86 import *

AN = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))

def ret_imm_consts(callee):
    """Return dict of ret sites and eax imm origin for a direct callee (via atlas size)."""
    cap = R.ATLAS.get(R.hx(callee), {}).get("size")
    if not cap: return None
    insns = R.disasm(callee, R.read_va(callee, cap))
    out = []
    eax = None
    for ins in insns:
        if ins.id==0: continue
        if ins.id in (X86_INS_XOR, X86_INS_SUB) and len(ins.operands)==2 and R.is_eax(ins.operands[0]) and R.is_eax(ins.operands[1]):
            eax = ("imm",0)
        elif ins.id==X86_INS_MOV and len(ins.operands)==2 and R.is_eax(ins.operands[0]):
            b=ins.operands[1]
            eax = ("imm", b.imm & 0xffffffff) if b.type==X86_OP_IMM else ("other",)
        elif ins.id==X86_INS_OR and len(ins.operands)==2 and R.is_eax(ins.operands[0]) and ins.operands[1].type==X86_OP_IMM:
            # or eax, imm where eax was 0 -> imm sentinel (e.g. or eax,-1)
            if eax==("imm",0): eax=("imm", ins.operands[1].imm & 0xffffffff)
        elif ins.id==X86_INS_CALL:
            eax=("call",)
        elif ins.id==X86_INS_RET:
            out.append((ins.address, eax)); eax=None
    return out

for rec in AN:
    e=rec["entry"]; va=int(e,16); size=rec["ring1"].get("atlas_size") or 256
    insns=R.disasm(va, R.read_va(va,size))
    print("="*100)
    print("ROW %s %s" % (e, rec["name"]))
    # direct calls
    for ins in insns:
        if ins.id==X86_INS_CALL and ins.operands and ins.operands[0].type==X86_OP_IMM:
            cal=ins.operands[0].imm & 0xffffffff
            if cal in (0x410320,0x410380):
                print("  DIRECT CALL 0x%08X @%08X  ==> E_POINTER VALIDATOR" % (cal,ins.address))
    # cmp eax,imm / cmp [..],-1 followed by jcc within 3
    for i,ins in enumerate(insns):
        imm=None; kind=None
        if ins.id==X86_INS_CMP and len(ins.operands)==2:
            a,b=ins.operands
            if R.is_eax(a) and b.type==X86_OP_IMM:
                imm=b.imm & 0xffffffff; kind="cmp eax,imm"
            elif a.type==X86_OP_MEM and b.type==X86_OP_IMM and b.imm & 0xffffffff in (0xffffffff,):
                imm=b.imm & 0xffffffff; kind="cmp [mem],imm"
        if kind and imm in (0xffffffff, 0x80004003, 0x80004005, 0x80070057):
            jcc=[]
            for k in range(i+1,min(i+4,len(insns))):
                if insns[k].id in R.JCC_IDS:
                    jcc.append((insns[k].address, insns[k].mnemonic)); break
            print("  %s imm=%s @%08X jcc=%s" % (kind, hex(imm), ins.address, jcc))
