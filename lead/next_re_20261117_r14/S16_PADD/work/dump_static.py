import re, sys, io

ROOT = r"D:\Project\ra2-campaign-forge"
COV = ROOT + r"\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ATLAS = ROOT + r"\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
OUT = ROOT + r"\lead\next_re_20261117_r14\S16_PADD\work\s16_static_rows.txt"

atlas = {}
with open(ATLAS, encoding="utf-8") as f:
    f.readline()
    for line in f:
        p = line.rstrip("\n").split("\t")
        if len(p) >= 2:
            atlas[p[0].lower()] = int(p[1])

rows = []
with open(COV, encoding="utf-8") as f:
    f.readline()
    for line in f:
        p = line.rstrip("\n").split("\t")
        if len(p) >= 8:
            rows.append(p)

s16_atlas = [p for p in rows if p[1] == "S16" and p[0].lower() in atlas]

with io.open(OUT, "w", encoding="utf-8") as o:
    o.write("S16 atlas [静态推断] rows (entry name grade nsrc conflict size | semantics)\n")
    o.write("="*120 + "\n")
    cnt=0
    for p in sorted(s16_atlas, key=lambda x: x[0]):
        if p[4] == "[静态推断]":
            cnt+=1
            o.write(f"{p[0]} | {p[2]} | {p[4]} | ns={p[6]} conf={p[7]} sz={atlas[p[0].lower()]}\n")
            o.write(f"    SEM: {p[3]}\n")
            o.write(f"    EVI: {p[5]}\n")
    o.write(f"\nTOTAL [静态推断] = {cnt}\n")
    o.write("\n\nS16 atlas [未证] rows:\n")
    for p in sorted(s16_atlas, key=lambda x: x[0]):
        if p[4] == "[未证]":
            o.write(f"{p[0]} | {p[2]} | {p[4]} | ns={p[6]} conf={p[7]} sz={atlas[p[0].lower()]}\n")
            o.write(f"    SEM: {p[3]}\n")
print("wrote", OUT)
