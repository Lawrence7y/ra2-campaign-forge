
import re
from pathlib import Path
K9=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K9')
txt=(K9/'EVIDENCE/VIRTUAL_CALLERS.txt').read_text(encoding='utf-8')
# sections
secs={}
cur=None
for line in txt.split('\n'):
    if line.startswith('=== '):
        cur=line.strip('= ').split(' vt_offset')[0]
        secs[cur]=[]
    elif cur and line.startswith('CALL_SITE'):
        secs[cur].append(line)
for k,v in secs.items():
    print(f'SECTION {k!r}: {len(v)} call sites')
    for s in v:
        print('  ',s)
