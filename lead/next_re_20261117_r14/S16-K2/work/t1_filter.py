#!/usr/bin/env python3
"""S16-K2 T1: filter subsystem==S16 rows from coverage.tsv; compute both denominators."""
import csv, re, os, collections

ROOT = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
OUT = os.path.join(ROOT, r"lead\next_re_20261117_r14\S16-K2\work\t1_targets_raw.tsv")

def load_tsv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))

cov = load_tsv(COV)
atlas = load_tsv(ATLAS)
atlas_entries = set(r["entry"].strip().upper() for r in atlas)

SUB = "S16"
s16 = [r for r in cov if r.get("subsystem", "").strip() == SUB]
for r in s16:
    r["entry"] = r["entry"].strip().upper()
    r["_in_atlas"] = r["entry"] in atlas_entries

# naming definitions
def is_placeholder(name):
    n = (name or "").strip()
    return (n == "" or re.fullmatch(r"sub_[0-9A-Fa-f]{8}", n) is not None
            or n.startswith("sub_"))

def is_grade_proved(g):
    return (g or "").strip() == "[已证]"

def stats(rows, label):
    n = len(rows)
    named_strict = sum(1 for r in rows if not is_placeholder(r["name"]))
    named_nonempty = sum(1 for r in rows if (r["name"] or "").strip() != "")
    proved = sum(1 for r in rows if is_grade_proved(r["grade"]))
    grades = collections.Counter((r["grade"] or "").strip() for r in rows)
    print(f"[{label}] n={n} named(strict)={named_strict} ({named_strict/n*100:.2f}%) "
          f"named(nonempty)={named_nonempty} ({named_nonempty/n*100:.2f}%) proved={proved} ({proved/n*100:.2f}%)")
    print(f"   grades={dict(grades)}")
    return dict(n=n, named=named_strict, proved=proved, grades=grades)

print("== coverage.tsv total rows:", len(cov), " atlas entries:", len(atlas_entries))
print()
all_s16 = stats(s16, "ALL coverage S16")
in_atlas = [r for r in s16 if r["_in_atlas"]]
out_atlas = [r for r in s16 if not r["_in_atlas"]]
atlas_stats = stats(in_atlas, "S16 IN ATLAS")
out_stats = stats(out_atlas, "S16 OUT OF ATLAS")
print()
print("PANEL claims atlas_n=90 named_n=73 proved_n=42")
print(f"  computed atlas_n={atlas_stats['n']} named={atlas_stats['named']} proved={atlas_stats['proved']}")
print()
# gap calc to thresholds, using atlas denominator
n = atlas_stats["n"]
need_named = max(0, int(__import__("math").ceil(0.9*n)) - atlas_stats["named"])
need_proved = max(0, int(__import__("math").ceil(0.5*n)) - atlas_stats["proved"])
print(f"DoD gap (atlas denom n={n}): need named +{need_named} (to {int(__import__('math').ceil(0.9*n))}), "
      f"need proved +{need_proved} (to {int(__import__('math').ceil(0.5*n))})")
print()
# write raw target rows
with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["entry","in_atlas","name","grade","one_line_semantics","evidence_path","is_named_strict","is_proved"])
    for r in sorted(s16, key=lambda x:(not x["_in_atlas"], x["entry"])):
        w.writerow([r["entry"], "Y" if r["_in_atlas"] else "N", r["name"], r["grade"],
                    r["one_line_semantics"], r["evidence_path"],
                    "Y" if not is_placeholder(r["name"]) else "N",
                    "Y" if is_grade_proved(r["grade"]) else "N"])
print("wrote", OUT, "rows:", len(s16))
