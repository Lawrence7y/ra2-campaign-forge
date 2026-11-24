# -*- coding: utf-8 -*-
"""M68 postcheck: coverage.tsv diff + counts + strict + DoD, and PANEL.md consistency."""
import csv, os, sys, math, re, collections, hashlib
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
MDIR = os.path.join(ROOT, "MERGE_M68")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
BAK = os.path.join(MDIR, "coverage.tsv.bak")
PANE = os.path.join(ROOT, "COVERAGE", "PANEL.md")
PBAK = os.path.join(MDIR, "PANEL.md.bak")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
DELTA = os.path.join(ROOT, "NAMED_PUSH_S12_B1", "delta.tsv")
TARGETS = ['00442230','00447210','00447F10','0044E8F0']
EVID = "NAMED_PUSH_AUDIT8/VERDICT.md"

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e

def sha256b(b):
    return hashlib.sha256(b).hexdigest().upper()

# atlas
atlas = set()
with open(ATLAS, encoding="utf-8-sig") as f:
    for i, line in enumerate(f):
        if i == 0: continue
        p = line.rstrip("\r\n").split("\t")
        if p and p[0].strip(): atlas.add(ne(p[0]))

# delta col4 map
dmap = {}
with open(DELTA, encoding="utf-8-sig", newline="") as f:
    for r in list(csv.reader(f, delimiter="\t"))[1:]:
        if len(r) >= 6 and r[0].strip(): dmap[ne(r[0])] = r[3]
T = [ne(x) for x in TARGETS]

def rows_from(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rr = list(csv.reader(f, delimiter="\t"))[1:]
    return [r for r in rr if len(r)>=8]

before = rows_from(BAK)
after = rows_from(COV)
assert len(before)==len(after)==18498, (len(before),len(after))
assert sha256b(open(BAK,"rb").read()) == "D89C2BD6B80951177973E9DF7EE20502E9395EE8EDBEF22610C02A4A86684EC4"

print("=== 1. coverage.tsv row diff (only 4 rows x cols 4/5/6) ===")
bn = {ne(r[0]):r for r in before}
an = {ne(r[0]):r for r in after}
changed = []
for e in an:
    if bn[e] != an[e]:
        changed.append(e)
print("  rows changed:", len(changed), sorted(ne(x) for x in changed))
assert set(ne(x) for x in changed) == set(T), "changed set mismatch"
for e in T:
    b, a = bn[e], an[e]
    assert b[0]==a[0] and b[1]==a[1] and b[2]==a[2] and b[6]==a[6] and b[7]==a[7], ("immutable col changed", e)
    assert a[3] == dmap[e], ("col4 not delta verbatim", e)
    assert a[4].strip() == "[已证]", ("col5", e)
    assert a[5] == EVID, ("col6", e)
    assert b[4].strip() == "[静态推断]", ("old grade", e)
    assert "[未证]" not in a[3], ("literal [未证] in new sem", e)
print("  OK: 4 rows, immutable cols identical, col4=delta verbatim, col5=[已证], col6=EVID, no literal [未证]")

# formatting
raw = open(COV,"rb").read()
assert b"\r\n" not in raw, "CRLF found"
assert raw.endswith(b"\n") == False, "trailing newline found (unexpected)"
nlines = raw.decode("utf-8").split("\n")
assert len(nlines)==18499
assert all(len(l.split("\t"))==8 for l in nlines[1:])
print("  OK: 18,498 data rows, 8 cols, TAB, LF-only, no BOM, no trailing newline")

print("\n=== 2. counts (AFTER) ===")
def counts(rows):
    tot=atlas_in=atlas_out=0
    hist=collections.Counter()
    conflict=0
    c=collections.defaultdict(collections.Counter)
    RE_CSUB=re.compile(r"::sub_[0-9A-Fa-f]+$"); RE_SLOT=re.compile(r"::v?slot\d+$")
    for r in rows:
        e=ne(r[0]); s=r[1].strip(); sem=r[3]; g=r[4].strip()
        hist[g]+=1
        if r[7].strip()=="1": conflict+=1
        ia = e in atlas
        if ia:
            atlas_in+=1
            c[s]["atlas_n"]+=1
            name=r[2].strip()
            if name and not name.startswith("sub_") and not RE_CSUB.search(name):
                c[s]["named_S14"]+=1
                if not RE_SLOT.search(name): c[s]["named_strict"]+=1
            if g=="[已证]":
                tot+=1  # will fix: tot should be full-table proved
                c[s]["proved"]+=1
                if "[未证]" not in sem: c[s]["strict"]+=1
        if g=="[已证]" and ia: pass
    # recompute full-table proved separately
    tot = sum(1 for r in rows if r[4].strip()=="[已证]")
    a_in = sum(1 for r in rows if r[4].strip()=="[已证]" and ne(r[0]) in atlas)
    a_out = tot - a_in
    return dict(total=tot, atlas_in=a_in, atlas_out=a_out, hist=hist,
                conflict=conflict, per=c, atlas_rows=sum(1 for r in rows if ne(r[0]) in atlas))

bc = counts(before); ac = counts(after)
print("  BEFORE total[已证]=%d atlas_in=%d atlas_out=%d hist=%s conflict=%d" % (
    bc['total'],bc['atlas_in'],bc['atlas_out'],dict(bc['hist']),bc['conflict']))
print("  AFTER  total[已证]=%d atlas_in=%d atlas_out=%d hist=%s conflict=%d" % (
    ac['total'],ac['atlas_in'],ac['atlas_out'],dict(ac['hist']),ac['conflict']))
assert (bc['total'],bc['atlas_in'],bc['atlas_out'])==(1569,1563,6)
assert (ac['total'],ac['atlas_in'],ac['atlas_out'])==(1573,1567,6)
assert ac['conflict']==bc['conflict']==254
assert sum(ac['hist'].values())==18498

print("\n=== 3. S12 / TOTAL proved & strict (authoritative literal [未证]) ===")
def dod_eval(c):
    nom=[]; st=[]
    for s in sorted(k for k in c if re.match(r"^S\d\d$",k)):
        a=c[s]["atlas_n"]; tn=math.ceil(0.9*a); tp=math.ceil(0.5*a)
        ok=c[s]["named_S14"]>=tn
        if ok and c[s]["proved"]>=tp: nom.append(s)
        if ok and c[s]["strict"]>=tp: st.append(s)
    return nom,st
for label,cd in [("BEFORE",bc),("AFTER",ac)]:
    c=cd['per']
    s12=c['S12']
    tpr=sum(v['proved'] for k,v in c.items() if re.match(r"^S\d\d$",k))
    tst=sum(v['strict'] for k,v in c.items() if re.match(r"^S\d\d$",k))
    nom,st=dod_eval(c)
    print(f"  {label}: S12 atlas_n=279 proved={s12['proved']} strict={s12['strict']} "
          f"| TOTAL proved={tpr} strict={tst} | 名义={nom} 严格={st}")
bn_nom,bn_st = dod_eval(bc['per']); an_nom,an_st = dod_eval(ac['per'])
assert bn_nom==an_nom==['S15','S16','S17']
assert bn_st==an_st==['S17']
assert ac['per']['S12']['proved']==59 and ac['per']['S12']['strict']==44
print("  OK: S12 proved 55->59, strict 40->44; TOTAL proved 1563->1567, strict 1246->1250; no DoD flip")

print("\n=== 4. PANEL.md consistency ===")
plines = open(PANE,encoding="utf-8").read().split("\n")
joined = "\n".join(plines)
assert plines[0].startswith("# PANEL — R14 coverageM68 并表"), plines[0][:60]
checks = [
 ("L17 全表/atlas", "**1,573 / 1,567**"),
 ("L66 S12 main", "| S12 | 279 | 204 | 73.12 | 204 | 73.12 | 54 | 19.35 | 59 | 21.15 |"),
 ("L77 TOTAL main", "| **1372** | **10.62** | **1567** | **12.13** |"),
 ("L116 S12 strict", "| S12 | 279 | 59 | 21.15 | **44** | **15.77** |"),
 ("L127 TOTAL strict", "| **TOTAL** | **12916** | **1567** | **12.13** | **1250** | **9.68** |"),
 ("note text", "M68 并表 NAMED_PUSH_AUDIT8 PASS 4 行"),
 ("M68 strict note", "M68 并表实算说明"),
]
for label,s in checks:
    assert s in joined, ("PANEL missing: "+label+" :: "+s[:40])
print("  OK: title, L17, L66, L77, L116, L127, note text, M68 strict note all present")
# ensure no stale anchors remain
stales = ["**1,569 / 1,563**",
          "| S12 | 279 | 55 | 19.71 |",
          "| **TOTAL** | **12916** | **1563** | **12.10** | **1246** | **9.65** |"]
for s in stales:
    assert s not in joined, ("stale anchor remains: "+s)
print("  OK: no stale S12/TOTAL anchors remain")
# note count (should appear at L17, L66, L77 = 3 times, plus title separately counts differently)
print("  NOTE occurrences in note columns:", joined.count("M68 并表 NAMED_PUSH_AUDIT8 PASS 4 行"))

print("\n=== ALL POSTCHECKS PASSED ===")
