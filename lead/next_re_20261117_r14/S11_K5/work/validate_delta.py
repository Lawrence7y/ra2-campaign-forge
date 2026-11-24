#!/usr/bin/env python3
"""Validate S11-K5 coverage_delta.tsv against on-disk baseline. Read-only."""
from pathlib import Path
import csv,collections,hashlib
ROOT=Path(r"D:\Project\ra2-campaign-forge")
COV=ROOT/"lead/next_re_20261117_r14/COVERAGE/coverage.tsv"
ATL=ROOT/"lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv"
EXE=ROOT/"ra2youli/gamemd.exe"; CARD=ROOT/"lead/next_re_20261117_r14/S11_K5"
def rows(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f,delimiter="\t"): yield r
def norm(x): return x.strip().lower()
cov=[r for r in rows(COV) if r.get("subsystem","").strip().upper()=="S11"]
cov_by={norm(r["entry"]):r for r in cov}
atl={norm(r["entry"]) for r in rows(ATL)}
inter=set(cov_by)&atl
old_proved=sum(1 for e in inter if cov_by[e]["grade"].strip()=="[已证]")
_f=csv.DictReader((CARD/"coverage_delta.tsv").open("r",encoding="utf-8",newline=""),fieldnames=["entry","subsystem","name","one_line_semantics","grade","evidence_path"],delimiter="\t")
delta=list(_f)
bad=[]; gains=[]; grades=collections.Counter(); names=collections.Counter()
for r in delta:
    e=norm(r["entry"]); names[r["name"].strip()]+=1; grades[r["grade"].strip()]+=1
    if e not in cov_by: bad.append(("not_in_coverage",r["entry"])); continue
    o=cov_by[e]
    if o.get("subsystem","").strip().upper()!="S11": bad.append(("subsystem",r["entry"]))
    if o.get("name","").strip()!=r.get("name","").strip(): bad.append(("name_mismatch",r["entry"]))
    if o.get("grade","").strip()!=r.get("grade","").strip(): bad.append(("grade_mismatch",r["entry"]))
    if o.get("grade","").strip()=="[已证]" and r.get("grade","").strip()=="[已证]": gains.append(r["entry"])
    ev=CARD/r.get("evidence_path","")
    if not ev.exists() or ev.stat().st_size<10: bad.append(("evidence_missing",r["entry"]))
dupe_entries=[e for e,c in collections.Counter(norm(r["entry"]) for r in delta).items() if c>1]
dupe_names=[n for n,c in names.items() if c>1]
new_proved=old_proved+sum(1 for r in delta if r["grade"].strip()=="[已证]" and cov_by.get(norm(r["entry"]),{}).get("grade","").strip()!="[已证]")
lines=[]
lines.append("S11-K5 DELTA VALIDATION")
lines.append("SHA256="+hashlib.sha256(EXE.read_bytes()).hexdigest().upper())
lines.append("S11_ROWS=%d ATLAS_INTERSECTION=%d OLD_PROVED=%d NEW_PROVED=%d"%(len(cov),len(inter),old_proved,new_proved))
lines.append("DELTA_ROWS=%d GRADES=%r DUPLICATE_ENTRIES=%d DUPLICATE_NAMES=%d BAD=%d"%(len(delta),dict(grades),len(dupe_entries),len(dupe_names),len(bad)))
lines.append("GRADE_UPGRADES=0 SEMANTIC_REPROOFS_UNCHANGED_GRADE=%d IN_ATLAS=%d"%(len(gains),sum(1 for r in delta if norm(r["entry"]) in atl)))
for b in bad: lines.append("BAD "+repr(b))
for e in dupe_entries: lines.append("DUPE_ENTRY "+e)
for n in dupe_names: lines.append("DUPE_NAME "+n)
if bad or dupe_entries or dupe_names: raise SystemExit(1)
(CARD/"EVIDENCE/validate_delta.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")
print("\n".join(lines))
