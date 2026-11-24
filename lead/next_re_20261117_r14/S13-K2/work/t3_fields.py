#!/usr/bin/env python3
"""T3 increment: field-access dual support scan over 4 S13 class core functions.
Classify each [reg+off] mem op: data-write / data-read / virtual-call(call [reg+disp]).
Report Verses(+0xA0) write/read full set and virtual-call exclusion counts.
Three access forms: (A) absolute [0x..] (B) imm-base+[reg+off] (C) [glob]->[idx*4]->[eax+off].
"""
import sys, os, csv, struct
sys.path.insert(0, os.path.dirname(__file__))
import re_lib as R
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG, X86_INS_CALL

ROOT=r"D:\Project\ra2-campaign-forge"
ATLAS=os.path.join(ROOT,r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
atl={}
for r in csv.DictReader(open(ATLAS,encoding="utf-8",errors="replace"),delimiter="\t"):
    if r.get("entry"): atl[int(r["entry"],16)]=int(r["size"])

# representative core functions per class (entry, label)
FUNCS = {
 "WeaponTypeClass":[(0x771C70,"ctor"),(0x7730D0,"GetSize"),(0x7730E0,"WhatAmI")],
 "WarheadTypeClass":[(0x75CEC0,"ctor"),(0x75E4F0,"GetSize"),(0x75E500,"WhatAmI")],
 "BulletTypeClass":[(0x46BBC0,"ctor"),(0x46C860,"GetSize"),(0x46C850,"WhatAmI")],
 "BulletClass":[(0x466380,"ctor"),(0x4664C0,"Construct"),(0x4666E0,"AI"),(0x46B540,"GetSize")],
}

def classify(ins):
    """return (kind, off, regs) for a memory operand; kind in W/R/VC/ABS."""
    res=[]
    for op in ins.operands:
        if op.type!=X86_OP_MEM: continue
        if op.mem.base==0 and op.mem.index==0:
            res.append(("ABS", op.mem.disp, ""))
        elif ins.id==X86_INS_CALL:
            res.append(("VC", op.mem.disp, "call"))
        else:
            # W if this operand is destination (op index 0 for mov/arith store)
            res.append(("?", op.mem.disp, ""))
    return res

print("=== field-access classification per class core functions ===")
for cls, flist in FUNCS.items():
    dw={}; dr={}; vc=set(); absset=set()
    for entry,label in flist:
        size=atl.get(entry, 0x200)
        code=R.read(entry,size)
        for ins in R.md.disasm(code,entry):
            try: ops=ins.operands
            except Exception: continue
            mnemonic=ins.mnemonic
            # detect write: capstone implicit - for mov, first operand dest if mem
            for idx,op in enumerate(ops):
                if op.type!=X86_OP_MEM: continue
                base = R.md.reg_name(op.mem.base) if op.mem.base else "-"
                idxr = R.md.reg_name(op.mem.index) if op.mem.index else "-"
                if base=="-" and idxr=="-":
                    absset.add(op.mem.disp); continue
                if mnemonic=="call":
                    vc.add(op.mem.disp); continue
                # write heuristic: mem operand at position 0 for store mnemonics
                store = (idx==0 and mnemonic in ("mov","movzx","movsx","fld","fstp","fst","add","sub","and","or","inc","dec","xor","lea","imul","shl","shr","neg","not"))
                # refine: fld/fstp - fstp is store, fld is load
                if mnemonic=="fld": store=False
                if op.mem.disp>=0 and op.mem.disp<0x400:
                    (dw if store else dr).setdefault(op.mem.disp,set()).add(f"{entry:X}:{label}")
    print(f"\n-- {cls}: distinct data-write off={len(dw)}, data-read off={len(dr)}, virtual-call disp={len(vc)}, abs={len(absset)}")
    print(f"   VC disp (excluded from data-field reads): {sorted(vc)}")

# Verses +0xA0 full set across whole .text (data ops only, exclude call)
print("\n=== Verses field +0xA0: full read/write set across .text (non-call) ===")
code=R.read(0x401000,0x3DF38D)
w=[];rd=[]
for ins in R.md.disasm(code,0x401000):
    try: ops=ins.operands
    except Exception: continue
    if ins.mnemonic=="call": continue
    for idx,op in enumerate(ops):
        if op.type==X86_OP_MEM and op.mem.disp==0xA0:
            base=R.md.reg_name(op.mem.base) if op.mem.base else "-"
            idxr=R.md.reg_name(op.mem.index) if op.mem.index else "-"
            scale=op.mem.scale
            # store: mem at op0
            store=(idx==0 and ins.mnemonic in ("mov","fstp","fst","movzx","movsx","add","sub","and","or","inc","dec","xor"))
            rec=f"{ins.address:08X} {ins.mnemonic} [{base}+{idxr}*{scale}+0xA0]"
            (w if store else rd).append(rec)
print("  writes:",len(w)); [print("   ",x) for x in w[:30]]
print("  reads:",len(rd)); [print("   ",x) for x in rd[:30]]
