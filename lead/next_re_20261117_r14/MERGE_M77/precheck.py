# -*- coding: utf-8 -*-
"""M77 precheck: baseline counts, target rows, atlas membership, strict caliber, DoD flip."""
import csv, os, re, sys, math, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
VERDICT = os.path.join(ROOT, "NAMED_PUSH_AUDIT20", "verdict.tsv")
DELTA = os.path.join(ROOT, "NAMED_PUSH_S07S11_B2", "delta.tsv")

TARGETS = ["006DBE00", "0069EE30", "00719E30", "0075C7F0"]


def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e


def pct(n, d):
    return "%.2f" % (100.0 * n / d)


ok = 0
fail = 0
def check(cond, label, detail=""):
    global ok, fail
    if cond:
        ok += 1
        print(f"PASS {label} {detail}")
    else:
        fail += 1
        print(f"FAIL {label} {detail}")


# ---- verdict.tsv ----
with open(VERDICT, encoding="utf-8-sig", newline="") as f:
    vr = list(csv.reader(f, delimiter="\t"))
vhdr, vrows = vr[0], [r for r in vr[1:] if r]
check(vhdr[:3] == ["entry", "subsystem", "verdict"], "verdict header", str(vhdr[:3]))
check(len(vrows) == 4, "verdict data rows == 4", str(len(vrows)))
check(sorted(ne(r[0]) for r in vrows) == sorted(TARGETS), "verdict entries == targets")
check(all(r[2].strip() == "PASS" for r in vrows), "all verdict PASS")
vmap = {ne(r[0]): r for r in vrows}
check(vmap["006DBE00"][1].strip() == "S07", "006DBE00 S07")
for e in TARGETS[1:]:
    check(vmap[e][1].strip() == "S11", f"{e} S11")

# ---- delta.tsv ----
with open(DELTA, encoding="utf-8-sig", newline="") as f:
    dr = list(csv.reader(f, delimiter="\t"))
dhdr, drows = dr[0], [r for r in dr[1:] if r]
check(dhdr[:6] == ["entry", "subsystem", "name", "one_line_semantics", "grade", "evidence_path"],
      "delta header", str(dhdr[:6]))
check(len(drows) == 4, "delta data rows == 4", str(len(drows)))
check(sorted(ne(r[0]) for r in drows) == sorted(TARGETS), "delta entries == targets")
dmap = {ne(r[0]): r for r in drows}
check(all(r[4].strip() == "[已证]" for r in drows), "all delta grade [已证]")
check(all(len(r) == 6 for r in drows), "all delta rows 6 cols")
check(all("[未证]" not in r[3] for r in drows), "all delta col4 no literal [未证]")
for e in TARGETS:
    print(f"DELTA {e} name={dmap[e][2]} sem_len={len(dmap[e][3])}")

# ---- atlas ----
atlas = set()
with open(ATLAS, encoding="utf-8-sig", newline="") as f:
    rd = csv.reader(f, delimiter="\t")
    ahdr = next(rd)
    for r in rd:
        if r and r[0].strip():
            atlas.add(ne(r[0]))
print(f"ATLAS data rows (unique entries) = {len(atlas)}")
for e in TARGETS:
    check(e in atlas, f"{e} in atlas")

# ---- coverage baseline ----
with open(COV, "rb") as f:
    raw = f.read()
text = raw.decode("utf-8")
lines = text.split("\n")
# trailing newline -> last element empty
trailing = lines[-1] == ""
data_lines = lines[1:-1] if trailing else lines[1:]
rows = [ln.split("\t") for ln in data_lines]
check(len(data_lines) == 18498, "coverage data rows == 18498", str(len(data_lines)))
check(all(len(r) == 8 for r in rows), "all coverage rows 8 cols")
check(not raw.startswith(b"\xef\xbb\xbf"), "coverage no BOM")
check("\r" not in text, "coverage LF only")

full_before = sum(1 for r in rows if r[4].strip() == "[已证]")
atl_in_before = sum(1 for r in rows if ne(r[0]) in atlas and r[4].strip() == "[已证]")
atl_out_before = full_before - atl_in_before
check((full_before, atl_in_before, atl_out_before) == (1650, 1644, 6),
      "baseline full/atlas_in/atlas_out",
      f"{full_before}/{atl_in_before}/{atl_out_before}")

# target rows current state
tmap = {}
for i, r in enumerate(rows):
    if ne(r[0]) in TARGETS:
        tmap[ne(r[0])] = (i, r)
check(set(tmap.keys()) == set(TARGETS), "all targets found exactly once", str(sorted(tmap.keys())))
for e in TARGETS:
    i, r = tmap[e]
    print(f"COV {e} line={i+2} sub={r[1]} name={r[2]} grade={r[4]} ev={r[5]}")
    check(r[4].strip() == "[静态推断]", f"{e} current grade [静态推断]")
    check("[未证]" not in dmap[e][3], f"{e} new semantics strict-ok")

# ---- compute counts function ----
RE_CSUB = re.compile(r"::sub_[0-9A-Fa-f]+$")
RE_SLOT = re.compile(r"::v?slot\d+$")

def compute(rowset):
    d = collections.defaultdict(collections.Counter)
    for r in rowset:
        e = ne(r[0]); s = r[1].strip()
        if e not in atlas:
            continue
        name, sem, grade = r[2].strip(), r[3], r[4].strip()
        d[s]["atlas_n"] += 1
        if name and not name.startswith("sub_"):
            d[s]["named_L"] += 1
            if not RE_CSUB.search(name):
                d[s]["named_S14"] += 1
                if not RE_SLOT.search(name):
                    d[s]["named_strict"] += 1
        if grade == "[已证]":
            d[s]["proved"] += 1
            if "[未证]" not in sem:
                d[s]["strict"] += 1
    return d

def dod(d, key):
    out = []
    for s in sorted(k for k in d if re.match(r"^S\d\d$", k)):
        a = d[s]["atlas_n"]; tn = math.ceil(0.9 * a); tp = math.ceil(0.5 * a)
        if d[s]["named_S14"] >= tn and d[s][key] >= tp:
            out.append(s)
    return out

d_before = compute(rows)
# build after rows: replace cols 4/5/6 for the 4 targets
after_rows = [list(r) for r in rows]
for e in TARGETS:
    i, _ = tmap[e]
    after_rows[i][3] = dmap[e][3]
    after_rows[i][4] = "[已证]"
    after_rows[i][5] = "NAMED_PUSH_AUDIT20/VERDICT.md"
d_after = compute(after_rows)

print("\n=== BEFORE counts ===")
for s in ("S07", "S11"):
    c = d_before[s]
    print(f"{s} atlas_n={c['atlas_n']} proved={c['proved']} strict={c['strict']} "
          f"proved_pct={pct(c['proved'], c['atlas_n'])} strict_pct={pct(c['strict'], c['atlas_n'])}")
print("TOTAL proved=%d strict=%d" % (sum(c["proved"] for c in d_before.values()),
                                     sum(c["strict"] for c in d_before.values())))
print("DoD BEFORE nominal=%s strict=%s" % (",".join(dod(d_before, "proved")), ",".join(dod(d_before, "strict"))))

print("\n=== AFTER counts ===")
for s in ("S07", "S11"):
    c = d_after[s]
    print(f"{s} atlas_n={c['atlas_n']} proved={c['proved']} strict={c['strict']} "
          f"proved_pct={pct(c['proved'], c['atlas_n'])} strict_pct={pct(c['strict'], c['atlas_n'])}")
tot_proved_after = sum(c["proved"] for c in d_after.values())
tot_strict_after = sum(c["strict"] for c in d_after.values())
print(f"TOTAL proved={tot_proved_after} strict={tot_strict_after} "
      f"proved_pct={pct(tot_proved_after, 12916)} strict_pct={pct(tot_strict_after, 12916)}")
nom_after, stc_after = dod(d_after, "proved"), dod(d_after, "strict")
print("DoD AFTER nominal=%s strict=%s" % (",".join(nom_after), ",".join(stc_after)))

full_after = sum(1 for r in after_rows if r[4].strip() == "[已证]")
atl_in_after = sum(1 for r in after_rows if ne(r[0]) in atlas and r[4].strip() == "[已证]")
check((full_after, atl_in_after, full_after - atl_in_after) == (1654, 1648, 6),
      "after full/atlas_in/atlas_out", f"{full_after}/{atl_in_after}/{full_after-atl_in_after}")

check(d_after["S07"]["proved"] == d_before["S07"]["proved"] + 1, "S07 proved +1")
check(d_after["S11"]["proved"] == d_before["S11"]["proved"] + 3, "S11 proved +3")
check(d_after["S07"]["strict"] == d_before["S07"]["strict"] + 1, "S07 strict +1")
check(d_after["S11"]["strict"] == d_before["S11"]["strict"] + 3, "S11 strict +3")

nom_before, stc_before = dod(d_before, "proved"), dod(d_before, "strict")
flip = (nom_before != nom_after) or (stc_before != stc_after)
check(not flip, "NO DoD flip",
      f"before nom={','.join(nom_before)} strict={','.join(stc_before)} | "
      f"after nom={','.join(nom_after)} strict={','.join(stc_after)}")

print(f"\nPRECHECK OK={ok} FAIL={fail}")
sys.exit(0 if fail == 0 else 1)
