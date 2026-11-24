"""_rsv_ten.py — verify the '10 verbatim copies' and strict-6 claims independently.
Run: python -I -X utf8 ".../_rsv_ten.py"
"""
import os, hashlib, re
from collections import defaultdict
ROOT = r"D:/Project/ra2-campaign-forge/lead"
CANON_PATH = r"D:/Project/ra2-campaign-forge/lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md"
CANON = open(CANON_PATH,"r",encoding="utf-8",newline="").read().splitlines()[122]
CANON_SHA = hashlib.sha256(CANON.encode("utf-8")).hexdigest()
print("canonical line len =",len(CANON),"sha =",CANON_SHA)
print()

START = re.compile(r"^\s*(?:<!--[^>]*草案正文[^>]*逐字转录开始[^>]*-->|#{1,6}\s*↓{2,}[^\n]*草案正文[^\n]*|↓{3,}\s*草案正文\s*↓{3,})\s*$")
END   = re.compile(r"^\s*(?:<!--[^>]*草案正文[^>]*逐字转录结束[^>]*-->|#{1,6}\s*↑{2,}[^\n]*草案正文[^\n]*|↑{3,}\s*草案正文[^\n]*↑{3,})\s*$")
def blocks(ls):
    st=[];pr=[]
    for i,x in enumerate(ls,1):
        if START.match(x): st.append(i)
        elif END.match(x) and st: pr.append((st.pop(),i))
    return pr

exact=[]; near=defaultdict(list)
NEEDLES=["只能判「不可复现」","不能定位当年错误步骤"]
VARIANT=["只能判『不可复现』","不能定位当年错误步骤"]
allmd=[]
for dp,dn,fn in os.walk(ROOT):
    rel=os.path.relpath(dp,ROOT).replace("\\","/")
    d=0 if rel=="." else rel.count("/")+1
    for f in fn:
        if f.lower().endswith(".md"):
            p=os.path.join(dp,f); r=os.path.relpath(p,ROOT).replace("\\","/")
            if r.startswith("refsync_scope_20261109/"): continue
            allmd.append((p,r,d))
print("md scanned (excluding write domain) =",len(allmd))
for p,r,d in allmd:
    ls=open(p,'r',encoding='utf-8',newline='').read().splitlines()
    bl=blocks(ls)
    for i,x in enumerate(ls,1):
        for n in NEEDLES:
            if n in x: near['exact'].append((r,i,x==CANON,any(s<i<e for s,e in bl),x[:70]))
        for n in VARIANT:
            if n in x: near['variant'].append((r,i,x==CANON,any(s<i<e for s,e in bl),x[:70]))
        if x==CANON:
            exact.append((r,i,any(s<i<e for s,e in bl),d))
print()
print("=== lines VERBATIM EQUAL to group-① canonical (whole lead/, no depth cap) ===")
for r,i,ib,d in sorted(exact):
    print(f"   {r}:{i}  IN_BLOCK={ib}  dir_depth={d}")
print("COUNT =",len(exact)," distinct files =",len({r for r,_,_,_ in exact}))
inblock=[(r,i) for r,i,ib,d in exact if ib]
print("IN_APPENDABLE_BLOCK =",len(inblock),"distinct files =",len({r for r,_ in inblock}))
for x in sorted(inblock): print("   ",x)
print()
print("=== needle variant counts (whole lead/ md, excluding write domain) ===")
for k in ['exact','variant']:
    v=near[k]
    print(f"  {k}: lines={len(v)} distinct_files={len({x[0] for x in v})}")
