#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S05-K2: build coverage_delta.tsv from byte-proven findings.
S05 [静态推断] vslot funcs of the 10 core object classes with >=3 proven-field
data accesses (vcall/lea/esp excluded) -> [已证] behavioral annotation rows.
"""
import os, json, csv
ROOT=r"D:\Project\ra2-campaign-forge"
OUTDIR=os.path.join(ROOT,"lead","next_re_20261117_r14","S05-K2"); EVID=os.path.join(OUTDIR,"EVIDENCE")
d=json.load(open(os.path.join(EVID,"t5_fieldslot_upgrades.json"),encoding="utf-8"))
CORE=('AbstractClass','ObjectClass','MissionClass','RadioClass','TechnoClass','FootClass',
      'BuildingClass','UnitClass','InfantryClass','AircraftClass')
byentry={r['entry']:r for r in d['rows']}
rows=[]
for e,r in byentry.items():
    nm=r['name']
    if not any(nm.startswith(c+'::') for c in CORE): continue
    tot=sum(f['n'] for f in r['fields'].values())
    if tot<3: continue
    parts=[]
    for k,f in sorted(r['fields'].items(), key=lambda x:-x[1]['n']):
        parts.append("%s %s x%d"%(k,f['sem'],f['n']))
    sem="vtable slot fn; byte-proven body: "+', '.join(parts)+"; vcall/lea/esp excluded"
    rows.append([e,'S05',nm,sem,'[已证]',"EVIDENCE/t5_fieldslot_upgrades.json#"+e])
rows.sort()
print('delta rows:',len(rows))
for r in rows:
    print('  ',r[0],r[2],'|',r[3][:90])
with open(os.path.join(OUTDIR,'coverage_delta.tsv'),'w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t',lineterminator='\n')
    w.writerow(['entry','subsystem','name','one_line_semantics','grade','evidence_path'])
    w.writerows(rows)
print('WROTE',os.path.join(OUTDIR,'coverage_delta.tsv'))
