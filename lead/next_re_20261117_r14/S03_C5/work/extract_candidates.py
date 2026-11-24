"""Extract S03 A-set candidates: subsystem=S03 AND has4_strict=1 from SURVEY_RING24 classification.tsv.
Also cross-check against A_samples.tsv and exclude the 7 entries merged by S03-C4.
"""
import csv, os, sys

BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
CLS = os.path.join(BASE, "SURVEY_RING24", "EVIDENCE", "classification.tsv")
ASAMP = os.path.join(BASE, "SURVEY_RING24", "EVIDENCE", "A_samples.tsv")

EXCLUDE_C4 = set("0065CAC0 004324B0 00552490 006C9890 00631CC0 0065D150 00431E80".split())

rows = []
with open(CLS, "r", encoding="utf-8") as f:
    r = csv.DictReader(f, delimiter="\t")
    for row in r:
        if row["subsystem"] == "S03" and row["has4_strict"] == "1":
            rows.append(row)

print("S03 has4_strict=1 count:", len(rows))
print("Columns:", list(rows[0].keys()) if rows else None)
print()
# header compact
cols = ["entry","has2_rtti","has4_strict","n_direct_all","n_direct_out","n_livevt",
        "rtti_classes","rtti_vt","rtti_slot","ring4_direct_sites","ring4_livevt","name"]
print("\t".join(cols))
for x in rows:
    print("\t".join(str(x.get(c,"")) for c in cols))

print("\n--- Excluded (already merged by S03-C4) present in A set? ---")
for x in rows:
    if x["entry"] in EXCLUDE_C4:
        print("EXCLUDED", x["entry"], x["name"])

print("\n--- Remaining candidates (not in exclude) ---")
rem = [x for x in rows if x["entry"] not in EXCLUDE_C4]
print("count:", len(rem))
for x in rem:
    print(x["entry"], x["name"], "direct_sites=", x["ring4_direct_sites"], "vt=", x["rtti_vt"], "slot=", x["rtti_slot"])
