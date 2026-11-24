import re, sys

ROOT = r"D:\Project\ra2-campaign-forge"
COV = ROOT + r"\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ATLAS = ROOT + r"\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"

# Read atlas entries (lowercase hex keys)
atlas = {}
with open(ATLAS, encoding="utf-8") as f:
    hdr = f.readline()
    for line in f:
        p = line.rstrip("\n").split("\t")
        if len(p) < 2: continue
        atlas[p[0].lower()] = int(p[1])

# Read coverage rows
rows = []
with open(COV, encoding="utf-8") as f:
    hdr = f.readline().rstrip("\n")
    for line in f:
        p = line.rstrip("\n").split("\t")
        if len(p) < 8: continue
        rows.append(p)

s16 = [p for p in rows if p[1] == "S16"]
print("TOTAL coverage rows:", len(rows))
print("S16 rows in coverage:", len(s16))

s16_atlas = [p for p in s16 if p[0].lower() in atlas]
print("S16 rows in atlas:", len(s16_atlas))

def named_R14(name):
    # L: name nonempty and not starts with sub_
    if not name: return False
    if name.startswith("sub_"): return False
    # R14: additionally exclude Class::sub_XXXXXXXX (0 in atlas anyway)
    if re.match(r"^\w+::sub_[0-9A-Fa-f]{8}$", name): return False
    return True

def named_strict(name):
    if not named_R14(name): return False
    # strict also excludes ::slotN / ::vslotN
    if re.match(r"^.*::v?slot\d+$", name): return False
    return True

def proved(p):
    return p[4] == "[已证]"

for label, pool in [("ALL_S16", s16), ("ATLAS_S16", s16_atlas)]:
    n = len(pool)
    nl = sum(1 for p in pool if named_R14(p[2]))
    ns = sum(1 for p in pool if named_strict(p[2]))
    pr = sum(1 for p in pool if proved(p))
    print(f"\n[{label}] n={n} named_R14={nl} named_strict={ns} proved={pr}")

# Focus: atlas S16 rows
print("\n=== ATLAS S16 ROWS (entry name grade nsrc conflict) ===")
for p in sorted(s16_atlas, key=lambda x: x[0]):
    print(f"{p[0]}  {p[2]:<45s} {p[4]:<10s} sz={atlas.get(p[0].lower())} conf={p[7]}")

# Coverage-only S16 rows (not in atlas)
print("\n=== S16 rows NOT in atlas ===")
for p in s16:
    if p[0].lower() not in atlas:
        print(f"{p[0]}  {p[2]:<45s} {p[4]:<10s} conf={p[7]}")
