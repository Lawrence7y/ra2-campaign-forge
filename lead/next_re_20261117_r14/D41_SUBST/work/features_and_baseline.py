# -*- coding: utf-8 -*-
"""Fixed structural feature detection (capstone X86_OP_IMM=2) + random baseline."""
import os, sys, json, random, statistics
sys.path.insert(0, os.path.dirname(__file__))
from common import disasm_va
from capstone.x86 import X86_OP_IMM

WORK=os.path.dirname(__file__)
ATLAS=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
size={}
for line in open(ATLAS,encoding="utf-8",errors="replace"):
    f=line.split("\t")
    if f and f[0]!="entry":
        try: size[f[0].strip().upper()]=int(f[1])
        except: pass

cand=json.load(open(os.path.join(WORK,"cand_scan.json"),encoding="utf-8"))
cc=json.load(open(os.path.join(WORK,"caller_contract.json"),encoding="utf-8"))
ccmap={r["entry"]:r for r in cc}
yrpp=json.load(open(os.path.join(WORK,"yrpp_bindings.json"),encoding="utf-8"))
ch1=set()
for b in yrpp:
    if b["kind"] in ("CALL","JMP_THIS","THISCALL"): ch1.add(b["va"])

res=[]
for r in cand:
    va=int(r["entry"],16)
    sz=size.get(r["entry"],0x200)
    ins=disasm_va(va,min(sz,0x1000))
    backedges=[]; indirect_jmp=[]; vt_writes=[]; calls=0; negret=0; cmpn=0
    for i in ins:
        if i.mnemonic.startswith("j") and i.mnemonic not in ("jmp",) and i.operands and i.operands[0].type==X86_OP_IMM:
            t=i.operands[0].imm&0xffffffff
            if va<=t<=i.address: backedges.append(i.address)
        if i.mnemonic=="jmp" and i.operands and i.operands[0].type!=X86_OP_IMM:
            indirect_jmp.append(i.address)
        if i.mnemonic=="call": calls+=1
        if i.mnemonic.startswith("cmp"): cmpn+=1
        if i.mnemonic=="mov" and len(i.operands)==2 and i.operands[1].type==X86_OP_IMM:
            imm=i.operands[1].imm&0xffffffff
            if 0x7E0000<=imm<0x810000: vt_writes.append((i.address,"%08X"%imm))
    for j in range(len(ins)-1):
        if ins[j].mnemonic=="xor" and ins[j].op_str.startswith("eax, eax") and ins[j+1].mnemonic=="ret":
            negret+=1
    ccm=ccmap.get(r["entry"],{})
    feats={"backedges":len(backedges),"ijmp":len(indirect_jmp),"vt":len(vt_writes),"negret":negret,
           "calls":calls,"cmp":cmpn,"vt_sample":["%08X:%s"%x for x in vt_writes[:3]]}
    # ③b structural proxy: any of loop / jump table / vt-memory-shape / falsifiable-return
    feats["b3_struct"]=int(len(backedges)>0 or len(indirect_jmp)>0 or len(vt_writes)>0 or negret>0)
    feats["ch1"]=int(r["entry"] in ch1)
    feats["ch2"]=int(ccm.get("proven_caller_n",0)>=2)
    feats["novt"]=int(r["vaocc"]==0)
    feats["direct"]=int(r.get("direct_n",0)>0)
    feats["fourring_proxy"]=int(feats["novt"] and feats["direct"] and (feats["ch1"] or feats["ch2"]) and feats["b3_struct"])
    res.append({"entry":r["entry"],"sub":r["sub"],"name":r["name"],"size":sz,"feats":feats})

json.dump(res,open(os.path.join(WORK,"features_fixed.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("=== rows with fourring_proxy=1 ===")
for r in res:
    if r["feats"]["fourring_proxy"]:
        f=r["feats"]; print("  %s %-30s ch1=%d ch2=%d b3=%d loop=%d ijmp=%d vt=%d negret=%d direct=%d"%
            (r["entry"],r["name"],f["ch1"],f["ch2"],f["b3_struct"],f["backedges"],f["ijmp"],f["vt"],f["negret"],f["direct"]))

# random baseline: sample 8 from each subsystem's [静态推断] pool, 2000 trials, seed 20261119
def baseline(sub):
    pool=[r for r in res if r["sub"]==sub]
    rng=random.Random(20261119)
    hits=[]; b3hits=[]
    for _ in range(2000):
        s=rng.sample(pool,8)
        hits.append(sum(r["feats"]["fourring_proxy"] for r in s))
        b3hits.append(sum(r["feats"]["b3_struct"] and r["feats"]["novt"] for r in s))
    return {"pool_n":len(pool),"trials":2000,"mean_fourring":round(statistics.mean(hits),4),
            "dist":{str(k):hits.count(k) for k in sorted(set(hits))},
            "mean_novt_b3":round(statistics.mean(b3hits),4),
            "b3_pool_rate":round(sum(r["feats"]["b3_struct"] and r["feats"]["novt"] for r in pool)/len(pool),4)}

bl={s:baseline(s) for s in ("S02","S19")}
json.dump(bl,open(os.path.join(WORK,"baseline.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("\n=== random baseline (seed 20261119, 2000 trials, 8 rows) ===")
for s,v in bl.items(): print(" ",s,json.dumps(v,ensure_ascii=False))
print("wrote work/features_fixed.json work/baseline.json")
