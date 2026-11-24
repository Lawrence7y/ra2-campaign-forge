# -*- coding: utf-8 -*-
"""Detect ③b structural features in all no-vtable candidates: backedges, jump tables, vt writes, error codes, guard-returns."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from common import disasm_va, md32, DATA, IB, SECS

WORK=os.path.dirname(__file__)
ATLAS=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
size={}
for line in open(ATLAS,encoding="utf-8",errors="replace"):
    f=line.split("\t")
    if f and f[0]!="entry":
        try: size[f[0].strip().upper()]=int(f[1])
        except: pass

cand=json.load(open(os.path.join(WORK,"cand_scan.json"),encoding="utf-8"))
res=[]
for r in cand:
    if r["vaocc"]!=0: continue
    va=int(r["entry"],16)
    sz=size.get(r["entry"],0x200)
    ins=disasm_va(va,min(sz,0x1000))
    addrs=[i.address for i in ins]
    backedges=[]; indirect_jmp=[]; vt_writes=[]; calls=0; negret=[]
    for i in ins:
        # backward conditional jump
        if i.mnemonic.startswith("j") and i.mnemonic not in ("jmp",):
            for o in i.operands:
                if o.type==1:  # IMM
                    t=o.imm&0xffffffff
                    if t<=i.address and t>=va: backedges.append((i.address,"%08X"%t))
        if i.mnemonic=="jmp" and i.operands and i.operands[0].type!=1:
            indirect_jmp.append(i.address)
        if i.mnemonic=="call": calls+=1
        # mov [reg/], imm in vtable range 0x7E0000..0x800000
        if i.mnemonic=="mov" and len(i.operands)==2 and i.operands[1].type==1:
            imm=i.operands[1].imm&0xffffffff
            if 0x7E0000<=imm<0x810000: vt_writes.append((i.address,"%08X"%imm))
    # falsifiable return: xor eax,eax; ret
    for j in range(len(ins)-1):
        if ins[j].mnemonic=="xor" and ins[j].op_str.startswith("eax, eax") and ins[j+1].mnemonic=="ret":
            negret.append(ins[j].address)
    res.append({"entry":r["entry"],"sub":r["sub"],"name":r["name"],"size":sz,
                "n_ins":len(ins),"backedges":len(backedges),"backedge_sample":["%08X->%s"%x for x in backedges[:3]],
                "indirect_jmp":len(indirect_jmp),"ijmp_sample":["%08X"%x for x in indirect_jmp[:3]],
                "vt_writes":len(vt_writes),"vt_sample":["%08X:%s"%x for x in vt_writes[:3]],
                "calls":calls,"negret":len(negret),"direct_n":r.get("direct_n",0)})

json.dump(res,open(os.path.join(WORK,"struct_features.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
for sub in ("S02","S19"):
    print("=== %s no-vtable: structural ③b candidates ==="%sub)
    for r in res:
        if r["sub"]!=sub: continue
        score=(r["backedges"]>0)+(r["indirect_jmp"]>0)+(r["vt_writes"]>0)+(r["negret"]>0)
        if score>=1:
            print("  %s %-28s sz=%-4d ins=%-4d back=%d ijmp=%d vt=%d calls=%d negret=%d"%(
                r["entry"],r["name"],r["size"],r["n_ins"],r["backedges"],r["indirect_jmp"],r["vt_writes"],r["calls"],r["negret"]))
print("wrote work/struct_features.json")
