
import json
from pathlib import Path
ROOT=Path(r'D:\Project\ra2-campaign-forge')
OUT=ROOT/'lead/next_re_20261117_r14/SURVEY_RING24'
idx=json.load(open(OUT/'work'/'index.json'))
livevt={int(k,16):v for k,v in idx['livevt'].items()}
installs={int(k,16):v for k,v in idx['installs'].items()}
M32_S20='0040F0A0 0040F150 0053C6A0 005514B0 00551560 00557090 00557140'.split()
M32_S10='0045A560 0045A610 006B1850 006B1900 006B8660 006B8710'.split()
for tag,lst in (('S20',M32_S20),('S10',M32_S10)):
    for a in lst:
        e=int(a,16)
        print(tag,a,'livevt' if e in livevt else 'NOT-in-livevt', (livevt.get(e) or [''])[0] if e in livevt else '')
print()
# how many entries in livevt total
print('livevt entries', len(livevt))
print('installs globals', len(installs), 'total install records', sum(len(v) for v in installs.values()))
# sample: check a livevt entry detail
for a in ['0040F0A0','0045A560','0040B740']:
    e=int(a,16)
    print(a, livevt.get(e))
