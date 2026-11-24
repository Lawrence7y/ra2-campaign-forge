# -*- coding: utf-8 -*-
# ⑨ self-check: disk current values for the 9 rows; must be [静态推断] + placeholder names.
import csv, json, os
COV=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
TARGETS=["0040B820","0040F5E0","0040F760","0040FD30","0046B780","0048AE90","0054EA10","0062B1F0","0065C070"]
rows={}
with open(COV,'r',encoding='utf-8',newline='') as f:
    for r in csv.reader(f,delimiter='\t'):
        if r and r[0] in TARGETS: rows[r[0]]={'subsystem':r[1],'name':r[2],'sem':r[3],'grade':r[4]}
out={}
for t in TARGETS:
    out[t]=rows.get(t)
    print(t, json.dumps(out[t],ensure_ascii=False))
assert len(out)==9 and all(v is not None for v in out.values()), "missing rows"
assert all(v['grade']=='[静态推断]' for v in out.values()), "grade mismatch -> STOP (⑨)"
assert all('vslot' in v['name'] or 'slot' in v['name'] for v in out.values()), "name not placeholder -> STOP (⑨)"
print("SELFCHECK PASS: all 9 [静态推断] placeholder; no mismatch with card's disk statement")
json.dump(out,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'DISK_CHECK.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
