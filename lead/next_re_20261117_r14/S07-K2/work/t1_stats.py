"""T1: S07 statistics from coverage.tsv ∩ function_atlas.tsv.
R14-R14 S caliber: named = name non-empty, not starting with 'sub_', not 'Class::sub_'.
"""
import os

ROOT = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")

def load_atlas():
    d = {}
    with open(ATLAS, "r", encoding="utf-8", errors="replace") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            p = line.split("\t")
            rec = dict(zip(hdr, p))
            try:
                va = int(rec["entry"], 16)
            except Exception:
                continue
            d[va] = rec
    return d

def load_cov():
    rows = []
    with open(COV, "r", encoding="utf-8", errors="replace") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            p = line.split("\t")
            rec = dict(zip(hdr, p))
            rec["va"] = int(rec["entry"], 16)
            rows.append(rec)
    return rows, hdr

atlas = load_atlas()
cov, hdr = load_cov()

# S07 ∩ atlas
s07 = [r for r in cov if r.get("subsystem") == "S07"]
s07_atlas = [r for r in s07 if r["va"] in atlas]

def is_named_L(name):
    if not name:
        return False
    if name.startswith("sub_"):
        return False
    return True

def is_sub_class(name):
    return "Class::sub_" in name or name.startswith("Class::sub_")

def is_named_S(name):
    return is_named_L(name) and not is_sub_class(name)

def is_proved(grade):
    return grade == "[已证]"

atlas_n = len(s07_atlas)
named_L = sum(1 for r in s07_atlas if is_named_L(r.get("name", "")))
named_S = sum(1 for r in s07_atlas if is_named_S(r.get("name", "")))
class_sub = sum(1 for r in s07_atlas if is_sub_class(r.get("name", "")))
proved = sum(1 for r in s07_atlas if is_proved(r.get("grade", "")))

# also full coverage S07 (not just atlas)
s07_full = len(s07)
s07_full_proved = sum(1 for r in s07 if is_proved(r.get("grade", "")))
s07_full_named_S = sum(1 for r in s07 if is_named_S(r.get("name", "")))

print("=== S07 ∩ function_atlas (A caliber) ===")
print("atlas_n (S07 ∩ atlas)      =", atlas_n)
print("named_n (L)                =", named_L, " (%.2f%%)" % (100.0*named_L/atlas_n))
print("named_n (S)                =", named_S, " (%.2f%%)" % (100.0*named_S/atlas_n))
print("Class::sub_ count          =", class_sub)
print("proved_n                   =", proved, " (%.2f%%)" % (100.0*proved/atlas_n))
print()
print("=== S07 full coverage (all rows) ===")
print("full rows                  =", s07_full)
print("full proved                =", s07_full_proved)
print("full named_S               =", s07_full_named_S)
print()
# gap to 50% proved using atlas denominator
for den_label, den in [("atlas_n(on-disk PANEL=804)", atlas_n), ("card 807", 807), ("PANEL 804", 804)]:
    need = den // 2 + (1 if den % 2 else 0)  # ceil(den/2)
    print("50%% of %-28s = %d ; need +%d proved" % (den_label, need, need - proved))
