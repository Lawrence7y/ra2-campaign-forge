# -*- coding: utf-8 -*-
"""M66 before-state verification + after-state simulation.
Uses the exact authoritative logic of strict_panel.py (ne(), atlas set, proved/strict definitions).
"""
import csv, os, re, collections, math, sys
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
RE_SLOT = re.compile(r"::v?slot\d+$")
RE_CSUB = re.compile(r"::sub_[0-9A-Fa-f]+$")

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e

def load_atlas():
    atlas = set()
    with open(ATLAS, encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            p = line.rstrip("\r\n").split("\t")
            if p and p[0].strip():
                atlas.add(ne(p[0]))
    return atlas

def load_cov():
    with open(COV, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    return rows[0], rows[1:]

def load_delta(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    return rows[0], {r[0].strip(): r for r in rows[1:] if r and r[0].strip()}

def panel_stats(cov, atlas):
    """Replicates strict_panel.py exactly, plus full/atlas-out [已证] counts."""
    d = collections.defaultdict(collections.Counter)
    full_proved = 0
    atlas_out_proved = 0
    atlas_in_count = 0
    atlas_out_count = 0
    colcounts = collections.Counter()
    for r in cov:
        colcounts[len(r)] += 1
        if len(r) < 8:
            continue
        e = ne(r[0])
        s = r[1].strip()
        grade = r[4].strip()
        if grade == "[已证]":
            full_proved += 1
        if e not in atlas:
            d[s]["cov_nonatlas"] += 1
            atlas_out_count += 1
            if grade == "[已证]":
                atlas_out_proved += 1
            continue
        atlas_in_count += 1
        name = r[2].strip()
        sem = r[3]
        d[s]["atlas_n"] += 1
        if name and not name.startswith("sub_"):
            d[s]["named_L"] += 1
            if not RE_CSUB.search(name):
                d[s]["named_S14"] += 1
                if not RE_SLOT.search(name):
                    d[s]["named_strict"] += 1
        if grade == "[已证]":
            d[s]["proved_n"] += 1
            if "[未证]" not in sem:
                d[s]["proved_strict_n"] += 1
    return d, dict(full_proved=full_proved, atlas_out_proved=atlas_out_proved,
                   atlas_in_count=atlas_in_count, atlas_out_count=atlas_out_count,
                   colcounts=dict(colcounts))

def fmt_stat(d, s):
    c = d[s]
    a = c["atlas_n"]
    tp = math.ceil(0.5 * a)
    tn = math.ceil(0.9 * a)
    return dict(S=s, atlas_n=a, named_S14=c["named_S14"], named_strict=c["named_strict"],
                proved_n=c["proved_n"], proved_strict_n=c["proved_strict_n"],
                thu_named=tn, thu_proved=tp,
                dod_nominal=(c["named_S14"]>=tn and c["proved_n"]>=tp),
                dod_strict=(c["named_S14"]>=tn and c["proved_strict_n"]>=tp))

atlas = load_atlas()
hdr, cov = load_cov()
print("coverage header:", hdr)
print("atlas entries (normalized unique):", len(atlas))

d0, extra0 = panel_stats(cov, atlas)
print("\n=== BEFORE STATE ===")
print("data rows:", len(cov))
print("column counts:", extra0["colcounts"])
print("full [已证]:", extra0["full_proved"])
print("atlas-in count:", extra0["atlas_in_count"], "atlas-out count:", extra0["atlas_out_count"])
print("atlas-in [已证] (sum proved_n):", sum(d0[s]["proved_n"] for s in d0))
print("atlas-out [已证]:", extra0["atlas_out_proved"])
for s in ("S22", "S06", "S20"):
    print(f"  {s}: proved_n={d0[s]['proved_n']}  proved_strict_n={d0[s]['proved_strict_n']}")

# Load deltas
_, dd22 = load_delta(os.path.join(ROOT, "NAMED_PUSH_S22_B2", "delta.tsv"))
_, dd06 = load_delta(os.path.join(ROOT, "NAMED_PUSH_S06_B1", "delta.tsv"))
_, dd20 = load_delta(os.path.join(ROOT, "NAMED_PUSH_S20_B1", "delta.tsv"))

# PASS sets
def pass_set(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f, delimiter="\t"))[1:]
    return set(r[0].strip() for r in rows if r[2].strip()=="PASS")

p6 = pass_set(os.path.join(ROOT, "NAMED_PUSH_AUDIT6", "verdict.tsv"))
p5rows = None
with open(os.path.join(ROOT, "NAMED_PUSH_AUDIT5", "verdict.tsv"), encoding="utf-8-sig", newline="") as f:
    p5rows = list(csv.reader(f, delimiter="\t"))[1:]
p5_06 = set(r[0].strip() for r in p5rows if r[2].strip()=="PASS" and r[1].strip()=="S06")
p5_20 = set(r[0].strip() for r in p5rows if r[2].strip()=="PASS" and r[1].strip()=="S20")

groups = [
    ("A/S22", p6, dd22, set(dd22.keys()), "NAMED_PUSH_AUDIT6/VERDICT.md"),
    ("B/S06", p5_06, dd06, set(dd06.keys()), "NAMED_PUSH_AUDIT5/VERDICT.md"),
    ("B/S20", p5_20, dd20, set(dd20.keys()), "NAMED_PUSH_AUDIT5/VERDICT.md"),
]

# Build index of coverage by normalized entry
cov_idx = {}
for i, r in enumerate(cov):
    cov_idx.setdefault(ne(r[0]), []).append(i)

print("\n=== 29 ROWS PRECHECK ===")
all_targets = []  # (group, entry, row_idx, delta_row, evidence_path)
problems = []
for gname, pass_set_, dd, de, evid in groups:
    inter = sorted(pass_set_ & de)
    print(f"\n-- {gname}: {len(inter)} rows --")
    for e in inter:
        dr = dd[e]
        ne_e = ne(e)
        idxs = cov_idx.get(ne_e, [])
        in_atlas = ne_e in atlas
        sem_has_unproven = "[未证]" in dr[3]
        if len(idxs) != 1:
            problems.append(f"{gname} {e}: coverage match count={len(idxs)}")
        row_idx = idxs[0] if len(idxs)==1 else None
        cur = cov[row_idx] if row_idx is not None else None
        print(f"  {e} atlas={in_atlas} cov_match={len(idxs)} cur_grade={cur[4] if cur else 'NA'} "
              f"sem_has_[未证]={sem_has_unproven} delta_grade={dr[4]}")
        if cur is not None and cur[4].strip() == "[已证]":
            problems.append(f"{gname} {e}: already [已证] in coverage (would not be a NEW proved)")
        if sem_has_unproven:
            problems.append(f"{gname} {e}: delta semantics contains literal [未证]")
        all_targets.append((gname, e, row_idx, dr, evid, in_atlas))

print("\n=== PROBLEMS ===")
if problems:
    for p in problems:
        print("  !!", p)
else:
    print("  none")

print("\n=== atlas-out rows (A 口径不计) ===")
atlas_out = [t for t in all_targets if not t[5]]
if atlas_out:
    for t in atlas_out:
        print("  ", t[0], t[1])
else:
    print("  none — all 29 rows are atlas-in")

# Simulate after-state
cov2 = [r[:] for r in cov]
for gname, e, row_idx, dr, evid, in_atlas in all_targets:
    if row_idx is None:
        continue
    cov2[row_idx][3] = dr[3]      # col4 semantics <- delta col4 original
    cov2[row_idx][4] = "[已证]"   # col5 grade
    cov2[row_idx][5] = evid       # col6 evidence_path
    # cols 1,2,3,7,8 untouched

d1, extra1 = panel_stats(cov2, atlas)
print("\n=== AFTER STATE (simulated) ===")
print("data rows:", len(cov2))
print("full [已证]:", extra1["full_proved"])
print("atlas-in [已证]:", sum(d1[s]["proved_n"] for s in d1))
print("atlas-out [已证]:", extra1["atlas_out_proved"])
for s in ("S22", "S06", "S20"):
    print(f"  {s}: proved {d0[s]['proved_n']}->{d1[s]['proved_n']}  strict {d0[s]['proved_strict_n']}->{d1[s]['proved_strict_n']}")

# 达标 check: compare before vs after for all subsystems
print("\n=== 达标 FLIP CHECK ===")
flips = []
nom_before = sorted(s for s in d0 if re.match(r"^S\d\d$", s) and fmt_stat(d0,s)["dod_nominal"])
str_before = sorted(s for s in d0 if re.match(r"^S\d\d$", s) and fmt_stat(d0,s)["dod_strict"])
nom_after = sorted(s for s in d1 if re.match(r"^S\d\d$", s) and fmt_stat(d1,s)["dod_nominal"])
str_after = sorted(s for s in d1 if re.match(r"^S\d\d$", s) and fmt_stat(d1,s)["dod_strict"])
print("nominal before:", nom_before)
print("nominal after :", nom_after)
print("strict  before:", str_before)
print("strict  after :", str_after)
if set(nom_before)!=set(nom_after) or set(str_before)!=set(str_after):
    flips.append("DOD FLIP DETECTED")
    print("  !! DOD FLIP DETECTED")
else:
    print("  no DOD flip")

# dumps all strict rows after for reference
print("\n=== AFTER strict rows (all S) ===")
for s in sorted(k for k in d1 if re.match(r"^S\d\d$", k)):
    st = fmt_stat(d1, s)
    pct = round(100.0*st["proved_n"]/st["atlas_n"],2) if st["atlas_n"] else 0
    spct = round(100.0*st["proved_strict_n"]/st["atlas_n"],2) if st["atlas_n"] else 0
    print(f"  {s}: atlas={st['atlas_n']} proved={st['proved_n']}({pct}) strict={st['proved_strict_n']}({spct}) thrP={st['thu_proved']} nom={st['dod_nominal']} strictOK={st['dod_strict']}")

# TOTAL strict after
tot_proved = sum(d1[s]["proved_n"] for s in d1)
tot_strict = sum(d1[s]["proved_strict_n"] for s in d1)
tot_atlas = sum(d1[s]["atlas_n"] for s in d1)
print(f"\nTOTAL after: atlas={tot_atlas} proved={tot_proved} ({round(100.0*tot_proved/tot_atlas,2)}) strict={tot_strict} ({round(100.0*tot_strict/tot_atlas,2)})")
print(f"TOTAL before: proved={sum(d0[s]['proved_n'] for s in d0)} strict={sum(d0[s]['proved_strict_n'] for s in d0)}")
