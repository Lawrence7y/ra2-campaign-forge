"""_rsv_scope2.py — controlled reproduction of the author-era corpus by mtime cutoff.
Also reports the current tree and explicitly identifies self-artifacts.
Run: python -I -X utf8 ".../_rsv_scope2.py"
"""
import os, datetime
from collections import defaultdict
ROOT = r"D:/Project/ra2-campaign-forge/lead"
NEEDLES = ["只能判「不可复现」", "不能定位当年错误步骤"]
CUT = datetime.datetime(2026,11,9,12,19,0).timestamp()  # before _rs_CARRIER_MAP.md (12:20)

def mdlist():
    out=[]
    for dp,dn,fn in os.walk(ROOT):
        rel=os.path.relpath(dp,ROOT).replace("\\","/")
        d=0 if rel=="." else rel.count("/")+1
        for f in fn:
            if f.lower().endswith(".md"):
                p=os.path.join(dp,f)
                out.append((p,os.path.relpath(p,ROOT).replace("\\","/"),d,os.path.getmtime(p)))
    return out
ALL=mdlist()

def scan(items,label):
    scanned=0; hits=defaultdict(list)
    for p,rel,d,m in items:
        b=open(p,'rb').read()
        if b"\x00" in b: continue
        scanned+=1
        ls=b.decode('utf-8','replace').splitlines()
        ln=[i for i,L in enumerate(ls,1) if any(n in L for n in NEEDLES)]
        if ln: hits[rel]=ln
    tot=sum(len(v) for v in hits.values())
    print(f"[{label}] scanned={scanned} carrier_files={len(hits)} hit_lines={tot}")
    return scanned,len(hits),tot,hits

print("=== AUTHOR-ERA CORPUS (mtime <= 12:19, i.e. exactly the 943 md they scanned) ===")
era=[x for x in ALL if x[3]<=CUT]
print("  era .md total =",len(era)," d<=2 =",sum(1 for x in era if x[2]<=2))
a1=scan([x for x in era if x[2]<=2],"era d2 .md  (orchestrator scope)")
a2=scan(era,"era no-depth-cap .md (whole lead/)")
print()
print("=== CURRENT TREE (parallel agents added .md after 12:19) ===")
print("  current .md total =",len(ALL)," d<=2 =",sum(1 for x in ALL if x[2]<=2))
c1=scan([x for x in ALL if x[2]<=2],"current d2 .md")
c2=scan(ALL,"current no-depth-cap .md")
print()
print("=== FILES ADDED AFTER 12:19 (explicit) ===")
for p,rel,d,m in sorted(ALL,key=lambda x:x[3]):
    if m>CUT:
        b=open(p,'rb').read()
        ls=b.decode('utf-8','replace').splitlines()
        ln=[i for i,L in enumerate(ls,1) if any(n in L for n in NEEDLES)]
        print(f"   {rel}  mtime={datetime.datetime.fromtimestamp(m).strftime('%H:%M:%S')}  hits={ln}")
print()
print("=== DELTA current - era ===")
print(f"  d2: {c1[1]-a1[1]} files / {c1[2]-a1[2]} lines")
print(f"  no-cap: {c2[1]-a2[1]} files / {c2[2]-a2[2]} lines")
print("  no-cap era B section (strict 6) check:")
for r in sorted(a2[3]):
    if 'gate_doc_name_fix' in r: print("   sandbox:",r,a2[3][r])
