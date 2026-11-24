#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Clean, reproducible a/b/c/d classification with a literal rule.
Rule:
  a = src imm 0
  d = src register
  b = src imm 1 AND (cmp/test in the 6 instructions immediately before the write
                     with a conditional jump between that cmp/test and the write)
  c = src imm 1 otherwise
Also computes variants with windows 4/8/10/16 to show sensitivity.
"""
import os,sys,json,bisect,collections
import pefile,capstone
HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=r"D:\Project\ra2-campaign-forge"
sys.path.insert(0,os.path.join(ROOT,"lead","next_re_20261116_r12","_lead_audit"))
import audit_lib
b=audit_lib.Bin();pe=b.pe;T=b.sec(".text")
TEXT=pe.__data__[T["raw"]:T["raw"]+T["rawsize"]];TV=T["va"]
def md():
    m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);m.detail=True;m.skipdata=True;return m
MD=md()
rows,_=audit_lib.load_func_atlas();atlas=sorted([e for e,_ in rows])
calls,_,_=audit_lib.sweep_calls(b)
union=sorted(set(atlas)|set(t for t in calls if TV<=t<TV+len(TEXT)))
def fr(va):
    i=bisect.bisect_right(union,va)-1
    return union[i],(union[i+1] if i+1<len(union) else TV+len(TEXT))
with open(os.path.join(HERE,"..","EVIDENCE","w174_writes.json"),"r",encoding="utf-8") as f:
    D=json.load(f);writes=D["writesA"]
def dis(lo,hi):return [i for i in MD.disasm(TEXT[lo-TV:hi-TV],lo) if i.id!=0]
COND=set("je jne jz jnz jg jge jl jle ja jae jb jbe js jns jo jno jp jnp jpe jpo jcxz jecxz loop loope loopne".split())
CMP={"cmp","test"}
sites_by=collections.defaultdict(list)
for d in writes:
    lo,_=fr(d["va"]);sites_by[lo].append(d)
results={}
for W in (4,6,8,10,16):
    res=[]
    for fn in sorted(sites_by):
        lo,hi=fr(fn);insns=dis(lo,min(hi,lo+0x6000));idx={ins.address:k for k,ins in enumerate(insns)}
        for d in sites_by[fn]:
            va=d["va"]
            if d["src_kind"]=="imm" and d["src"]==0: cls="a"
            elif d["src_kind"]=="reg": cls="d"
            else:
                k=idx.get(va)
                pre=insns[max(0,k-W):k] if k is not None else []
                # need cmp/test AND a conditional jump after it before write
                gated=False
                for i,ins in enumerate(pre):
                    if ins.mnemonic in CMP:
                        if any(p.mnemonic in COND for p in pre[i+1:]):
                            gated=True;break
                cls="b" if gated else "c"
            res.append((va,cls))
    results[W]=dict(res)
    print("window",W,dict(collections.Counter(c for _,c in res)))
# write window-6 as primary
primary=results[6]
with open(os.path.join(HERE,"..","EVIDENCE","w174_classify_literal.tsv"),"w",encoding="utf-8") as f:
    f.write("va\tcls\n")
    for d in writes:
        f.write("%08X\t%s\n"%(d["va"],primary.get(d["va"],"?")))
# compare with CFG
with open(os.path.join(HERE,"..","EVIDENCE","w174_classify_cfg.tsv"),"r",encoding="utf-8") as f:
    h=f.readline().rstrip().split("\t");cfg={}
    for ln in f:
        p=ln.rstrip().split("\t");r=dict(zip(h,p));cfg[int(r["va"],16)]=r["cls"]
n=sum(1 for v in primary if primary[v]!=cfg.get(v))
print("literal(W6) vs CFG disagreements:",n)
