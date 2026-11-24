import os, re, io
D = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16_PADD"
files = ["PROGRESS.md","UNKNOWNS.md","DISAGREE.md","coverage_delta.tsv","EVIDENCE/FOUR_RINGS.md"]
for f in files:
    p=os.path.join(D,f)
    print(f, "EXISTS" if os.path.exists(p) else "MISSING", os.path.getsize(p) if os.path.exists(p) else "")
print("PROGRESS lines:", sum(1 for _ in open(os.path.join(D,"PROGRESS.md"),encoding="utf-8")))
print("\n--- coverage_delta.tsv check ---")
rows=[]
with open(os.path.join(D,"coverage_delta.tsv"),encoding="utf-8") as f:
    hdr=f.readline().rstrip("\n")
    print("header:",hdr)
    for line in f:
        p=line.rstrip("\n").split("\t")
        rows.append(p)
print("data rows:",len(rows))
for p in rows:
    print("cols:",len(p),"entry:",p[0],"grade:",p[4])
    sem=p[3]
    bad=[w for w in ["未证","未定","弱信号","线索"] if w in sem]
    print("   forbidden words in col4:",bad)
    print("   has ③b:", "③b" in sem, " has +0x:", "+0x" in sem)
    print("   class in name:", p[2].split("::")[0], " appears in sem:", p[2].split("::")[0] in sem)

# Work dir
print("\n--- work dir ---")
for f in sorted(os.listdir(os.path.join(D,"work"))):
    print("  ",f)
