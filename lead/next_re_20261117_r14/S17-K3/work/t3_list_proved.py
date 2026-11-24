#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T3: list all S17 [已证] rows with evidence_path, and pick 5 for audit."""
import csv,io,os,sys
ROOT=r"D:\Project\ra2-campaign-forge"
COV=os.path.join(ROOT,r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
with io.open(COV,"r",encoding="utf-8-sig",newline="") as f:
    cov=list(csv.DictReader(f,delimiter="\t"))
ATLAS=os.path.join(ROOT,r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
with io.open(ATLAS,"r",encoding="utf-8-sig",newline="") as f:
    atlas=list(csv.DictReader(f,delimiter="\t"))
aent=set(r["entry"].lower() for r in atlas)
s17p=[r for r in cov if r.get("subsystem")=="S17" and r.get("grade")=="[已证]" and r["entry"].lower() in aent]
out=[]
out.append(f"S17 [已证] rows within atlas: {len(s17p)}")
out.append("entry\tname\tsem\tevidence_path")
for r in sorted(s17p,key=lambda x:x["entry"]):
    out.append("\t".join([r["entry"],r["name"],r["one_line_semantics"],r["evidence_path"]]))
txt="\n".join(out)+"\n"
CARD=os.path.join(ROOT,r"lead\next_re_20261117_r14\S17-K3")
with io.open(os.path.join(CARD,"EVIDENCE","t3_proved_list.txt"),"w",encoding="utf-8") as f:f.write(txt)
sys.stdout.write(f"written {len(s17p)} proved rows\n")
