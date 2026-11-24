#!/usr/bin/env python3
# T1: coverage(S01) ∩ function_atlas, with case normalization (§990 trap).
import csv, os, re, sys

ROOT = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATL = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
OUT = os.path.join(ROOT, r"lead\next_re_20261117_r14\S01-K2\TARGETS.tsv")
REP = os.path.join(ROOT, r"lead\next_re_20261117_r14\S01-K2\EVIDENCE\t1_report.txt")


def load(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


cov = load(COV)
atl = load(ATL)

# --- case check (§990): atlas entries may be lower-case hex, coverage upper-case ---
atl_entries_raw = [r["entry"] for r in atl]
atl_lower = sum(1 for e in atl_entries_raw if any(c.isalpha() and c.islower() for c in e))
cov_entries_raw = [r["entry"] for r in cov]
cov_lower = sum(1 for e in cov_entries_raw if any(c.isalpha() and c.islower() for c in e))

s01 = [r for r in cov if r["subsystem"] == "S01"]
s01_set_raw = {r["entry"] for r in s01}
atl_set_raw = set(atl_entries_raw)
inter_raw = s01_set_raw & atl_set_raw  # naive, no normalization

# normalized (upper-case)
atl_set_u = {e.upper() for e in atl_entries_raw}
s01_by_u = {r["entry"].upper(): r for r in s01}
inter_u = set(s01_by_u) & atl_set_u

lines = []
def p(s=""):
    lines.append(str(s))

p("=== T1 TARGETS report ===")
p(f"coverage data rows      : {len(cov)}")
p(f"atlas data rows         : {len(atl)}")
p(f"coverage entries with any lower hex letter : {cov_lower}")
p(f"atlas entries with any lower hex letter    : {atl_lower}")
p(f"S01 coverage rows (all, incl outside atlas): {len(s01)}")
p(f"naive intersection (no case normalize)      : {len(inter_raw)}   <-- §990 trap")
p(f"normalized intersection (upper)             : {len(inter_u)}   <-- TARGETS")

# named / proved per R14-R14 (S caliber) + L caliber
def is_named_L(name):
    n = (name or "").strip()
    return bool(n) and not n.startswith("sub_")

def is_named_S(name):
    n = (name or "").strip()
    if not is_named_L(name):
        return False
    # exclude Class::sub_XXXXXXXX self-made placeholders
    if re.search(r"::sub_[0-9A-Fa-f]{8}$", n):
        return False
    return True

named_L = sum(1 for e in inter_u if is_named_L(s01_by_u[e]["name"]))
named_S = sum(1 for e in inter_u if is_named_S(s01_by_u[e]["name"]))
proved = sum(1 for e in inter_u if s01_by_u[e]["grade"] == "[已证]")
static = sum(1 for e in inter_u if s01_by_u[e]["grade"] == "[静态推断]")
unprov = sum(1 for e in inter_u if s01_by_u[e]["grade"] == "[未证]")
n = len(inter_u)
p(f"atlas_n (denominator)   : {n}")
p(f"named_n (L)             : {named_L}  ({100*named_L/n:.2f}%)" if n else "")
p(f"named_n (S)             : {named_S}  ({100*named_S/n:.2f}%)" if n else "")
p(f"proved                  : {proved}  ({100*proved/n:.2f}%)" if n else "")
p(f"static / unproved       : {static} / {unprov}")
p(f"50% gate = 27/53 -> need 27; shortfall = {max(0,27-proved)}" if n==53 else f"50% gate ceil(0.5*N)={int(n*0.5+0.999)}; shortfall={max(0,int(n*0.5+0.999)-proved)}")
p(f"90% named(S) gate = ceil(0.9*N)={int(n*0.9+0.999)}; shortfall={max(0,int(n*0.9+0.999)-named_S)}")
p()
p("grade breakdown of named_S rows:")
for e in sorted(inter_u):
    r = s01_by_u[e]
    if is_named_S(r["name"]):
        p(f"  {e}  {r['grade']:<8} {r['name']}")

# ---- emit TARGETS.tsv (normalized upper hex, sorted) ----
hdr = ["entry", "subsystem", "name", "one_line_semantics", "grade", "evidence_path", "conflict", "in_atlas", "atlas_size", "named_L", "named_S"]
atl_by_u = {r["entry"].upper(): r for r in atl}
with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(hdr)
    for e in sorted(inter_u):
        r = s01_by_u[e]
        a = atl_by_u[e]
        w.writerow([e, r["subsystem"], r["name"], r["one_line_semantics"], r["grade"],
                    r["evidence_path"], r["conflict"], "Y", a["size"],
                    "1" if is_named_L(r["name"]) else "0", "1" if is_named_S(r["name"]) else "0"])

with open(REP, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines))
print("\nTARGETS.tsv ->", OUT, f"({len(inter_u)} rows)")
