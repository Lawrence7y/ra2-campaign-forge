#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backward per-site base-register origin trace for all 179 writes.
For each site, walk backwards to the last instruction that writes the base register;
classify its source. Handles push/pop spills and ecx(THIS) propagation with a
bounded backward dataflow (worklist over (instruction_index, register) states).
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
with open(os.path.join(HERE,"..","EVIDENCE","w174_class_decision.txt"),"r",encoding="utf-8") as f:
    f.readline();fndec={}
    for ln in f:
        p=ln.rstrip().split("\t");fndec[int(p[0],16)]=p[1]
REGS={"eax","ecx","edx","ebx","esp","ebp","esi","edi"}
def rn(ins,rid):return ins.reg_name(rid) if rid else None
def dis(lo,hi):return [i for i in MD.disasm(TEXT[lo-TV:hi-TV],lo) if i.id!=0]
sites_by=collections.defaultdict(list)
for d in writes:
    lo,_=fr(d["va"]);sites_by[lo].append(d)

def reg_write(ins):
    """Return dst reg name if ins writes a register (explicit), else None."""
    ops=ins.operands
    if ins.mnemonic in ("push","cmp","test","jmp","je","jne","call","nop") or ins.mnemonic.startswith("j"):
        return None
    if ins.mnemonic in RETSET: return None
    if ops and ops[0].type==capstone.x86.X86_OP_REG:
        return rn(ins,ops[0].reg)
    return None
RETSET={"ret","retn","retf"}
def src_of(ins,reg):
    """Given ins writes `reg`, describe the source tag."""
    ops=ins.operands
    if ins.mnemonic in ("pop",):
        return ("POP",None)
    if len(ops)>=2:
        s=ops[1]
        if ins.mnemonic=="lea": return ("LEA",None)
        if s.type==capstone.x86.X86_OP_REG: return ("REG",rn(ins,s.reg))
        if s.type==capstone.x86.X86_OP_IMM: return ("IMM",s.imm)
        if s.type==capstone.x86.X86_OP_MEM:
            br=rn(ins,s.mem.base); return ("MEM",(br,s.mem.disp))
    return ("OTHER",None)

def resolve(fn_insns,k_start,reg,max_steps=4000):
    """Backward-walk from (k_start,reg) to origin. Returns (kind, detail, chain)."""
    chain=[]
    cur_k=k_start; cur_reg=reg
    for _ in range(max_steps):
        if cur_k<0: return ("ENTRY",None,chain)
        ins=fn_insns[cur_k]
        # find last write to cur_reg at or before cur_k (excluding site instruction itself for start)
        j=cur_k
        found=False
        while j>=0:
            w=reg_write(fn_insns[j])
            if w==cur_reg:
                found=True;break
            j-=1
        if not found:
            return ("ENTRY",None,chain)  # never written in function -> entry (ecx=THIS, others unknown)
        ins=fn_insns[j]
        kind,det=src_of(ins,cur_reg)
        chain.append((ins.address,cur_reg,ins.mnemonic,ins.op_str,kind,str(det)))
        if kind=="REG":
            cur_reg=det;cur_k=j-1;continue
        if kind=="MEM":
            br,disp=det
            if br=="ecx" and disp==0: return ("THIS",None,chain)  # [ecx]
            return ("MEM",det,chain)
        return (kind,det,chain)
    return ("LOOP",None,chain)

site_results=[]
for fn in sorted(sites_by):
    lo,hi=fr(fn);insns=dis(lo,min(hi,lo+0x6000))
    idx={ins.address:k for k,ins in enumerate(insns)}
    fdec=fndec.get(fn,"UNKNOWN")
    for d in sites_by[fn]:
        base=d["base"];k=idx.get(d["va"])
        if k is None:
            site_results.append((d["va"],fn,base,"NOSITE","",fdec,"?","?",""));continue
        kind,det,chain=resolve(insns,k-1,base)
        if kind=="ENTRY":
            resolved="THIS" if base=="ecx" else "ENTRY_"+base
        elif kind=="THIS":
            resolved="THIS"
        elif kind=="REG" or kind=="MEM":
            resolved="%s:%s"%(kind,str(det))
        else:
            resolved=kind+(":%s"%det if det else "")
        if resolved=="THIS":
            meaning="TEAM_StepCompleted" if fdec=="TEAM" else ("OBJ_NeedsRedraw" if fdec=="OBJ" else "UNKNOWN")
        elif resolved.startswith("MEM"):
            meaning="MEM_LOAD (object pointer from memory)"
        else:
            meaning="NONTHIS/UNKNOWN"
        site_results.append((d["va"],fn,base,resolved,"",fdec,meaning,len(chain),
                             " | ".join("%08X %s=%s %s %s"%(c[0],c[1],c[2],c[3],c[4]) for c in chain[:4])))
with open(os.path.join(HERE,"..","EVIDENCE","w174_site_origin_backward.tsv"),"w",encoding="utf-8") as f:
    f.write("va\tfn\tbase\tresolved\tdetail\tfn_class\tmeaning\tchain_len\tchain\n")
    for r in site_results:
        f.write("%08X\t%08X\t%s\t%s\t%s\t%s\t%s\t%d\t%s\n"%r)
print("resolved:",collections.Counter(r[3].split(':')[0] for r in site_results))
print("meaning:",collections.Counter(r[6] for r in site_results))
print("meaning x fnclass:",collections.Counter((r[6],r[5]) for r in site_results))
