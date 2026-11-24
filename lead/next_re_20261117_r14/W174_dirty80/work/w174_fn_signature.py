#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""For each of the 83 write-point functions, determine class via:
  (1) RTTI vfunc membership (symbols.json)
  (2) field-access signature of the write's base register:
      ObjectClass-family fields: 0x74 IsOnMap, 0x81 InLimbo, 0x83 IsSelected,
         0x84 HasParachute, 0x8c-0x90 flags, 0x94 LastLayer, 0x520 House, 0x28
      TeamClass fields: 0x54 FirstUnit, 0x7b/0x7d/0x7f unknown, 0x83 IsSuspended,
         0x64/0x6c timers, 0x28 Owner, frame 0xA8ED84
  (3) `this` origin: ecx on thiscall entry -> which register at the write site.
"""
import os, sys, json, bisect
import pefile, capstone
HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=r"D:\Project\ra2-campaign-forge"
sys.path.insert(0,os.path.join(ROOT,"lead","next_re_20261116_r12","_lead_audit"))
import audit_lib

b=audit_lib.Bin(); pe=b.pe; T=b.sec(".text")
TEXT=pe.__data__[T["raw"]:T["raw"]+T["rawsize"]]; TV=T["va"]
def md():
    m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);m.detail=True;m.skipdata=True;return m
MD=md()
rows,_=audit_lib.load_func_atlas(); atlas=sorted([e for e,_ in rows])
calls,_,_=audit_lib.sweep_calls(b)
union=sorted(set(atlas)|set(t for t in calls if TV<=t<TV+len(TEXT)))
def fr(va):
    i=bisect.bisect_right(union,va)-1
    return union[i],(union[i+1] if i+1<len(union) else TV+len(TEXT))

with open(os.path.join(HERE,"..","EVIDENCE","w174_writes.json"),"r",encoding="utf-8") as f:
    D=json.load(f); writes=D["writesA"]
with open(os.path.join(HERE,"..","EVIDENCE","w174_classify_cfg.tsv"),"r",encoding="utf-8") as f:
    hdr=f.readline().rstrip().split("\t"); cls_of={}
    for line in f:
        p=line.rstrip().split("\t");r=dict(zip(hdr,p));cls_of[int(r["va"],16)]=r["cls"]

sites_by_fn={}
for d in writes:
    lo,hi=fr(d["va"])
    sites_by_fn.setdefault(lo,[]).append(d)

# RTTI map
S=json.load(open(os.path.join(ROOT,"re_atlas","evidence","rtti","symbols.json"),"r",encoding="utf-8"))
vf2class={}
for cname,obj in S["classes"].items():
    for v in obj.get("vfuncs",[]):
        try: va=int(v,16)
        except: continue
        vf2class.setdefault(va,[]).append(cname)
def ancestors(c,seen=None):
    if seen is None:seen=set()
    if c in seen or c not in S["classes"]:return seen
    seen.add(c)
    for bb in S["classes"][c].get("bases",[]):
        if bb!=c:ancestors(bb,seen)
    return seen

# signature offsets (dword byte offsets accessed off the this-register)
OBJF={0x74,0x81,0x83,0x84,0x88,0x8c,0x8d,0x8e,0x8f,0x90,0x91,0x94,0x95,0x96,0x97,0x98,0x99}
TEAMF={0x54,0x58,0x5c,0x60,0x64,0x68,0x6c,0x70,0x74,0x75,0x76,0x77,0x78,0x79,0x7a,0x7b,
       0x7c,0x7d,0x7e,0x7f,0x80,0x81,0x82,0x83,0x84,0x85,0x86,0x87}

def dis(lo,hi):
    return [i for i in MD.disasm(TEXT[lo-TV:hi-TV],lo) if i.id!=0]

out=[]
out.append("fn\tRTTI_classes\tobj_ancestor\tbase_regs\tthis_origin\tnearby_offsets_obj\tnearby_offsets_team\tn_sites\tcls_counts")
fn_summary=[]
for fn in sorted(sites_by_fn):
    lo,hi=fr(fn)
    insns=dis(lo,hi)
    idx={ins.address:k for k,ins in enumerate(insns)}
    sites=sites_by_fn[fn]
    cnames=vf2class.get(fn,[])
    fam=set()
    for c in cnames: fam|=ancestors(c)
    objanc="ObjectClass" in fam
    # Determine the primary base register(s) at sites and simple this-origin:
    # ecx at entry; track mov reg,ecx (and mov reg,other_this) forward.
    base_regs=set(); offs_all=set(); origins=set()
    # forward this-alias propagation (linear, approximate but documented)
    thisregs={"ecx"}
    for ins in insns:
        ops=ins.operands
        if ins.mnemonic=="mov" and len(ops)>=2 and ops[0].type==capstone.x86.X86_OP_REG and ops[1].type==capstone.x86.X86_OP_REG:
            dn=ins.reg_name(ops[0].reg); sn=ins.reg_name(ops[1].reg)
            if sn in thisregs: thisregs.add(dn)
            elif dn in thisregs and sn not in thisregs: thisregs.discard(dn)
        # collect all mem offsets referenced with a base in {esi,edi,ebp,ebx,ecx,eax,edx}
        for op in ops:
            if op.type==capstone.x86.X86_OP_MEM and op.mem.base and op.mem.disp>0 and op.mem.disp<0x1000:
                offs_all.add(op.mem.disp)
    for d in sites:
        base_regs.add(d["base"])
        k=idx.get(d["va"])
        if k is not None:
            # nearest preceding 'mov <base>, ecx' within function
            origin="?"
            for j in range(k,-1,-1):
                ins=insns[j]
                if ins.mnemonic=="mov" and len(ins.operands)>=2 and ins.operands[0].type==capstone.x86.X86_OP_REG and ins.reg_name(ins.operands[0].reg)==d["base"]:
                    o=ins.operands[1]
                    if o.type==capstone.x86.X86_OP_REG:
                        origin=ins.reg_name(o.reg); break
                    if o.type==capstone.x86.X86_OP_MEM:
                        origin="[mem]"; break
            origins.add(origin)
    objhits=sorted(offs_all & OBJF)
    teamhits=sorted(offs_all & TEAMF)
    cnt={}
    for d in sites: cnt[cls_of.get(d["va"],"?")]=cnt.get(cls_of.get(d["va"],"?"),0)+1
    cnts=" ".join("%s:%d"%(k,v) for k,v in sorted(cnt.items()))
    line="%08X\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t%s"%(
        fn,",".join(cnames) or "-",objanc,",".join(sorted(base_regs)),
        ",".join(sorted(origins)),",".join("0x%X"%x for x in objhits),
        ",".join("0x%X"%x for x in teamhits),len(sites),cnts)
    out.append(line)
    fn_summary.append((fn,cnames,objanc,base_regs,origins,objhits,teamhits,len(sites),cnts))

with open(os.path.join(HERE,"..","EVIDENCE","w174_fn_signature.txt"),"w",encoding="utf-8") as f:
    f.write("\n".join(out)+"\n")
print("wrote fn signature for",len(fn_summary),"functions")
print("TeamClass-attributed fn:",[hex(x[0]) for x in fn_summary if any('Team' in c and 'TeamType' not in c for c in x[1])])
