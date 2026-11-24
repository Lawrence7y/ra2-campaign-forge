# -*- coding: utf-8 -*-
"""Exact call-site parameter bytes + provenance for the final selected rows."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, IB, SECS, md32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

WORK=os.path.dirname(__file__)
ATLAS=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
COV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
atlas=[]
for line in open(ATLAS,encoding="utf-8",errors="replace"):
    f=line.split("\t")
    if f and f[0]!="entry":
        try: atlas.append((int(f[0],16),int(f[1])))
        except: pass
atlas.sort()
def caller_of(s):
    lo,hi,b=0,len(atlas)-1,None
    while lo<=hi:
        m=(lo+hi)//2
        if atlas[m][0]<=s: b=m;lo=m+1
        else: hi=m-1
    return atlas[b][0] if b is not None and atlas[b][0]<=s<atlas[b][0]+atlas[b][1] else None
cov={}
for line in open(COV,encoding="utf-8",errors="replace"):
    f=line.rstrip("\n").split("\t")
    if len(f)>=5 and f[0]!="entry": cov[f[0].upper()]=(f[1],f[4],f[2])

text=[s for s in SECS if s[0]==".text"][0]
blob=DATA[text[4]:text[4]+text[3]]
md=md32()
targets=set("007C9442 00406130 00406170 0065CA80 00428B80 00405BE0 00401F90 004052F0 00407F40 00405190".split())
sites={}
prev=[]
for ins in md.disasm(blob,IB+text[1]):
    if ins.mnemonic=="call" and ins.bytes and ins.bytes[0]==0xE8 and ins.operands and ins.operands[0].type==X86_OP_IMM:
        t=ins.operands[0].imm&0xffffffff
        if "%08X"%t in targets:
            ce=caller_of(ins.address)
            ci=cov.get("%08X"%ce,("?","?","?")) if ce else ("?","?","?")
            sites.setdefault("%08X"%t,[]).append({"site":"%08X"%ins.address,"caller":("%08X"%ce) if ce else None,
                "grade":ci[1],"name":ci[2],"prev":[{"a":"%08X"%a,"b":h,"m":m,"o":o} for a,h,m,o in prev[-6:]]})
    prev.append((ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
json.dump(sites,open(os.path.join(WORK,"final_sites.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
for t in sorted(targets):
    ss=sites.get(t,[])
    print("=== %s sites=%d proven_callers=%s"%(t,len(ss),sorted(set(x["caller"] for x in ss if x["grade"]=="[已证]"))))
    for x in ss[:3]:
        if x["grade"]=="[已证]":
            print("   site %s caller %s [%s] %s"%(x["site"],x["caller"],x["grade"],x["name"]))
            for p in x["prev"]: print("       %s %-18s %s %s"%(p["a"],p["b"],p["m"],p["o"]))
print("wrote work/final_sites.json")
