# -*- coding: utf-8 -*-
"""M70 read-only analysis: preconditions, 11-row intersection, atlas membership, before counts."""
import csv, os, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
VERD = os.path.join(ROOT, "NAMED_PUSH_AUDIT11", "verdict.tsv")
DELTA= os.path.join(ROOT, "NAMED_PUSH_S22_B3", "delta.tsv")

EXPECT = ["006C2B10","006C2C90","006C2E10","006C2F90","006C3110",
          "006C3290","006C3410","006C3590","006C3890","006C3A10","006C3B90"]

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e

# atlas
atlas = set()
with open(ATLAS, encoding="utf-8-sig") as f:
    for i, line in enumerate(f):
        if i == 0: continue
        p = line.rstrip("\r\n").split("\t")
        if p and p[0].strip():
            atlas.add(ne(p[0]))
print("ATLAS data entries:", len(atlas))

# coverage
with open(COV, encoding="utf-8-sig", newline="") as f:
    allrows = list(csv.reader(f, delimiter="\t"))
cov = [r for r in allrows[1:] if len(r) >= 8]
header = allrows[0]
print("COVERAGE header cols:", len(header))
print("COVERAGE total lines (incl header):", len(allrows))
print("COVERAGE data rows (>=8 cols):", len(cov))
# column-count histogram
hist = collections.Counter(len(r) for r in allrows)
print("COVERAGE col-count histogram:", dict(sorted(hist.items())))
# blanks / row len <8
short = [i for i,r in enumerate(allrows) if len(r) < 8]
print("COVERAGE rows with <8 cols:", len(short), short[:10])

full_ok = sum(1 for r in cov if r[4].strip()=="[已证]")
atlas_ok = sum(1 for r in cov if ne(r[0]) in atlas and r[4].strip()=="[已证]")
out_ok = sum(1 for r in cov if ne(r[0]) not in atlas and r[4].strip()=="[已证]")
print("BEFORE full [已证]:", full_ok)
print("BEFORE atlas-in [已证]:", atlas_ok)
print("BEFORE atlas-out [已证]:", out_ok)
s22_proved = sum(1 for r in cov if ne(r[0]) in atlas and r[1].strip()=="S22" and r[4].strip()=="[已证]")
print("BEFORE S22 atlas-in proved:", s22_proved)
# strict by bracketed literal
def strict_count(rows):
    return sum(1 for r in rows if r[4].strip()=="[已证]" and "[未证]" not in r[3])
print("BEFORE S22 strict (bracket literal):", strict_count([r for r in cov if ne(r[0]) in atlas and r[1].strip()=="S22"]))
print("BEFORE TOTAL strict (bracket literal, atlas-in):", strict_count([r for r in cov if ne(r[0]) in atlas]))

# verdict.tsv
with open(VERD, encoding="utf-8-sig", newline="") as f:
    vd = [r for r in csv.reader(f, delimiter="\t") if r and any(c.strip() for c in r)]
vheader = vd[0]; vrows = vd[1:]
print("VERDICT header:", vheader)
print("VERDICT data rows:", len(vrows))
verdicts = collections.Counter(r[2].strip() for r in vrows)
print("VERDICT verdict histogram:", dict(verdicts))
ventries = [ne(r[0]) for r in vrows]
print("VERDICT entries:", ventries)

# delta.tsv
with open(DELTA, encoding="utf-8-sig", newline="") as f:
    dd = [r for r in csv.reader(f, delimiter="\t") if r and any(c.strip() for c in r)]
dheader = dd[0]; drows = dd[1:]
print("DELTA header:", dheader)
print("DELTA data rows:", len(drows))
dentries = [ne(r[0]) for r in drows]
print("DELTA entries:", dentries)

# coverage entries dict (normalized)
cov_by_entry = collections.defaultdict(list)
for idx, r in enumerate(cov):
    cov_by_entry[ne(r[0])].append((idx, r))
centries = set(cov_by_entry.keys())

# intersection
vset = set(ventries); dset = set(dentries)
inter = vset & dset & centries
print("INTERSECTION size (verdict ∩ delta ∩ coverage):", len(inter))
print("INTERSECTION entries:", sorted(inter))
print("EXPECT size:", len(set(EXPECT)))
print("INTERSECTION == EXPECTED 11:", inter == set(EXPECT))
print("Any verdict entry duplicated in coverage:", {e:len(cov_by_entry[e]) for e in sorted(inter)})
print("Verdict entries missing in delta:", sorted(vset - dset))
print("Delta entries missing in verdict:", sorted(dset - vset))

# per-entry detail
print("\n--- per-entry detail ---")
for e in EXPECT:
    in_atlas = e in atlas
    cv = cov_by_entry.get(e, [])
    if len(cv)==1:
        i,r = cv[0]
        print(f"{e}: atlas={in_atlas} covrow(dataidx)={i} subsystem={r[1]} grade={r[4]} ev={r[5]}")
        print(f"    sem-head={r[3][:60]!r}")
    else:
        print(f"{e}: atlas={in_atlas} cov occurrences={len(cv)}")

# delta semantics check for bracket literal [未证]
print("\n--- delta col4 bracket-literal [未证] check ---")
for r in drows:
    print(ne(r[0]), "[未证]" in r[3], "已证" in r[4])
