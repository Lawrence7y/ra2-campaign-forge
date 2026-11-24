# -*- coding: utf-8 -*-
"""M52 exploratory: inspect name patterns + validate named criteria vs M47."""
import re, collections, math

COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ATL = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"

def load_cov():
    rows = []
    with open(COV, "r", encoding="utf-8-sig", newline="") as f:
        lines = f.read().split("\n")
    # strip trailing empty
    while lines and lines[-1] == "":
        lines.pop()
    hdr = lines[0]
    assert hdr == "entry,subsystem,name,one_line_semantics,grade,evidence_path,n_sources,conflict", repr(hdr)
    for ln in lines[1:]:
        cols = ln.split("\t")
        assert len(cols) == 8, (len(cols), ln[:200])
        rows.append(cols)
    return rows

def load_atl():
    entries = []
    with open(ATL, "r", encoding="utf-8-sig", newline="") as f:
        lines = f.read().split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    hdr = lines[0]
    for ln in lines[1:]:
        cols = ln.split("\t")
        entries.append(cols[0].strip().upper())
    return entries

cov = load_cov()
atl = load_atl()
print("cov data rows:", len(cov))
print("atl data rows:", len(atl), "unique upper entries:", len(set(atl)))

# grade histogram (col 5 = index 4)
grade_c = collections.Counter(r[4] for r in cov)
print("grade histogram:", dict(grade_c))
# conflict col8 index7
conf1 = sum(1 for r in cov if r[7].strip() == "1")
print("conflict==1:", conf1)

# entry duplicates
ec = collections.Counter(r[0].upper() for r in cov)
print("cov unique upper entries:", len(ec), "dup groups:", sum(1 for v in ec.values() if v>1))

# atlas in/out
cov_entries_upper = set(ec.keys())
atl_set = set(atl)
in_atl = [r for r in cov if r[0].upper() in atl_set]
out_atl = [r for r in cov if r[0].upper() not in atl_set]
print("cov rows in atlas:", len(in_atl), "out atlas:", len(out_atl))

# proved total and atlas-internal
prov_all = sum(1 for r in cov if r[4].strip() == "[已证]")
prov_atl = sum(1 for r in in_atl if r[4].strip() == "[已证]")
print("proved all:", prov_all, "proved atlas-internal:", prov_atl)

# S22 count overall and out-atlas
s22_all = sum(1 for r in cov if r[1].strip() == "S22")
s22_out = sum(1 for r in out_atl if r[1].strip() == "S22")
print("S22 all:", s22_all, "S22 out-atlas:", s22_out)

# name pattern exploration
names = [r[2] for r in in_atl]
patterns = collections.Counter()
for n in names:
    if n == "":
        patterns["EMPTY"] += 1
    elif n.startswith("sub_"):
        patterns["starts_sub_"] += 1
    elif "::sub_" in n:
        patterns["contains_::sub_"] += 1
    elif re.search(r'::v?slot\d+', n):
        patterns["contains_slot"] += 1
    else:
        patterns["other_named"] += 1
print("atlas name patterns:", dict(patterns))

# Explicit counts for criteria variants
def L(n): return n != "" and not n.startswith("sub_")
def R14(n): return L(n) and not re.search(r'::sub_[0-9A-Fa-f]{8}$', n)
def STRICT(n): return R14(n) and not re.search(r'::v?slot\d+', n)

# compare with M47 table for S01-S21
M47 = {
 "S01":(53,11,11,9,6),"S02":(330,41,41,34,34),"S03":(194,125,125,12,38),
 "S04":(316,104,104,88,91),"S05":(643,521,520,157,165),"S06":(847,388,388,123,126),
 "S07":(804,587,587,64,67),"S08":(22,20,20,1,9),"S09":(1051,681,681,82,106),
 "S10":(526,513,513,82,130),"S11":(368,358,358,29,28),"S12":(279,204,204,54,55),
 "S13":(240,216,216,108,89),"S14":(489,330,330,135,107),"S15":(158,144,144,102,101),
 "S16":(90,81,81,54,46),"S17":(102,94,94,58,54),"S18":(659,497,497,57,54),
 "S19":(355,46,40,20,20),"S20":(410,399,399,42,46),"S21":(129,91,91,27,28),
}

print("\n=== per-subsystem recompute (atlas-internal only) ===")
print(f"{'S':5} {'atlas_n':>8} {'L':>5} {'R14':>5} {'STRICT':>7} {'proved':>7} | M47 (n,L,R14,STRICT,proved) match")
tot = [0,0,0,0,0]
recomputed = {}
for s in [f"S{i:02d}" for i in range(1,22)]:
    rs = [r for r in in_atl if r[1].strip() == s]
    n = len(rs)
    l = sum(1 for r in rs if L(r[2]))
    r14 = sum(1 for r in rs if R14(r[2]))
    st = sum(1 for r in rs if STRICT(r[2]))
    pv = sum(1 for r in rs if r[4].strip() == "[已证]")
    recomputed[s] = (n,l,r14,st,pv)
    for i,v in enumerate((n,l,r14,st,pv)): tot[i]+=v
    m = M47[s]
    ok = (n,l,r14,st,pv)==m
    print(f"{s:5} {n:8} {l:5} {r14:5} {st:7} {pv:7} | {m} {'OK' if ok else 'DIFF'}")

print("21-subsys totals (n,L,R14,STRICT,proved):", tuple(tot))

# S22 in atlas
s22_in = [r for r in in_atl if r[1].strip()=="S22"]
print("S22 in atlas:", len(s22_in),
      "L", sum(1 for r in s22_in if L(r[2])),
      "R14", sum(1 for r in s22_in if R14(r[2])),
      "STRICT", sum(1 for r in s22_in if STRICT(r[2])),
      "proved", sum(1 for r in s22_in if r[4].strip()=="[已证]"))

# grand total including S22
allt = [tot[i] + (0,) for i in range(5)]
s22t = (len(s22_in), sum(1 for r in s22_in if L(r[2])), sum(1 for r in s22_in if R14(r[2])),
        sum(1 for r in s22_in if STRICT(r[2])), sum(1 for r in s22_in if r[4].strip()=="[已证]"))
print("TOTAL incl S22:", tuple(tot[i]+s22t[i] for i in range(5)))
