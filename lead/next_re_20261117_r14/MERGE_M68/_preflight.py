# -*- coding: utf-8 -*-
"""M68-MERGE read-only preflight: intersection, preconditions, before/after stats."""
import csv, os, sys, math, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
VERDICT = os.path.join(ROOT, "NAMED_PUSH_AUDIT8", "verdict.tsv")
DELTA = os.path.join(ROOT, "NAMED_PUSH_S12_B1", "delta.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
CARD_ENTRIES = ['00442230', '00447210', '00447F10', '0044E8F0']

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e

def read_tsv(path, skip_header=True):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    return rows[1:] if skip_header else rows

# --- atlas ---
atlas = set()
with open(ATLAS, encoding="utf-8-sig") as f:
    for i, line in enumerate(f):
        if i == 0:
            continue
        p = line.rstrip("\r\n").split("\t")
        if p and p[0].strip():
            atlas.add(ne(p[0]))

# --- verdict.tsv ---
verdict_rows = read_tsv(VERDICT)
verdict_entries = [ne(r[0]) for r in verdict_rows if r and r[0].strip()]
verdict_pass = [r for r in verdict_rows if len(r) >= 8 and r[2].strip() == "PASS"]

# --- delta.tsv ---
delta_rows = read_tsv(DELTA)
delta_by_entry = {ne(r[0]): r for r in delta_rows if r and r[0].strip()}
delta_entries = [ne(r[0]) for r in delta_rows if r and r[0].strip()]

# --- coverage.tsv ---
cov_rows = read_tsv(COV)
cov_rows = [r for r in cov_rows if len(r) >= 8]
cov_entry_counts = collections.Counter(ne(r[0]) for r in cov_rows)

card_norm = [ne(e) for e in CARD_ENTRIES]

print("=== PRECONDITIONS ===")
print("verdict.tsv data rows:", len(verdict_rows), " cols:", len(verdict_rows[0]))
print("verdict verdicts:", [r[2].strip() for r in verdict_rows], "PASS count:", len(verdict_pass))
print("delta.tsv data rows:", len(delta_rows), " cols:", len(delta_rows[0]))
print("coverage data rows:", len(cov_rows))
print("card entries (norm):", card_norm)
print()
print("=== INTERSECTION ===")
print("verdict entries:", sorted(verdict_entries))
print("delta entries  :", sorted(delta_entries))
print("card entries   :", sorted(card_norm))
inter = set(verdict_entries) & set(delta_entries) & set(card_norm)
print("3-way intersection (verdict∩delta∩card):", sorted(inter), "count=", len(inter))
# 4-way with coverage presence
inter4 = inter & set(cov_entry_counts)
print("4-way intersection (+present in coverage):", sorted(inter4), "count=", len(inter4))
# exact row matches in coverage (each entry exactly once?)
for e in sorted(card_norm):
    print("  entry", e, "coverage occurrences:", cov_entry_counts.get(e, 0),
          "in verdict:", e in set(verdict_entries), "in delta:", e in set(delta_entries))
# duplicates in coverage overall
dups = {e:c for e,c in cov_entry_counts.items() if c > 1}
print("coverage duplicate normalized entries:", len(dups))
print()

# --- current grade of 4 rows ---
print("=== 4 ROWS CURRENT GRADE ===")
for e in sorted(card_norm):
    for r in cov_rows:
        if ne(r[0]) == e:
            print(" ", e, "grade=", repr(r[4].strip()), "sub=", r[1].strip(), "name=", r[2].strip())
print()

# --- atlas membership of 4 rows ---
print("=== ATLAS MEMBERSHIP ===")
for e in sorted(card_norm):
    print(" ", e, "in atlas:", e in atlas, "(raw lowercase present:",
          e.lower() in atlas, ")")
print()

# --- stats computation function ---
def stats(rows, label):
    total_proved = 0
    atlas_proved = 0
    outside_proved = 0
    atlas_tot = 0
    per_sub = collections.defaultdict(lambda: collections.Counter())
    for r in rows:
        e = ne(r[0])
        s = r[1].strip()
        sem = r[3]
        grade = r[4].strip()
        is_atlas = e in atlas
        if is_atlas:
            atlas_tot += 1
            per_sub[s]["atlas_n"] += 1
        if grade == "[已证]":
            total_proved += 1
            if is_atlas:
                atlas_proved += 1
                per_sub[s]["proved_n"] += 1
                if "[未证]" not in sem:
                    per_sub[s]["proved_strict"] += 1
            else:
                outside_proved += 1
    print(f"--- {label} ---")
    print("  data rows:", len(rows))
    print("  atlas rows:", atlas_tot, " outside:", len(rows)-atlas_tot)
    print("  total [已证]:", total_proved, " atlas内:", atlas_proved, " atlas外:", outside_proved)
    c = per_sub["S12"]
    a = c["atlas_n"]
    tp = math.ceil(0.5 * a)
    tn = math.ceil(0.9 * a)
    print("  S12: atlas_n=%d proved=%d strict=%d thu_p=%d thu_n=%d nominal_ok=%s strict_ok=%s" % (
        a, c["proved_n"], c["proved_strict"], tp, tn,
        c["proved_n"]>=tp, c["proved_strict"]>=tp))
    return dict(total=total_proved, atlas=atlas_proved, outside=outside_proved,
                s12_proved=c["proved_n"], s12_strict=c["proved_strict"],
                per_sub=per_sub)

before = stats(cov_rows, "BEFORE")

# --- simulate AFTER: modify 4 rows (cols 4,5,6) ---
after_rows = [list(r) for r in cov_rows]
modified = []
for r in after_rows:
    e = ne(r[0])
    if e in inter4:
        d = delta_by_entry[e]
        r[3] = d[3]                         # col4 = delta col4 verbatim
        r[4] = "[已证]"                      # col5
        r[5] = "NAMED_PUSH_AUDIT8/VERDICT.md"  # col6
        modified.append(e)
print("modified entries:", sorted(modified), "count=", len(modified))
after = stats(after_rows, "AFTER (simulated)")

# --- full 达标 evaluation (nominal + strict) for BEFORE and AFTER ---
def dod_eval(per_sub, label):
    nominal, strict = [], []
    for s in sorted(k for k in per_sub if __import__('re').match(r"^S\d\d$", k)):
        a = per_sub[s]["atlas_n"]
        if a == 0:
            continue
        tn = math.ceil(0.9*a); tp = math.ceil(0.5*a)
        # named_S14 needed: count named using same rules
        # (not recomputed here; use PANEL values as baseline - named cols unaffected by this merge)
        if per_sub[s]["proved_n"] >= tp:
            nominal.append(s)
        if per_sub[s]["proved_strict"] >= tp:
            strict.append(s)
    print(f"  {label} proved-threshold-met subsystems: {nominal}")
    print(f"  {label} strict-proved-threshold-met subsystems: {strict}")

# Also compute named_S14 to determine full DoD — need coverage rows with names
def full_dod(rows, label):
    RE_SLOT = __import__('re').compile(r"::v?slot\d+$")
    RE_CSUB = __import__('re').compile(r"::sub_[0-9A-Fa-f]+$")
    d = collections.defaultdict(collections.Counter)
    for r in rows:
        e = ne(r[0]); s = r[1].strip()
        if e not in atlas:
            continue
        name = r[2].strip(); sem = r[3]; grade = r[4].strip()
        d[s]["atlas_n"] += 1
        if name and not name.startswith("sub_"):
            if not RE_CSUB.search(name):
                d[s]["named_S14"] += 1
        if grade == "[已证]":
            d[s]["proved_n"] += 1
            if "[未证]" not in sem:
                d[s]["proved_strict"] += 1
    nom, st = [], []
    for s in sorted(k for k in d if __import__('re').match(r"^S\d\d$", k)):
        a=d[s]["atlas_n"]; tn=math.ceil(0.9*a); tp=math.ceil(0.5*a)
        ok_n = d[s]["named_S14"] >= tn
        if ok_n and d[s]["proved_n"]>=tp: nom.append(s)
        if ok_n and d[s]["proved_strict"]>=tp: st.append(s)
    print(f"  {label} FULL DoD nominal: {nom}")
    print(f"  {label} FULL DoD strict : {st}")
    return nom, st

print()
print("=== FULL DoD (named_S14 + proved) ===")
bn, bs = full_dod(cov_rows, "BEFORE")
an, as_ = full_dod(after_rows, "AFTER")
print("  NOMINAL flip:", bn != an, " STRICT flip:", bs != as_)

# --- new semantics contain literal [未证]? ---
print()
print("=== NEW SEMANTICS [未证] CHECK ===")
for e in sorted(inter4):
    sem = delta_by_entry[e][3]
    print(" ", e, "contains literal [未证]:", "[未证]" in sem, " | contains 未证:", "未证" in sem)

# --- new proved_pct ---
print()
print("=== S12 / TOTAL PERCENT AFTER ===")
c = after["per_sub"]["S12"]
print("  S12 proved_pct = %d/279 = %.4f -> %.2f" % (c["proved_n"], 100*c["proved_n"]/279, round(100*c["proved_n"]/279,2)))
print("  S12 strict_pct = %d/279 = %.4f -> %.2f" % (c["proved_strict"], 100*c["proved_strict"]/279, round(100*c["proved_strict"]/279,2)))
print("  TOTAL atlas proved =", after["atlas"], "pct = %.4f -> %.2f" % (100*after["atlas"]/12916, round(100*after["atlas"]/12916,2)))
ts = sum(v["proved_strict"] for k,v in after["per_sub"].items() if __import__('re').match(r"^S\d\d$", k))
print("  TOTAL strict =", ts, "pct = %.4f -> %.2f" % (100*ts/12916, round(100*ts/12916,2)))
