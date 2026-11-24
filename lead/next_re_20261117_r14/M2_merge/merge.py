# -*- coding: utf-8 -*-
"""M2 final merge. Writes ONLY inside COVERAGE/. Dry-run by default; pass --apply to commit.
Rules (per task + coverage_README.md):
 - only PASS/PARTIAL cards; apply PARTIAL explicit downgrades from VERDICT
 - already-same (entry+name+grade) -> skip
 - higher delta grade -> upgrade grade in-place (only permitted in-place change)
 - same grade but name/subsystem mismatch -> CONFLICTS.tsv append (dedup by entry+field), set conflict=1, keep old value
 - non-function (field offset/global/call site/dispatch/jump table/internal labels) -> probe table, NOT coverage
 - §966 guard: UNSOURCED_PROVED + PENDING downgrade entries -> do NOT re-promote
 - 'high' is classification confidence (different quantity) -> never a grade upgrade; flag for Lead
 - [已证] with missing evidence_path/file -> downgrade [未证] + PENDING_CORRECTIONS + report
 - coverage.tsv append-only: only grade column & conflict flag change in place; new rows appended at end
"""
import csv, os, sys, glob, re, collections
sys.stdout.reconfigure(encoding="utf-8")
APPLY = "--apply" in sys.argv
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
COVD = os.path.join(ROOT,"COVERAGE")
TEXT_END = 0x7E038D  # .text end from R14_COMMON §7 (imagebase 0x400000)
def rd(p):
    with open(p,"r",encoding="utf-8-sig",newline="") as f: return list(csv.reader(f,delimiter="\t"))
def wr(p,rows):
    with open(p,"w",encoding="utf-8",newline="") as f:
        csv.writer(f,delimiter="\t",lineterminator="\n").writerows(rows)
def ne(e):
    e=e.strip().upper()
    if e.startswith("0X"): e=e[2:]
    try: return "%08X"%int(e,16)
    except: return e
RANK={"[已证]":3,"[静态推断]":2,"[未证]":1}
def gr(g): return RANK.get(g.strip(),0)
def normg(g):
    g=g.strip()
    return {"已证":"[已证]","静态推断":"[静态推断]","未证":"[未证]","[已证·复用]":"[已证]",
            "[已证·观测]":"[已证]","[已证读数]":"[已证]","[未证·未调用]":"[未证]",
            "[推断·可观测]":"[静态推断]"}.get(g,g)
def is_hdr(r): return r and r[0].strip().lower() in ("entry","entry(hex8)")

# --- load current state ---
covfile=os.path.join(COVD,"coverage.tsv"); covrows=rd(covfile); covhdr=covrows[0]
covidx={ne(r[0]):i for i,r in enumerate(covrows) if i>0 and r and r[0].strip()}
conf_file=os.path.join(COVD,"CONFLICTS.tsv"); confrows=rd(conf_file)
probe_file=os.path.join(COVD,"probe_and_data_entries.tsv"); prow=rd(probe_file); probidx={ne(r[0]):i for i,r in enumerate(prow) if i>0 and r and r[0].strip()}
pend_file=os.path.join(COVD,"PENDING_CORRECTIONS.tsv"); pendrows=rd(pend_file)
# protected = unsourced41 + pending entries whose audited grade < current
uns=set(ne(r[0]) for r in rd(os.path.join(COVD,"UNSOURCED_PROVED.tsv"))[1:] if r and r[0].strip())
protected=set(uns)
for r in pendrows[1:]:
    if len(r)>4 and r[2].strip()=="grade":
        m1=re.search(r"\[(已证|静态推断|未证)\]",r[3]); m2=re.search(r"\[(已证|静态推断|未证)\]",r[4])
        if m1 and m2 and RANK["["+m2.group(1)+"]"]<RANK["["+m1.group(1)+"]"]:
            protected.add(ne(r[1]))

def resolve_ev(card_dir,ev):
    ev=ev.strip()
    if not ev: return False
    for b in [ev.split("#")[0], ev.split(";")[0].split("#")[0]]:
        for base in [os.path.join(card_dir,b), os.path.join(ROOT,b), os.path.join(r"D:\Project\ra2-campaign-forge",b)]:
            if os.path.exists(base): return True
    return False

# explicit VERDICT downgrades on specific coverage_delta entries (from VERDICT text)
EXPLICIT_DN = {
 ("W177-B","0000021C"): "[未证]",   # verdict: +0x21C [已证]->[未证] (evidence only prose)
 ("S10-K1","00414B9E"): "[未证]",   # verdict: 0x414B9E mislabeled (broken RTTI chain) -> not [已证]
}
# explicit part of W177-B #6 also: 00A83D4C? no -- verdict #6 is about order event, map to no extra entry.

def is_nonfunc(e,sub,name,sem,val):
    if val < 0x10000: return True
    if val >= TEXT_END: return True  # global/data address (outside .text)
    if not re.match(r"^S\d\d$",sub): return True
    if re.search(r"guard_site|sw_singleton|Handler_|JumpTable|canplace_check|percell_validate|cell_loop_increment|fail_exit|shortpath_mode_gate|slot73_hook",name): return True
    if re.search(r"write \[|read \[|ctor write|INI write|use \+0x",name): return True
    if "call [vptr" in sem or sem.startswith("E8 direct call") or "E8 direct call" in sem: return True
    return False

deltas=sorted(glob.glob(os.path.join(ROOT,"**","coverage_delta.tsv"),recursive=True))
new_cov_rows=[]; new_probe_rows=[]; new_conf_rows=[]
grade_up=[]; conf_set=set(); skip_same=0; nochg=[]
protected_hold=[]; unfounded=[]; explicit_dn_applied=[]; high_flag=[]
card_report={}

# existing conflict keys (entry+field+the two values) for dedup
existing_conf_pairs=set()
for r in confrows[1:]:
    if len(r)>3: existing_conf_pairs.add((ne(r[0]),r[1].strip()))

for dpath in deltas:
    card_dir=os.path.dirname(dpath); card=os.path.basename(card_dir)
    vpath=os.path.join(card_dir,"_audit","VERDICT.md"); verdict="NO_VERDICT"
    if os.path.exists(vpath):
        txt=open(vpath,encoding="utf-8-sig").read()
        m=re.findall(r"裁决[：:]?\s*\*{0,2}\s*(PASS|PARTIAL|FAIL)",txt,re.I)
        if m: verdict=m[-1].upper()
    st=collections.Counter()
    if verdict not in ("PASS","PARTIAL"):
        card_report[card]=(verdict,0,0,0,"NOT MERGED: verdict")
        continue
    rows=rd(dpath)
    if rows and is_hdr(rows[0]): rows=rows[1:]
    for r in rows:
        if not r or not r[0].strip(): continue
        e=ne(r[0]); sub=r[1].strip() if len(r)>1 else ""
        name=r[2].strip() if len(r)>2 else ""
        sem=r[3].strip() if len(r)>3 else ""
        dg_raw=r[4].strip() if len(r)>4 else ""
        ev=r[5] if len(r)>5 else ""
        # explicit verdict downgrade
        if (card,e) in EXPLICIT_DN:
            dg=normg(EXPLICIT_DN[(card,e)]); explicit_dn_applied.append((card,e,dg_raw,dg))
        else:
            dg=normg(dg_raw)
        if e in covidx:
            c=covrows[covidx[e]]; cg=c[4].strip(); csub=c[1].strip(); cname=c[2].strip()
            if cg==dg and csub==sub and cname==name:
                st['skip']+=1; continue
            if dg=="high" or cg=="high":
                high_flag.append((card,e,cg,dg_raw)); st['high']+=1; continue
            if gr(dg)>gr(cg):
                if e in protected:
                    protected_hold.append((card,e,cg,dg,cname,name)); st['protected']+=1; continue
                if dg=="[已证]" and not resolve_ev(card_dir,ev):
                    unfounded.append((card,e,cg,dg,cname,name,ev)); st['unfounded']+=1; continue
                grade_up.append((card,e,cg,dg,csub,sub,cname,name)); st['grade_up']+=1
            elif gr(dg)<gr(cg):
                nochg.append((card,e,cg,dg)); st['keep_high']+=1
            else:
                # same grade -> name/subsystem conflicts (dedup existing by entry+field)
                added=False
                for fld,cv,dv in (("subsystem",csub,sub),("name",cname,name)):
                    if cv!=dv and (e,fld) not in existing_conf_pairs:
                        new_conf_rows.append([e,fld,"%s:%s"%(card,dv),"%s:%s"%("COVERAGE(prior)",cv)])
                        existing_conf_pairs.add((e,fld)); conf_set.add((e,fld)); st['conflict']+=1; added=True
                if not added: st['keep_same']+=1
        else:
            # new entry
            if e in probidx:
                st['probe_dup']+=1; continue
            try: val=int(e,16)
            except: val=0
            if is_nonfunc(e,sub,name,sem,val):
                new_probe_rows.append([e,"non_function",sub or "(misc)",name,dg,ev,card,"routed by M2 (non-function)"])
                probidx[e]=len(prow)+len(new_probe_rows)-1; st['probe_new']+=1
            else:
                new_cov_rows.append([e,sub,name,sem,dg,ev,"1","0"])
                covidx[e]=len(covrows)+len(new_cov_rows)-1; st['cov_new']+=1
    card_report[card]=(verdict,st['skip'],st['grade_up'],st['conflict'],st['cov_new'],st['probe_new'],st['protected'],st['high'],st['unfounded'],st['keep_high'],st['keep_same'],st['probe_dup'])

print("APPLY=",APPLY)
print("baseline cov=%d conf=%d probe=%d"%(len(covrows)-1,len(confrows)-1,len(prow)-1))
print("\nCARD REPORT: card verdict skip grade_up conflict cov_new probe_new protected high unfounded keep_high keep_same probe_dup")
for k,v in card_report.items(): print("  %-16s %s"%(k,v))
print("\nSUMMARY: grade_up=%d new_conf=%d cov_new=%d probe_new=%d protected_hold=%d high_flag=%d unfounded=%d explicit_dn=%d"%(
    len(grade_up),len(new_conf_rows),len(new_cov_rows),len(new_probe_rows),len(protected_hold),len(high_flag),len(unfounded),len(explicit_dn_applied)))
print("\nNEW COV ROWS:")
for x in new_cov_rows: print("   ",x)
print("\nEXPLICIT DOWNGRADES:")
for x in explicit_dn_applied: print("   ",x)
print("\nUNFOUNDED [已证]:")
for x in unfounded: print("   ",x)
print("\nHIGH FLAG (first 10):")
for x in high_flag[:10]: print("   ",x)

if APPLY:
    # 1) apply grade upgrades in place
    for card,e,cg,dg,csub,sub,cname,name in grade_up:
        r=covrows[covidx[e]]; r[4]=dg
    # 2) set conflict=1 for entries with new conflicts (keep old name/subsystem)
    for e,fld in conf_set:
        covrows[covidx[e]][7]="1"
    # 3) append new coverage rows
    covrows.extend(new_cov_rows)
    # 4) append conflict rows
    confrows.extend(new_conf_rows)
    # 5) append probe rows
    prow.extend(new_probe_rows)
    # 6) PENDING_CORRECTIONS for unfounded / explicit downgrades on NEW rows
    for card,e,cg,dg,cname,name,ev in unfounded:
        pendrows.append([card,e,"grade","[已证] (delta; no valid evidence)","[未证]","M2-merge","UNFOUNDED_PROVED (M2 guard)"])
    for card,e,dg_raw,dg in explicit_dn_applied:
        pendrows.append([card,e,"grade",dg_raw,dg,"VERDICT.md","explicit audit downgrade applied by M2"])
    wr(covfile,covrows); wr(conf_file,confrows); wr(probe_file,prow); wr(pend_file,pendrows)
    print("\nWROTE files.")
