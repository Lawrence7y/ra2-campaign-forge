
import csv
from pathlib import Path
ATL=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv')
with ATL.open(encoding='utf-8-sig',newline='') as f:
    rd=csv.DictReader(f,delimiter='\t')
    print('HDR=',rd.fieldnames)
    rows={r['entry'].strip().lower():r for r in rd}
targets=['0051D6F0','0051DAF0','0051B1F0','0051BAB0','00522340','00521760','00517FA0','00519630','0051AA40','0051F330','0051F6E0','004D55C0','0065C7E0','004DA530','004D4280','0051BB7A']
for t in targets:
    r=rows.get(t.lower())
    print(t, 'size=', r['size'] if r else 'NOT_IN_ATLAS')
