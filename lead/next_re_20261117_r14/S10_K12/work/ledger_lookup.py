
import csv
from pathlib import Path
R=Path(r'D:\Project\ra2-campaign-forge')
COV=R/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
with COV.open(encoding='utf-8',newline='') as f:
    rd=csv.DictReader(f,delimiter='\t')
    hdr=rd.fieldnames
    rows=list(rd)
print('HEADER=',hdr)
print('TOTAL=',len(rows))
# index by entry lower
idx={}
for r in rows:
    idx.setdefault(r['entry'].strip().lower(),[]).append(r)

targets=['0051D6F0','0051DAF0','0051B1F0','0051BAB0','00522340','005B3A00','004D55C0',
         '0051F330','0051F6E0','0051F39D','0051F7AF','005B3060','00521760','0051DAA1',
         '0051BBEF','004DAEE1','004DAEF3','004D473A','00511760','004D55C0']
# also find RandomRanged by name search
for t in targets:
    k=t.lower()
    if k in idx:
        for r in idx[k]:
            print(f"ENTRY {t}: grade={r.get('grade')} sub={r.get('subsystem')} name={r.get('name')!r} sem={r.get('sem')!r} conf={r.get('conflict')}")
    else:
        print(f"ENTRY {t}: NOT_IN_COVERAGE")
# find by name keywords
for kw in ['Random','Ranged','StopMoving','Mission','dtor','Deleting','5B3A00']:
    hits=[]
    for r in rows:
        blob=(r.get('name','')+' '+r.get('sem','')).lower()
        if kw.lower() in blob:
            hits.append((r['entry'],r.get('grade'),r.get('name'),r.get('sem')))
        if len(hits)>=12: break
    print(f'\nNAMEKW {kw!r}: {len(hits)} hits (cap12)')
    for h in hits: print('  ',h)
