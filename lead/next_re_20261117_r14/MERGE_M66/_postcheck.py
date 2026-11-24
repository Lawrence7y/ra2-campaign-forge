# -*- coding: utf-8 -*-
"""Post-change verification of coverage.tsv against backup + authoritative stats."""
import csv, os, re, collections, math, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
BAK = os.path.join(ROOT, "MERGE_M66", "coverage.tsv.bak")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
sys.path.insert(0, os.path.join(ROOT, "MERGE_M66"))

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e

def sha256(p):
    h = hashlib.sha256()
    with open(p,"rb") as f:
        for c in iter(lambda:f.read(1<<20),b""): h.update(c)
    return h.hexdigest().upper()

# load old/new as line arrays
old_lines = open(BAK, encoding="utf-8").read().split("\n")
new_lines = open(COV, encoding="utf-8").read().split("\n")
assert len(old_lines)==len(new_lines)==18499, (len(old_lines),len(new_lines))

# find changed lines
changed = [(i, old_lines[i], new_lines[i]) for i in range(len(old_lines)) if old_lines[i]!=new_lines[i]]
print("num changed lines:", len(changed))

# Verify each changed line: only cols 4,5,6 differ; cols 1,2,3,7,8 identical
ok = True
for i, o, n in changed:
    oc, nc = o.split("\t"), n.split("\t")
    assert len(oc)==len(nc)==8
    diffs = [j for j in range(8) if oc[j]!=nc[j]]
    if diffs != [3,4,5]:
        print(f"  !! line {i} diffs at cols {[d+1 for d in diffs]} (entry {oc[0]})")
        ok = False
    if nc[4] != "[已证]":
        print(f"  !! line {i} grade not [已证]: {nc[4]}")
        ok = False
print("only cols 4/5/6 differ on all changed lines, grade=[已证]:", ok)

# entries of changed lines
changed_entries = [o.split("\t")[0] for _,o,_ in changed]
print("changed entries:", sorted(changed_entries))

# Verify delta col4 original copied verbatim + evidence_path
def load_delta(path):
    with open(path,encoding="utf-8-sig",newline="") as f:
        rows=list(csv.reader(f,delimiter="\t"))
    return {r[0].strip():r for r in rows[1:] if r and r[0].strip()}
dd22=load_delta(os.path.join(ROOT,"NAMED_PUSH_S22_B2","delta.tsv"))
dd06=load_delta(os.path.join(ROOT,"NAMED_PUSH_S06_B1","delta.tsv"))
dd20=load_delta(os.path.join(ROOT,"NAMED_PUSH_S20_B1","delta.tsv"))
all_delta={}; 
for d,g in [(dd22,"A/S22"),(dd06,"B/S06"),(dd20,"B/S20")]:
    for e,r in d.items(): all_delta[e]=(r,g)
evid_ok=True
for i,o,n in changed:
    nc=n.split("\t"); e=nc[0].strip()
    dr,g=all_delta[e]
    if nc[3]!=dr[3]:
        print(f"  !! {e} semantics mismatch vs delta col4"); evid_ok=False
    expect_evid = "NAMED_PUSH_AUDIT6/VERDICT.md" if g=="A/S22" else "NAMED_PUSH_AUDIT5/VERDICT.md"
    if nc[5]!=expect_evid:
        print(f"  !! {e} evidence_path={nc[5]} expected {expect_evid}"); evid_ok=False
print("semantics verbatim + evidence_path correct:", evid_ok)

# Authoritative stats (replicating strict_panel.py)
atlas=set()
with open(ATLAS,encoding="utf-8-sig") as f:
    for i,line in enumerate(f):
        if i==0: continue
        p=line.rstrip("\r\n").split("\t")
        if p and p[0].strip(): atlas.add(ne(p[0]))

RE_SLOT=re.compile(r"::v?slot\d+$")
RE_CSUB=re.compile(r"::sub_[0-9A-Fa-f]+$")
with open(COV,encoding="utf-8-sig",newline="") as f:
    cov=list(csv.reader(f,delimiter="\t"))[1:]

d=collections.defaultdict(collections.Counter)
full_proved=0; atlas_out_proved=0; colcounts=collections.Counter()
for r in cov:
    colcounts[len(r)]+=1
    if len(r)<8: continue
    e=ne(r[0]); s=r[1].strip(); grade=r[4].strip()
    if grade=="[已证]": full_proved+=1
    if e not in atlas:
        d[s]["cov_nonatlas"]+=1
        if grade=="[已证]": atlas_out_proved+=1
        continue
    name=r[2].strip(); sem=r[3]
    d[s]["atlas_n"]+=1
    if name and not name.startswith("sub_"):
        d[s]["named_L"]+=1
        if not RE_CSUB.search(name):
            d[s]["named_S14"]+=1
            if not RE_SLOT.search(name): d[s]["named_strict"]+=1
    if grade=="[已证]":
        d[s]["proved_n"]+=1
        if "[未证]" not in sem: d[s]["proved_strict_n"]+=1

atlas_in_proved=sum(d[s]["proved_n"] for s in d)
tot_atlas=sum(d[s]["atlas_n"] for s in d)
tot_strict=sum(d[s]["proved_strict_n"] for s in d)
print("\n=== POST-CHANGE STATS (authoritative logic) ===")
print("data rows:",len(cov),"colcounts:",dict(colcounts))
print("full [已证]:",full_proved)
print("atlas-in [已证]:",atlas_in_proved)
print("atlas-out [已证]:",atlas_out_proved)
print("TOTAL atlas_n:",tot_atlas,"TOTAL strict:",tot_strict, f"({round(100.0*tot_strict/tot_atlas,2)}%)")
for s in ("S22","S06","S20"):
    a=d[s]["atlas_n"]; p=d[s]["proved_n"]; sp=d[s]["proved_strict_n"]
    print(f"  {s}: atlas={a} proved={p}({round(100.0*p/a,2)}%) strict={sp}({round(100.0*sp/a,2)}%) thrP={math.ceil(0.5*a)}")

# 达标
nom=sorted(s for s in d if re.match(r"^S\d\d$",s) and d[s]["named_S14"]>=math.ceil(0.9*d[s]["atlas_n"]) and d[s]["proved_n"]>=math.ceil(0.5*d[s]["atlas_n"]))
st=sorted(s for s in d if re.match(r"^S\d\d$",s) and d[s]["named_S14"]>=math.ceil(0.9*d[s]["atlas_n"]) and d[s]["proved_strict_n"]>=math.ceil(0.5*d[s]["atlas_n"]))
print("nominal 达标:",nom)
print("strict  达标:",st)

print("\nsha before(backup):",sha256(BAK))
print("sha after (cov)   :",sha256(COV))
