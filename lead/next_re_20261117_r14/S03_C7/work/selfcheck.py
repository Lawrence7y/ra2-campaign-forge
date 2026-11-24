import os, csv, json, re
BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_C7"

# 1. PROGRESS lines
p = os.path.join(BASE,"PROGRESS.md")
n = len(open(p,encoding='utf-8').read().splitlines())
print("PROGRESS.md lines =", n, "(<=60)", n<=60)

# 2. delta
rows=list(csv.DictReader(open(os.path.join(BASE,"coverage_delta.tsv"),encoding='utf-8'),delimiter='\t'))
print("delta data rows =", len(rows))
BAD=['未证','未定','弱信号','线索']
for r in rows:
    sem=r['one_line_semantics']
    hit=[w for w in BAD if w in sem]
    offs=re.findall(r'\+0x[0-9A-Fa-f]+', sem)
    print(f"  {r['entry']} grade={r['grade']} badwords={hit} anchors={offs}")
    # check evidence file exists
    ev=os.path.join(BASE,r['evidence_path'])
    print("     evidence exists:", os.path.exists(ev))
    # check each anchor offset appears in EVIDENCE dis/ANCHOR
    anchor_file=os.path.join(BASE,"EVIDENCE",f"ANCHOR_{r['entry']}.txt")
    txt=open(anchor_file,encoding='utf-8').read() if os.path.exists(anchor_file) else ""
    missing=[o for o in offs if o not in txt]
    print("     anchors missing from ANCHOR file:", missing)

# 3. all deliverables
for f in ["PROGRESS.md","UNKNOWNS.md","DISAGREE.md","coverage_delta.tsv"]:
    print(f, "exists:", os.path.exists(os.path.join(BASE,f)))
for d in ["EVIDENCE","work"]:
    print(d, "files:", len(os.listdir(os.path.join(BASE,d))))
