#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Definitive class split for the 179 write sites.
Decision basis (all from authoritative YRpp headers + this-origin trace):
  ObjectClass+0x80 = NeedsRedraw (ObjectClass.h:281)
  TeamClass+0x80   = StepCompleted (TeamClass.h:84)
  TeamClass derives AbstractClass, NOT ObjectClass -> must be excluded.
Classification rules per function:
  TEAM  : address in [0x6E8000,0x6F1000) AND accesses [this+0x54] (FirstUnit)
          OR RTTI vfunc of TeamClass; plus YRpp-confirmed TeamClass methods.
  OBJ   : RTTI vfunc with ObjectClass ancestor OR accesses [this+0x520]
          (TechnoClass House) / ObjectClass-only offsets, OR address in known
          ObjectClass method regions with ecx->this and no +0x54.
  OTHER : explicitly non-ObjectClass, non-Team (e.g. pure consumer wrappers are OBJ).
  UNKNOWN: ambiguous.
Also traces the 18 register-value (class d) source registers.
"""
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
with open(os.path.join(HERE,"..","EVIDENCE","w174_classify_cfg.tsv"),"r",encoding="utf-8") as f:
    h=f.readline().rstrip().split("\t");cls_of={}
    for ln in f:
        p=ln.rstrip().split("\t");r=dict(zip(h,p));cls_of[int(r["va"],16)]=r["cls"]

S=json.load(open(os.path.join(ROOT,"re_atlas","evidence","rtti","symbols.json"),"r",encoding="utf-8"))
vf2class={}
for cn,ob in S["classes"].items():
    for v in ob.get("vfuncs",[]):
        try:va=int(v,16)
        except:continue
        vf2class.setdefault(va,[]).append(cn)
defanc={}
def ancestors(c,seen=None):
    if seen is None:seen=set()
    if c in seen or c not in S["classes"]:return seen
    seen.add(c)
    for bb in S["classes"][c].get("bases",[]):
        if bb!=c:ancestors(bb,seen)
    return seen

def dis(lo,hi):return [i for i in MD.disasm(TEXT[lo-TV:hi-TV],lo) if i.id!=0]

sites_by=collections.defaultdict(list)
for d in writes:
    lo,_=fr(d["va"]);sites_by[lo].append(d)

out=[]
out.append("fn\tdecision\trtti\toff54\toff520\tregion\tother_sig\tn_sites\tevidence")
decisions={}
for fn in sorted(sites_by):
    lo,_=fr(fn)
    insns=dis(lo, min(fr(fn)[1],lo+0x4000))
    offsets=set()
    # only offsets based on likely this-registers (ecx/esi/edi/ebp/ebx)
    for ins in insns:
        for op in ins.operands:
            if op.type==capstone.x86.X86_OP_MEM and op.mem.base and op.mem.disp>0 and op.mem.disp<0x2000:
                bn=ins.reg_name(op.mem.base)
                if bn in ("ecx","esi","edi","ebp","ebx","eax","edx"):
                    offsets.add(op.mem.disp)
    cnames=vf2class.get(fn,[])
    fam=set()
    for c in cnames:fam|=ancestors(c)
    objanc="ObjectClass" in fam
    teamanc=any("Team" in c for c in fam)
    off54=0x54 in offsets
    off520=0x520 in offsets
    region = "TEAMREG" if 0x6E8000<=fn<0x6F1000 else ("OBJREG" if (0x400000<=fn<0x610000 or 0x6D0000<=fn<0x6E8000 or 0x710000<=fn<0x760000) else "OTHERREG")
    # decision
    if teamanc or (region=="TEAMREG" and off54):
        dec="TEAM"
    elif objanc or off520 or (region=="OBJREG" and not off54):
        dec="OBJ"
    else:
        dec="UNKNOWN"
    decisions[fn]=dec
    other=sorted(x for x in offsets if x in (0x74,0x81,0x83,0x84,0x94,0x28,0x64,0x6c,0x7b,0x7d,0x7f))
    out.append("%08X\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t%s"%(
        fn,dec,",".join(cnames) or "-",off54,off520,region,
        ",".join("0x%X"%x for x in other),len(sites_by[fn]),
        "w174_fn_signature.txt / YRpp ObjectClass.h:281 TeamClass.h:84"))
with open(os.path.join(HERE,"..","EVIDENCE","w174_class_decision.txt"),"w",encoding="utf-8") as f:
    f.write("\n".join(out)+"\n")

# per-site class
site_out=[]
site_out.append("va\tfn\tclass\tcls_abcd\tsrc_kind\tsrc\tbase")
for d in writes:
    lo,_=fr(d["va"]);dec=decisions.get(lo,"UNKNOWN")
    site_out.append("%08X\t%08X\t%s\t%s\t%s\t%s\t%s"%(
        d["va"],lo,dec,cls_of.get(d["va"],"?"),d["src_kind"],d["src"],d["base"]))
with open(os.path.join(HERE,"..","EVIDENCE","w174_site_class.tsv"),"w",encoding="utf-8") as f:
    f.write("\n".join(site_out)+"\n")

print("function decisions:",collections.Counter(decisions.values()))
print("site decisions:",collections.Counter(decisions[fr(d['va'])[0]] for d in writes))
print("TEAM fns:",[hex(x) for x in sorted(decisions) if decisions[x]=="TEAM"])
print("UNKNOWN fns:",[hex(x) for x in sorted(decisions) if decisions[x]=="UNKNOWN"])
# cross tab class x abcd
ct=collections.Counter((decisions[fr(d['va'])[0]],cls_of.get(d["va"],"?")) for d in writes)
print("crosstab:",sorted(ct.items()))
