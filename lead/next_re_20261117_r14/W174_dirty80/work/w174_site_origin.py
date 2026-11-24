#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Per-site base-register origin trace (forward dataflow) for all 179 writes."""
import os, sys, json, bisect, collections
import pefile, capstone
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
with open(os.path.join(HERE,"..","EVIDENCE","w174_class_decision.txt"),"r",encoding="utf-8") as f:
    f.readline(); fndec={}
    for ln in f:
        p=ln.rstrip().split("\t");fndec[int(p[0],16)]=p[1]
with open(os.path.join(HERE,"..","EVIDENCE","w174_classify_cfg.tsv"),"r",encoding="utf-8") as f:
    h=f.readline().rstrip().split("\t");cls_of={}
    for ln in f:
        p=ln.rstrip().split("\t");r=dict(zip(h,p));cls_of[int(r["va"],16)]=r["cls"]
REGS={"eax","ecx","edx","ebx","esp","ebp","esi","edi"}
def rn(ins,rid):return ins.reg_name(rid) if rid else None
def dis(lo,hi):return [i for i in MD.disasm(TEXT[lo-TV:hi-TV],lo) if i.id!=0]
sites_by=collections.defaultdict(list)
for d in writes:
    lo,_=fr(d["va"]);sites_by[lo].append(d)
site_results=[]
for fn in sorted(sites_by):
    lo,hi=fr(fn)
    insns=dis(lo,min(hi,lo+0x5000))
    idx={ins.address:k for k,ins in enumerate(insns)}
    tag={r:("UNK",) for r in REGS}
    tag["ecx"]=("THIS",)
    site_needed=set(idx[d["va"]] for d in sites_by[fn] if d["va"] in idx)
    for k,ins in enumerate(insns):
        ops=ins.operands
        if ins.mnemonic=="mov" and len(ops)>=2:
            dst=ops[0];src=ops[1]
            if dst.type==capstone.x86.X86_OP_REG:
                dn=rn(ins,dst.reg)
                if src.type==capstone.x86.X86_OP_REG:
                    tag[dn]=tag.get(rn(ins,src.reg),("UNK",))
                elif src.type==capstone.x86.X86_OP_IMM:
                    tag[dn]=("IMM",)
                elif src.type==capstone.x86.X86_OP_MEM:
                    br=rn(ins,src.mem.base)
                    if br and tag.get(br,("UNK",))[0]=="THIS" and src.mem.disp>0:
                        tag[dn]=("THIS_MEM",src.mem.disp)
                    else:
                        tag[dn]=("MEM",br or "abs",src.mem.disp)
        elif ins.mnemonic in ("pop",) and len(ops)>=1 and ops[0].type==capstone.x86.X86_OP_REG:
            tag[rn(ins,ops[0].reg)]=("UNK",)
        elif ins.mnemonic in ("lea",) and len(ops)>=2 and ops[0].type==capstone.x86.X86_OP_REG:
            tag[rn(ins,ops[0].reg)]=("LEA",)
    for d in sites_by[fn]:
        base=d["base"]
        t=tag.get(base,("UNK",))
        fdec=fndec.get(fn,"UNKNOWN")
        if t[0]=="THIS":
            meaning = "TEAM_StepCompleted" if fdec=="TEAM" else ("OBJ_NeedsRedraw" if fdec=="OBJ" else "UNKNOWN")
        elif t[0]=="THIS_MEM":
            meaning = "THIS_MEM+%X (need class of pointed object)"%t[1]
        else:
            meaning = "NONTHIS_%s"%t[0]
        site_results.append((d["va"],fn,base,t[0],t[1] if len(t)>1 else "",fdec,meaning,cls_of.get(d["va"],"?"),d["src_kind"],d["src"]))
with open(os.path.join(HERE,"..","EVIDENCE","w174_site_origin.tsv"),"w",encoding="utf-8") as f:
    f.write("va\tfn\tbase\ttag\ttag_disp\tfn_class\tmeaning_0x80\tcls_abcd\tsrc_kind\tsrc\n")
    for r in site_results:
        f.write("%08X\t%08X\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n"%r)
print("site origin tags:",collections.Counter(r[3] for r in site_results))
print("meaning:",collections.Counter(r[6].split(' ')[0] for r in site_results))
print("origin x fnclass:",collections.Counter((r[3],r[5]) for r in site_results))
