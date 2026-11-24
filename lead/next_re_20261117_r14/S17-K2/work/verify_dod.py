#!/usr/bin/env python3
"""S17-K2: simulate M-card merge of coverage_delta.tsv and recompute DoD numbers.
Read-only on coverage.tsv/atlas/delta. Writes recomputation proof to EVIDENCE.
"""
import csv, re, os, io

ROOT = r"D:\Project\ra2-campaign-forge"
CARD = os.path.join(ROOT, r"lead\next_re_20261117_r14\S17-K2")
COV  = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS= os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
DELTA= os.path.join(CARD,"coverage_delta.tsv")

def is_named(name):
    n=(name or "").strip()
    if not n: return False
    if re.fullmatch(r"sub_[0-9A-Fa-f]{8}(?:_\d+)?",n): return False
    if n.lower().startswith("sub_") and re.fullmatch(r"sub_[0-9a-fA-F]{8}.*",n): return False
    return True

atlas=set()
with open(ATLAS,encoding="utf-8",errors="replace") as f:
    for row in csv.DictReader(f,delimiter="\t"):
        atlas.add(row["entry"].strip().upper())

rows=[]
with open(COV,encoding="utf-8",errors="replace") as f:
    for row in csv.DictReader(f,delimiter="\t"):
        if row["subsystem"].strip().upper()=="S17":
            rows.append({k:(v or "").strip() for k,v in row.items()})

delta={}
with open(DELTA,encoding="utf-8",errors="replace") as f:
    for row in csv.reader(f,delimiter="\t"):
        if len(row)<6: continue
        delta[row[0].strip().upper()]={"name":row[2],"sem":row[3],"grade":row[4],"ev":row[5]}

out=io.StringIO()
def p(*a): print(*a,file=out)

def stats(rr,label):
    n=len(rr); nm=sum(1 for r in rr if is_named(r["name"])); pv=sum(1 for r in rr if r["grade"]=="[已证]")
    p(f"  {label}: n={n} named={nm} ({100*nm/n:.2f}%) proved={pv} ({100*pv/n:.2f}%)")

p("S17-K2 DoD recomputation (atlas分母 + 全coverage 双口径)")
p(f"delta rows = {len(delta)}")
p("BEFORE:")
a=[r for r in rows if r["entry"].upper() in atlas]; o=[r for r in rows if r["entry"].upper() not in atlas]
stats(a,"atlas-internal  "); stats(rows,"full-coverage   "); p(f"  outside-atlas rows = {len(o)}")

# apply delta
applied=0
for r in rows:
    d=delta.get(r["entry"].upper())
    if d:
        p(f"  apply {r['entry']}: name {r['name']} -> {d['name']}; grade {r['grade']} -> {d['grade']}")
        r["name"]=d["name"]; r["one_line_semantics"]=d["sem"]; r["grade"]=d["grade"]; r["evidence_path"]=d["ev"]
        applied+=1
p(f"\nAFTER (applied {applied}/{len(delta)} delta rows):")
stats(a,"atlas-internal  "); stats(rows,"full-coverage   ")

p("\nDOOR thresholds:")
for label,rr in [("atlas",a),("full",rows)]:
    n=len(rr); nm=sum(1 for r in rr if is_named(r["name"])); pv=sum(1 for r in rr if r["grade"]=="[已证]")
    p(f"  {label}: named {nm}/{n} = {100*nm/n:.2f}% {'PASS' if nm/n>=0.90 else 'FAIL'} (>=90%) | proved {pv}/{n} = {100*pv/n:.2f}% {'PASS' if pv/n>=0.50 else 'FAIL'} (>=50%)")

with open(os.path.join(CARD,"EVIDENCE","DOD_RECOMPUTE.txt"),"w",encoding="utf-8") as f: f.write(out.getvalue())
print("wrote DOD_RECOMPUTE.txt")
