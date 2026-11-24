# -*- coding: utf-8 -*-
"""M67 post-check: verify coverage.tsv after apply + recompute all counts (authoritative strict)."""
import csv, os, sys, collections, math
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
BAK = os.path.join(ROOT, "MERGE_M67", "coverage.tsv.bak")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
D20 = os.path.join(ROOT, "NAMED_PUSH_S20_B2", "delta.tsv")
D06 = os.path.join(ROOT, "NAMED_PUSH_S06_B3", "delta.tsv")
EVID = "NAMED_PUSH_AUDIT7/VERDICT.md"

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e

def read_tsv(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.reader(f, delimiter="\t"))

TARGETS = ['0062D9A0','0062FE90','00630090','00644960','006457A0','00645950',
           '0071E1D0','007220A0','007220D0','007281A0',
           '00749F30','0074BA30','00763D90']
TARGETS = [ne(x) for x in TARGETS]

dmap = {}
for p in (D20, D06):
    for r in read_tsv(p)[1:]:
        if len(r) >= 6 and r[0].strip():
            dmap[ne(r[0])] = r[3]

def fix_sem(sem, entry):
    if entry == ne("0062FE90"):
        sem = sem.replace("0x7E9D84", "0x7E9D64").replace("007E9D84", "007E9D64")
    return sem

before = read_tsv(BAK)
after = read_tsv(COV)
assert len(before) == len(after) == 18499, (len(before), len(after))  # header + 18498 data
assert before[0] == after[0]
bd = before[1:]; ad = after[1:]
assert all(len(r)==8 for r in bd) and all(len(r)==8 for r in ad)

# row-by-row diff
changed = []
for i,(b,a) in enumerate(zip(bd,ad)):
    if b != a:
        changed.append((i,b,a))
print("changed data rows=", len(changed))

chg_entries = []
for i,b,a in changed:
    e = ne(b[0])
    chg_entries.append(e)
    # only cols 4,5,6 (indices 3,4,5) may change
    for ci in (0,1,2,6,7):
        assert b[ci]==a[ci], ("immutable col changed", e, ci, b[ci], a[ci])
    assert a[4].strip()=="[已证]", (e,a[4])
    assert a[5]==EVID, (e,a[5])
    assert a[3]==fix_sem(dmap[e], e), ("semantics mismatch", e)
print("changed entries=", sorted(chg_entries))
assert set(chg_entries)==set(TARGETS), (sorted(set(chg_entries)^set(TARGETS)))

# 0062FE90 evidence
f = [a for i,b,a in changed if ne(b[0])==ne("0062FE90")][0]
print("\n=== 0062FE90 col4 post-fix ===")
print("  contains 007E9D64:", "007E9D64" in f[3], " contains 0x7E9D64:", "0x7E9D64" in f[3])
print("  contains 007E9D84:", "007E9D84" in f[3], " contains 0x7E9D84:", "0x7E9D84" in f[3])
print("  grade:", f[4], " evidence:", f[5])

# S06 rows: semantics must equal delta original (no ④ added)
print("\n=== S06 5 rows semantics == original delta (no ④ injected) ===")
for e in ['0071E1D0','007220A0','007220D0','007281A0','00763D90']:
    a = [a for i,b,a in changed if ne(b[0])==ne(e)][0]
    print(" ", e, "sem==delta:", a[3]==dmap[ne(e)], " has④:", "④" in a[3])

# recompute counts on AFTER
atlas = set()
with open(ATLAS, encoding="utf-8-sig") as fh:
    for i,line in enumerate(fh):
        if i==0: continue
        p = line.rstrip("\r\n").split("\t")
        if p and p[0].strip(): atlas.add(ne(p[0]))

full = [r for r in ad if r[4].strip()=="[已证]"] if False else [r for r in ad if len(r)>=8 and r[4].strip()=="[已证]"]
inprov = [r for r in full if ne(r[0]) in atlas]
outprov = [r for r in full if ne(r[0]) not in atlas]
print("\n=== COUNTS AFTER ===")
print("data rows=", len(ad))
print("full [已证]=", len(full), "expect 1569")
print("atlas-in [已证]=", len(inprov), "expect 1563")
print("atlas-out [已证]=", len(outprov), "expect 6")
grades = collections.Counter(r[4].strip() for r in ad)
print("grade histogram:", dict(grades))
print("conflict==1:", sum(1 for r in ad if r[7].strip()=="1"))

by = collections.Counter(r[1].strip() for r in inprov)
print("S20 proved=", by["S20"], "expect 61")
print("S06 proved=", by["S06"], "expect 135")

# authoritative strict (strict_panel.py line 78): proved_strict = atlas-in & [已证] & no literal [未证]
bystrict = collections.Counter()
for r in inprov:
    if "[未证]" not in r[3]:
        bystrict[r[1].strip()] += 1
print("S20 strict=", bystrict["S20"], "expect 49")
print("S06 strict=", bystrict["S06"], "expect 120")
print("TOTAL strict=", sum(bystrict.values()), "expect 1246")

# per-system atlas_n
atlas_n = collections.Counter()
for r in ad:
    if ne(r[0]) in atlas:
        atlas_n[r[1].strip()] += 1
print("S20 atlas_n=", atlas_n["S20"], "S06 atlas_n=", atlas_n["S06"], "TOTAL atlas rows=", sum(atlas_n.values()))

# DoD判定 before/after
RE_CSUB = __import__("re").compile(r"::sub_[0-9A-Fa-f]+$")
RE_SLOT = __import__("re").compile(r"::v?slot\d+$")
def dod(path):
    rows = read_tsv(path)[1:]
    d = collections.defaultdict(collections.Counter)
    for r in rows:
        if len(r)<8: continue
        e=ne(r[0]); s=r[1].strip()
        if e not in atlas: continue
        name=r[2].strip(); sem=r[3]; grade=r[4].strip()
        d[s]["atlas_n"]+=1
        if name and not name.startswith("sub_"):
            d[s]["named_L"]+=1
            if not RE_CSUB.search(name):
                d[s]["named_S14"]+=1
                if not RE_SLOT.search(name):
                    d[s]["named_strict"]+=1
        if grade=="[已证]":
            d[s]["proved"]+=1
            if "[未证]" not in sem:
                d[s]["proved_strict"]+=1
    nom=[]; strict=[]
    for s in sorted(k for k in d if __import__("re").match(r"^S\d\d$",k)):
        a=d[s]["atlas_n"]; tn=math.ceil(0.9*a); tp=math.ceil(0.5*a)
        if d[s]["named_S14"]>=tn and d[s]["proved"]>=tp: nom.append(s)
        if d[s]["named_S14"]>=tn and d[s]["proved_strict"]>=tp: strict.append(s)
    return nom,strict

nb,ns = dod(BAK); ab,ass = dod(COV)
print("\n=== DoD ===")
print("BEFORE nominal=",nb," strict=",ns)
print("AFTER  nominal=",ab," strict=",ass)
print("nominal flip:", nb!=ab, " strict flip:", ns!=ass)
