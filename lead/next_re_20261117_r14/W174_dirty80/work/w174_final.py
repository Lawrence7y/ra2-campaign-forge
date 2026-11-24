#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate coverage_delta.tsv and final numbers for W174 deliverables."""
import os,sys,json,bisect,collections
HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=r"D:\Project\ra2-campaign-forge"
with open(os.path.join(HERE,"..","EVIDENCE","w174_writes.json"),"r",encoding="utf-8") as f:
    D=json.load(f);writes=D["writesA"]
# load site class decision
sitefile=os.path.join(HERE,"..","EVIDENCE","w174_site_class.tsv")
site={}
with open(sitefile,"r",encoding="utf-8") as f:
    h=f.readline().rstrip().split("\t")
    for ln in f:
        p=ln.rstrip().split("\t");r=dict(zip(h,p));site[int(r["va"],16)]=r
# load CFG classification
cfg={}
with open(os.path.join(HERE,"..","EVIDENCE","w174_classify_cfg.tsv"),"r",encoding="utf-8") as f:
    h=f.readline().rstrip().split("\t")
    for ln in f:
        p=ln.rstrip().split("\t");r=dict(zip(h,p));cfg[int(r["va"],16)]=r
# also heuristic (nearby-cmp) classification
heur={}
with open(os.path.join(HERE,"..","EVIDENCE","w174_classify_results.tsv"),"r",encoding="utf-8") as f:
    h=f.readline().rstrip().split("\t")
    for ln in f:
        p=ln.rstrip().split("\t");r=dict(zip(h,p));heur[int(r["va"],16)]=r

# group per function
byfn=collections.defaultdict(list)
for d in writes:
    fn=int(site[d["va"]]["fn"],16)
    byfn[fn].append(d)

# subsystem + name heuristics
def subsystem(fn,dec):
    if dec=="TEAM": return "S14"
    if 0x430000<=fn<0x460000: return "S05"  # Object/Building state setters
    if 0x460000<=fn<0x490000: return "S05"
    if 0x490000<=fn<0x5A0000: return "S05"
    if 0x5A0000<=fn<0x600000: return "S05"
    if 0x6D0000<=fn<0x6E8000: return "S07"  # render list
    if 0x710000<=fn<0x760000: return "S07"  # slot65 wrappers
    return "S05"

def fn_decision(fn):
    ds=set(site[d["va"]]["class"] for d in byfn[fn])
    return ds.pop() if len(ds)==1 else "MIXED"

def fn_name(fn,dec):
    # evidence-based names only where known
    known={0x438BF0:"ObjectClass state setter (NeedsRedraw set on change)",
           0x43CEA0:"BuildingClass slot65 DrawIfVisible (consumes NeedsRedraw)",
           0x43DA80:"BuildingClass DrawBehind/DrawExtras helper (sets NeedsRedraw)",
           0x6D97D0:"DrawList reverse iterator (consumes NeedsRedraw)",
           0x6D9920:"DrawList forward iterator (consumes NeedsRedraw)",
           0x6D9A50:"DrawList slice iterator (consumes NeedsRedraw)",
           0x71CC50:"TerrainClass slot65 wrapper (consumes NeedsRedraw)",
           0x6E9140:"TeamClass::Update-like (sets +0x80 StepCompleted)",
           0x5F4B10:"ObjectClass slot65 wrapper (consumes NeedsRedraw)",
           0x5F4D30:"ObjectClass::Limbo (sets +0x81, consumes NeedsRedraw)",
           0x6E8A90:"TeamClass ctor (initializes +0x80)"}
    if fn in known:return known[fn]
    if dec=="TEAM":return "TeamClass member (offset +0x80=StepCompleted)"
    if dec=="OBJ":return "ObjectClass-family member (offset +0x80=NeedsRedraw)"
    return "offset +0x80 writer (class [未证])"

def fn_grade(fn,dec):
    # §925-2 已证上下文的两处条件置位 / 四处消费清 0
    confirmed = (0x438BF0,0x43DA80,0x43CEA0,0x6D97D0,0x6D9920,0x6D9A50,0x71CC50,0x5F4B10,0x5F4D30)
    if fn in confirmed: return "[已证]"
    if dec=="TEAM" and (fn==0x6E9140 or 0x6E8000<=fn<0x6F1000):return "[静态推断]"
    if dec=="OBJ":return "[静态推断]"
    return "[未证]"

rows=[]
for fn in sorted(byfn):
    dec=fn_decision(fn)
    sub=subsystem(fn,dec)
    nm=fn_name(fn,dec)
    gr=fn_grade(fn,dec)
    ev=r"lead\next_re_20261117_r14\W174_dirty80\EVIDENCE\w174_site_class.tsv"
    # coverage_delta.tsv: entry<TAB>subsystem<TAB>name<TAB>one_line_semantics<TAB>grade<TAB>evidence_path
    # use nm as name, a short semantics line, grade, evidence path
    semantics = nm
    shortname = "fn_%08X"%fn
    rows.append((fn,sub,shortname,semantics,gr,ev,len(byfn[fn]),dec))
cov=os.path.join(HERE,"..","coverage_delta.tsv")
with open(cov,"w",encoding="utf-8") as f:
    for fn,sub,shortname,semantics,gr,ev,n,dec in rows:
        f.write("%08X\t%s\t%s\t%s\t%s\t%s\n"%(fn,sub,shortname,semantics,gr,ev))
print("coverage_delta rows:",len(rows))
print("class x abcd (CFG):")
cc=collections.Counter((site[d["va"]]["class"],cfg[d["va"]]["cls"]) for d in writes)
for k,v in sorted(cc.items()):print("  ",k,v)
print("total a/b/c/d CFG:",collections.Counter(cfg[d["va"]]["cls"] for d in writes))
print("total a/b/c/d heuristic:",collections.Counter(heur[d["va"]]["cls"] for d in writes))
print("unconditional (CFG c) sites:")
for d in writes:
    if cfg[d["va"]]["cls"]=="c":
        print("  %08X fn=%s class=%s base=%s src=%s"%(d["va"],site[d["va"]]["fn"],site[d["va"]]["class"],d["base"],d["src"]))
