# -*- coding: utf-8 -*-
"""M2 definitive merge plan (read-only) — correct header handling, dedup vs cov+probe+conflicts.
Applies: PASS/PARTIAL only; non-function routing; §966 guard; PENDING/UNSOURCED protection;
same-grade name/subsystem -> CONFLICTS.tsv; higher grade -> upgrade."""
import csv, os, sys, glob, re, collections
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
PROJ = r"D:\Project\ra2-campaign-forge"
COVD = os.path.join(ROOT,"COVERAGE")
def rd(p):
    with open(p,"r",encoding="utf-8-sig",newline="") as f: return list(csv.reader(f,delimiter="\t"))
def ne(e):
    e=e.strip().upper()
    if e.startswith("0X"): e=e[2:]
    try: return "%08X"%int(e,16)
    except: return e
RANK={"[已证]":3,"[静态推断]":2,"[未证]":1}
def gr(g): return RANK.get(g.strip(),0)
def normg(g):
    g=g.strip()
    return {"已证":"[已证]","静态推断":"[静态推断]","未证":"[未证]"}.get(g,g)

covrows=rd(os.path.join(COVD,"coverage.tsv"))
cov={ne(r[0]):r for r in covrows[1:]}
prow=rd(os.path.join(COVD,"probe_and_data_entries.tsv"))
probe={ne(r[0]):r for r in prow[1:] if r and r[0].strip()}
confrows=rd(os.path.join(COVD,"CONFLICTS.tsv"))
confset=set((ne(r[0]),r[1],r[2],r[3]) for r in confrows[1:] if len(r)>3)
pendrows=rd(os.path.join(COVD,"PENDING_CORRECTIONS.tsv"))[1:]
pend_dn=set()
for r in pendrows:
    if len(r)>4 and r[2].strip()=="grade":
        # audited_value lower grade than current -> protected from re-promotion
        m1=re.search(r"\[(已证|静态推断|未证)\]",r[3]); m2=re.search(r"\[(已证|静态推断|未证)\]",r[4])
        if m1 and m2 and RANK["["+m2.group(1)+"]"]<RANK["["+m1.group(1)+"]"]:
            pend_dn.add(ne(r[1]))
unsrows=rd(os.path.join(COVD,"UNSOURCED_PROVED.tsv"))[1:]
uns=set(ne(r[0]) for r in unsrows)
protected = pend_dn | uns
print("protected(downgrade-revoked) entries:",len(protected))

def is_header(r): return r and r[0].strip().lower() in ("entry","entry(hex8)")

deltas=sorted(glob.glob(os.path.join(ROOT,"**","coverage_delta.tsv"),recursive=True))
plan=collections.defaultdict(list)
stats=collections.Counter()
cardstats={}
for dpath in deltas:
    card=os.path.basename(os.path.dirname(dpath))
    vpath=os.path.join(os.path.dirname(dpath),"_audit","VERDICT.md")
    verdict="NO_VERDICT"
    if os.path.exists(vpath):
        txt=open(vpath,encoding="utf-8-sig").read()
        m=re.findall(r"裁决[：:]?\s*\*{0,2}\s*(PASS|PARTIAL|FAIL)",txt,re.I)
        if m: verdict=m[-1].upper()
    if verdict not in ("PASS","PARTIAL"):
        plan["SKIP_CARD"].append((card,verdict)); cardstats[card]=(verdict,0,0,0,0,0); continue
    rows=rd(dpath)
    if rows and is_header(rows[0]): rows=rows[1:]
    c_same=c_up=c_nochg=c_conf=c_new=c_newprobe=c_skip=0
    for r in rows:
        if not r or not r[0].strip(): continue
        e=ne(r[0]); sub=r[1].strip() if len(r)>1 else ""
        name=r[2].strip() if len(r)>2 else ""
        sem=r[3].strip() if len(r)>3 else ""
        dg=normg(r[4]) if len(r)>4 else ""
        ev=r[5] if len(r)>5 else ""
        # non-function detection: field offset (value<0x10000) or non-S subsystem
        isnum=True
        try: val=int(e,16)
        except: isnum=False
        nonfunc = (isnum and val<0x10000) or (not re.match(r"^S\d\d$",sub))
        if e in cov:
            c=cov[e]; cg=c[4].strip(); csub=c[1].strip(); cname=c[2].strip()
            if cg==dg and csub==sub and cname==name:
                c_same+=1; continue
            if dg!=cg:
                if gr(dg)>gr(cg):
                    if e in protected:
                        plan["PROTECTED_NO_PROMOTE"].append((card,e,cg,dg,cname,name)); c_skip+=1
                    elif dg=="[已证]" and not ev.strip():
                        plan["UNFOUNDED_PROVED"].append((card,e,cg,dg,cname,name)); c_skip+=1
                    else:
                        plan["GRADE_UP"].append((card,e,cg,dg,csub,sub,cname,name)); c_up+=1
                else:
                    c_nochg+=1  # keep higher cov grade
            else:
                # same grade: name/subsystem mismatch
                key=(e,"", "", "")  # dedup check below by e+field
                a=(e,"subsystem",csub,sub); b=(e,"name",cname,name)
                added=False
                for t in (a,b):
                    if t[2]!=t[3]:
                        # check existing conflict with same entry+field regardless of card
                        exists=any(x[0]==e and x[1]==t[1] for x in [ (ne(cr[0]),cr[1],cr[2],cr[3]) for cr in confrows[1:] if len(cr)>3])
                        if not exists:
                            plan["CONFLICT_ADD"].append((card,t[0],t[1],t[2],t[3])); added=True
                if added: c_conf+=1
                else: c_nochg+=1
        else:
            # not in coverage
            if e in probe:
                c_newprobe+=1  # already routed
            elif nonfunc or "guard_site" in name or "singleton_" in name or "Handler_" in name or "JumpTable" in name or ("call " in sem.lower()):
                plan["NEW_TO_PROBE"].append((card,e,sub,name,dg,ev)); c_newprobe+=1
            else:
                plan["NEW_TO_COV"].append((card,e,sub,name,dg,ev,sem)); c_new+=1
    cardstats[card]=(verdict,c_same,c_up,c_nochg,c_conf,c_new,c_newprobe,c_skip)

print("\n=== CARD STATS (verdict,same,up,nochg,conf,new2cov,new2probe,protectedskip) ===")
for k,v in cardstats.items(): print("  %-16s %s"%(k,v))

for key in ["NEW_TO_COV","NEW_TO_PROBE","PROTECTED_NO_PROMOTE","UNFOUNDED_PROVED","SKIP_CARD","CONFLICT_ADD","GRADE_UP"]:
    print("\n=== %s : %d ==="%(key,len(plan[key])))
    for x in plan[key][:60]: print("   ",x)
