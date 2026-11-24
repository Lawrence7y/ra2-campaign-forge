# -*- coding: utf-8 -*-
"""S02-K2 / T1: coverage(S02) cap function_atlas -> TARGETS.tsv ; recompute named(L/S)/proved by R14-R14."""
import csv, os, re, sys

ROOT = r"D:\Project\ra2-campaign-forge"
COV  = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATL  = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
CARD = os.path.join(ROOT, r"lead\next_re_20261117_r14\S02-K2")
OUT  = os.path.join(CARD, "TARGETS.tsv")
EVID = os.path.join(CARD, "EVIDENCE", "T1_counts.txt")

def norm(e):
    e = e.strip().upper()
    if e.lower().startswith("0X"):
        e = e[2:]
    return e.zfill(8)

# atlas entries (data lines)
atl = {}
with open(ATL, encoding="utf-8", errors="replace") as f:
    hdr = f.readline().rstrip("\n").split("\t")
    for ln in f:
        if not ln.strip():
            continue
        p = ln.rstrip("\n").split("\t")
        if len(p) < 2:
            continue
        atl[norm(p[0])] = p[1]

# coverage rows subsystem S02
cov = {}
s02_all = 0
with open(COV, encoding="utf-8", errors="replace") as f:
    hdr = f.readline().rstrip("\n").split("\t")
    for ln in f:
        if not ln.strip():
            continue
        p = ln.rstrip("\n").split("\t")
        if len(p) < 5:
            continue
        entry = norm(p[0]); subsys = p[1]; name = p[2]; sem = p[3]; grade = p[4]
        if subsys != "S02":
            continue
        s02_all += 1
        cov[entry] = dict(subsystem=subsys, name=name, sem=sem, grade=grade,
                          ev=p[5] if len(p) > 5 else "", raw=p)

# intersection = coverage S02 whose entry is in atlas
inter = sorted(e for e in cov if e in atl)

# Named calibers
def named_L(name):
    return bool(name) and not name.startswith("sub_")
def named_S(name):
    # R14-R14 S: L caliber minus Class::sub_XXXX placeholder forms
    return named_L(name) and not re.match(r"^.*::sub_[0-9A-Fa-f]{8}$", name)

named_L_n = sum(1 for e in inter if named_L(cov[e]["name"]))
named_S_n = sum(1 for e in inter if named_S(cov[e]["name"]))
class_sub_n = named_L_n - named_S_n
proved_n = sum(1 for e in inter if cov[e]["grade"] == "[已证]")

# all S02 (incl outside atlas) for cross-check
s02_inter = len(inter)
all_named_L = sum(1 for e in cov if named_L(cov[e]["name"]))
all_named_S = sum(1 for e in cov if named_S(cov[e]["name"]))
all_proved = sum(1 for e in cov if cov[e]["grade"] == "[已证]")

N = len(inter)
thresh50 = (N + 1)//2  # ceil(N/2) minimum integer count to reach >=50%
need_proved = max(0, thresh50 - proved_n)

lines = []
lines.append("S02-K2 T1 counts (recomputed from disk 2026-11-17)")
cov_total = sum(1 for _ in open(COV, encoding="utf-8", errors="replace")) - 1
lines.append("coverage.tsv data rows (all): %d" % cov_total)
lines.append("coverage S02 rows (all, incl outside atlas): %d" % s02_all)
lines.append("function_atlas data rows: %d" % len(atl))
lines.append("TARGETS = coverage(S02) cap atlas: %d" % N)
lines.append("named_L(in atlas): %d (%.2f%%)" % (named_L_n, 100.0*named_L_n/N))
lines.append("named_S(in atlas): %d (%.2f%%)  [R14-R14 DoD caliber]" % (named_S_n, 100.0*named_S_n/N))
lines.append("Class::sub_ placeholders within named_L: %d" % class_sub_n)
lines.append("proved=[已证](in atlas): %d (%.2f%%)" % (proved_n, 100.0*proved_n/N))
lines.append("50%% threshold count = ceil(%d/2) = %d ; need %d more proved" % (N, thresh50, need_proved))
lines.append("all S02 proved (incl outside atlas): %d ; named_L %d named_S %d" % (all_proved, all_named_L, all_named_S))
lines.append("")
lines.append("PANEL.md S02 row: atlas_n=327 named_n=37 named_pct_L=11.31 proved_n=31 proved_pct=9.48")
lines.append("Task card / HANDOFF: S02 atlas 327 named 37 (11.31%) [已证] 30 (9.17%)")
lines.append("DISCREPANCY: PANEL proved_n=31 (9.48%) vs task card 30 (9.17%). Use on-disk recomputation above (纪律 9).")

msg = "\n".join(lines)
with open(EVID, "w", encoding="utf-8") as f:
    f.write(msg + "\n")

# write TARGETS.tsv : entry + atlas fields + coverage fields
with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["entry","atlas_size","atlas_n_instr","atlas_n_callers","cov_subsystem","cov_name","cov_grade","named_L","named_S","sem","evidence_path"])
    for e in inter:
        a = atl[e].split("\t")
        c = cov[e]
        w.writerow([e, a[1] if len(a)>1 else "", a[2] if len(a)>2 else "", a[3] if len(a)>3 else "",
                    c["subsystem"], c["name"], c["grade"], "1" if named_L(c["name"]) else "0",
                    "1" if named_S(c["name"]) else "0", c["sem"], c["ev"]])

print(msg)
print("\nWROTE", OUT, "rows", N)
print("WROTE", EVID)
