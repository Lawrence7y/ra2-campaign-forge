# -*- coding: utf-8 -*-
"""Grade-up breakdown + reverse-engineer PANEL panel-table computation."""
import csv, os, sys, glob, re, collections
sys.stdout.reconfigure(encoding="utf-8")
ROOT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
PROJ=r"D:\Project\ra2-campaign-forge"
COVD=os.path.join(ROOT,"COVERAGE")
def rd(p):
    with open(p,"r",encoding="utf-8-sig",newline="") as f: return list(csv.reader(f,delimiter="\t"))
def ne(e):
    e=e.strip().upper()
    if e.startswith("0X"):e=e[2:]
    try:return "%08X"%int(e,16)
    except:return e
RANK={"[已证]":3,"[静态推断]":2,"[未证]":1}
def gr(g):return RANK.get(g.strip(),0)
def normg(g):
    g=g.strip();return {"已证":"[已证]","静态推断":"[静态推断]","未证":"[未证]","[已证·复用]":"[已证]","[已证·观测]":"[已证]","[已证读数]":"[已证]","[未证·未调用]":"[未证]","[推断·可观测]":"[静态推断]"}.get(g,g)
cov={ne(r[0]):r for r in rd(os.path.join(COVD,"coverage.tsv"))[1:]}
uns=set(ne(r[0]) for r in rd(os.path.join(COVD,"UNSOURCED_PROVED.tsv"))[1:] if r and r[0].strip())
protected=set(uns)
for r in rd(os.path.join(COVD,"PENDING_CORRECTIONS.tsv"))[1:]:
    if len(r)>4 and r[2].strip()=="grade":
        m1=re.search(r"\[(已证|静态推断|未证)\]",r[3]);m2=re.search(r"\[(已证|静态推断|未证)\]",r[4])
        if m1 and m2 and RANK["["+m2.group(1)+"]"]<RANK["["+m1.group(1)+"]"]:protected.add(ne(r[1]))
# recompute grade_up (same logic as merge) - summary by transition & card
trans=collections.Counter(); bycard=collections.Counter()
for dpath in sorted(glob.glob(os.path.join(ROOT,"**","coverage_delta.tsv"),recursive=True)):
    card=os.path.basename(os.path.dirname(dpath))
    rows=rd(dpath)
    if rows and rows[0][0].strip().lower() in ("entry","entry(hex8)"):rows=rows[1:]
    for r in rows:
        if not r or not r[0].strip():continue
        e=ne(r[0]); dg=normg(r[4]) if len(r)>4 else ""
        if e not in cov:continue
        cg=cov[e][4].strip()
        if dg=="high" or e in protected:continue
        if gr(dg)>gr(cg):
            trans[(cg,dg)]+=1; bycard[card]+=1
print("GRADE-UP TRANSITIONS:")
for k,v in sorted(trans.items(),key=lambda x:-x[1]):print("  %s -> %s : %d"%(k[0],k[1],v))
print("BY CARD:",dict(bycard))

# atlas set
ap=os.path.join(PROJ,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv")
atlas={}
with open(ap,encoding="utf-8-sig") as f:
    for i,line in enumerate(f):
        if i==0:continue
        p=line.rstrip("\n").split("\t")
        if p: atlas[ne(p[0])]=p
print("\nATLAS rows:",len(atlas))
# current panel target values (from PANEL.md)
# try to reproduce named_n / proved_n / doctype_n for atlas rows
def named(nm):
    # heuristic: named if not sub_/fn_/slot and not generic
    return not re.match(r"^(sub_|fn_|T_)",nm)
cur=collections.defaultdict(lambda:collections.Counter())
for e,r in cov.items():
    if e not in atlas:continue
    sub=r[1].strip(); nm=r[2].strip(); gd=r[4].strip(); sem=r[3].strip()
    cur[sub]["n"]+=1
    if named(nm):cur[sub]["named"]+=1
    if gd=="[已证]":cur[sub]["proved"]+=1
print("\nSUB  cur_n  named  proved (atlas only, heuristic named)")
for s in sorted(cur):print("  %s %5d %5d %5d"%(s,cur[s]['n'],cur[s]['named'],cur[s]['proved']))
