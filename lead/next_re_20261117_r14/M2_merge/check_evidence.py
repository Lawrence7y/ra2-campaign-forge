# -*- coding: utf-8 -*-
"""Check evidence_path existence for [已证] upgrade candidates and NEW function entries."""
import csv, os, sys, glob, collections
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
PROJ = r"D:\Project\ra2-campaign-forge"
def rd(p):
    with open(p,"r",encoding="utf-8-sig",newline="") as f: return list(csv.reader(f,delimiter="\t"))
def ne(e):
    e=e.strip().upper()
    try: return "%08X"%int(e,16)
    except: return e
RANK={"[已证]":3,"[静态推断]":2,"[未证]":1}
def gr(g): return RANK.get(g.strip(),0)
cov={ne(r[0]):r for r in rd(os.path.join(ROOT,"COVERAGE","coverage.tsv"))[1:]}
uns={ne(r[0]) for r in rd(os.path.join(ROOT,"COVERAGE","UNSOURCED_PROVED.tsv"))[1:]}

def resolve_ev(card_dir, ev):
    ev=ev.strip()
    if not ev: return None,False
    # strip fragment
    base=ev.split("#")[0]
    cands=[os.path.join(card_dir,base), os.path.join(PROJ,base), os.path.join(PROJ,"lead",base)]
    for c in cands:
        if os.path.exists(c): return c,True
    # try basename search inside card EVIDENCE
    return cands[0],False

print("=== [已证] delta rows on EXISTING entries where cov grade < [已证] (upgrade to 已证) ===")
cnt_ok=cnt_missing=cnt_uns=0
for dpath in sorted(glob.glob(os.path.join(ROOT,"**","coverage_delta.tsv"),recursive=True)):
    card_dir=os.path.dirname(dpath); card=os.path.basename(card_dir)
    for r in rd(dpath)[1:]:
        if not r or not r[0].strip(): continue
        e=ne(r[0]); dg=r[4].strip() if len(r)>4 else ""
        if e not in cov: continue
        cg=cov[e][4].strip()
        if gr(dg)>gr(cg) and gr(dg)==3:  # delta [已证], upgrade
            ev=r[5] if len(r)>5 else ""
            path,exists=resolve_ev(card_dir,ev)
            tag="UNSOURCED41" if e in uns else ""
            if e in uns: cnt_uns+=1
            if exists: cnt_ok+=1
            else: cnt_missing+=1
            print("  %-12s %s cov=%-8s ev=%-60s exists=%s %s" % (card,e,cg,ev[:60],exists,tag))
print("SUMMARY upgrade-to-[已证]: ok=%d missing=%d inUNSOURCED41=%d"%(cnt_ok,cnt_missing,cnt_uns))

print("\n=== NEW function-ish entries with [已证]: evidence check ===")
# Cards whose NEW entries might be real functions: S10-K1,S11-K1,S16-K1,S18-F1,W173_layer_add,W176_place81
for dpath in sorted(glob.glob(os.path.join(ROOT,"**","coverage_delta.tsv"),recursive=True)):
    card_dir=os.path.dirname(dpath); card=os.path.basename(card_dir)
    if card not in ("S10-K1","S11-K1","S16-K1","S18-F1","W173_layer_add","W176_place81","W177-B","W177-C","W177_live_place","W175_global8871","W178_guards"): continue
    for r in rd(dpath)[1:]:
        if not r or not r[0].strip(): continue
        e=ne(r[0])
        if e in cov: continue
        dg=r[4].strip() if len(r)>4 else ""
        ev=r[5] if len(r)>5 else ""
        path,exists=resolve_ev(card_dir,ev)
        print("  %-16s %s sub=%-10s grade=%-12s ev=%-50s exists=%s" % (card,e,r[1] if len(r)>1 else "",dg,ev[:50],exists))
