# -*- coding: utf-8 -*-
"""M67 read-only analysis: preconditions + intersection + atlas + strict prep."""
import csv, os, sys, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")

AUDIT = os.path.join(ROOT, "NAMED_PUSH_AUDIT7", "verdict.tsv")
D20 = os.path.join(ROOT, "NAMED_PUSH_S20_B2", "delta.tsv")
D06 = os.path.join(ROOT, "NAMED_PUSH_S06_B3", "delta.tsv")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")

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

# ---------- audit ----------
aud = read_tsv(AUDIT)
hdr = aud[0]
assert hdr[2] == "verdict", hdr
audit_rows = [r for r in aud[1:] if len(r) >= 8 and r[0].strip()]
audit_pass = {}
for r in audit_rows:
    if r[2].strip() == "PASS":
        audit_pass[ne(r[0])] = r
print("AUDIT rows=%d PASS=%d" % (len(audit_rows), len(audit_pass)))
print("  PASS entries:", sorted(audit_pass.keys()))
print("  non-PASS:", [ (r[0],r[2]) for r in audit_rows if r[2].strip()!="PASS" ])

# ---------- deltas ----------
d20 = [r for r in read_tsv(D20)[1:] if len(r) >= 6 and r[0].strip()]
d06 = [r for r in read_tsv(D06)[1:] if len(r) >= 6 and r[0].strip()]
e20 = {ne(r[0]): r for r in d20}
e06 = {ne(r[0]): r for r in d06}
print("S20_B2 delta rows=%d entries=%s" % (len(d20), sorted(e20.keys())))
print("S06_B3 delta rows=%d entries=%s" % (len(d06), sorted(e06.keys())))

# ---------- intersection ----------
delta_all = dict(e20); delta_all.update(e06)
pass_set = set(audit_pass.keys())
delta_set = set(delta_all.keys())
inter = pass_set & delta_set
print("\n=== INTERSECTION ===")
print("PASS count=%d delta count=%d intersection=%d" % (len(pass_set), len(delta_set), len(inter)))
print("PASS - delta =", sorted(pass_set - delta_set))
print("delta - PASS =", sorted(delta_set - pass_set))
i20 = sorted(inter & set(e20.keys()))
i06 = sorted(inter & set(e06.keys()))
print("S20 inter=%d %s" % (len(i20), i20))
print("S06 inter=%d %s" % (len(i06), i06))
print("INTER OK (13, S20 8 + S06 5):", len(inter) == 13 and len(i20)==8 and len(i06)==5)

# ---------- atlas ----------
atlas = set()
with open(ATLAS, encoding="utf-8-sig") as f:
    for i, line in enumerate(f):
        if i == 0:
            continue
        p = line.rstrip("\r\n").split("\t")
        if p and p[0].strip():
            atlas.add(ne(p[0]))
print("\nATLAS entries=%d" % len(atlas))

# ---------- coverage ----------
cov = read_tsv(COV)
data = [r for r in cov[1:] if len(r) >= 8]
print("\n=== COVERAGE PRECONDITIONS ===")
print("data rows=%d (expect 18498)" % len(data))
full_proved = [r for r in data if r[4].strip() == "[已证]"]
in_proved = [r for r in full_proved if ne(r[0]) in atlas]
out_proved = [r for r in full_proved if ne(r[0]) not in atlas]
print("full [已证]=%d (expect 1556)" % len(full_proved))
print("atlas-in [已证]=%d (expect 1550)" % len(in_proved))
print("atlas-out [已证]=%d (expect 6)" % len(out_proved))

# grade histogram & conflict
grades = collections.Counter(r[4].strip() for r in data)
print("grade histogram:", dict(grades))
print("conflict==1:", sum(1 for r in data if r[7].strip()=="1"))

# per-subsystem proved (atlas in)
by = collections.Counter()
for r in in_proved:
    by[r[1].strip()] += 1
print("S20 atlas-in proved=%d (expect 53)" % by["S20"])
print("S06 atlas-in proved=%d (expect 130)" % by["S06"])

# ---------- 13 rows current state ----------
cov_by = {}
for r in data:
    cov_by.setdefault(ne(r[0]), []).append(r)
print("\n=== 13 ROWS CURRENT STATE ===")
all_ok = True
for e in sorted(inter):
    rows = cov_by.get(e, [])
    atl = e in atlas
    src = "S20" if e in e20 else "S06"
    d = delta_all[e]
    sem = d[3]
    has_unver = "[未证]" in sem
    has_4 = "④" in sem
    if len(rows) != 1:
        all_ok = False
    g = rows[0][4].strip() if rows else "MISSING"
    print("%s %s atlas=%s cov_hits=%d grade=%s delta_sem_has_[未证]=%s delta_sem_has④=%s" %
          (e, src, atl, len(rows), g, has_unver, has_4))
print("all 13 have unique coverage row:", all_ok)
print("all 13 in atlas:", all(e in atlas for e in inter))
print("atlas-out among 13:", [e for e in inter if e not in atlas])

# 0062FE90 specifics
f = delta_all.get(ne("0062FE90"))
if f:
    sem = f[3]
    print("\n=== 0062FE90 delta col4 occurrences ===")
    print("  007E9D84 count:", sem.count("007E9D84"))
    print("  0x7E9D84 count:", sem.count("0x7E9D84"))
    print("  007E9D64 count:", sem.count("007E9D64"))
    print("  004E9F00 count:", sem.count("004E9F00"))

# ---------- strict prep: check all 13 delta semantics for literal [未证] ----------
print("\n=== STRICT PREP ===")
unver_rows = [e for e in inter if "[未证]" in delta_all[e][3]]
print("13 rows with literal [未证] in delta col4:", unver_rows)
print("=> strict increment should equal proved increment for these 13 (all clean)" if not unver_rows else "=> CHECK")
