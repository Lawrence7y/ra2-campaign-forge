#!/usr/bin/env python3
"""Disassemble selected function entries and trace `this` (ecx on thiscall entry)
to the base register used at the [reg+0x80] write sites.
Also prints the raw bytes around each write site for character-by-character value check.
"""
import os, sys, bisect, json
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
    return union[i], (union[i+1] if i+1<len(union) else TV+len(TEXT))

TARGET_FNS=[0x6E9140,0x6ECA70,0x438BF0,0x43DA80,0x454CE0,0x543780,0x6ECF10,
            0x6EDC70,0x6EDF10,0x6EF610,0x6EFE60,0x6F0130,0x448260,0x44D880]
with open(os.path.join(HERE,"..","EVIDENCE","w174_writes.json"),"r",encoding="utf-8") as f:
    D=json.load(f); writes=D["writesA"]
sites_by_fn={}
for d in writes:
    lo,hi=fr(d["va"])
    sites_by_fn.setdefault(lo,[]).append(d)

out=[]
for fn in TARGET_FNS:
    lo,hi=fr(fn)
    insns=[]
    for insn in MD.disasm(TEXT[lo-TV:hi-TV],lo):
        if insn.id==0:continue
        insns.append(insn)
    sites=sites_by_fn.get(fn,[])
    out.append("=== fn %08X range [%08X,%08X) n_insn=%d n_sites=%d ==="%(fn,lo,hi,len(insns),len(sites)))
    # first 24 instructions
    for insn in insns[:24]:
        out.append("  %08X  %-8s %s"%(insn.address,insn.mnemonic,insn.op_str))
    out.append("  ...")
    # for each site, print ±3 instructions with raw bytes
    idx={insn.address:k for k,insn in enumerate(insns)}
    for d in sites:
        k=idx.get(d["va"])
        if k is None: continue
        out.append("  --- site %08X base=%s src=%s:%s bytes=%s ---"%(d["va"],d["base"],d["src_kind"],d["src"],d["insn_bytes"]))
        for insn in insns[max(0,k-3):min(len(insns),k+3)]:
            mark=" <== SITE" if insn.address==d["va"] else ""
            out.append("    %08X  %-8s %s%s"%(insn.address,insn.mnemonic,insn.op_str,mark))
    out.append("")

with open(os.path.join(HERE,"..","EVIDENCE","w174_this_origin_probe.txt"),"w",encoding="utf-8") as f:
    f.write("\n".join(out)+"\n")
print("wrote this-origin probe, functions:",len(TARGET_FNS))
