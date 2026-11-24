"""Step 5: emit per-row EVIDENCE for the 8 chosen rows:
  VTABLES_ALL8.tsv  - every holding vtable (vt + slot + TD + TD+8 inline name) + ⑯ attribution
  CLASS_ATTRIB8.tsv - ② attribution conclusion per row
  CONTRACT_3B.tsv   - ③b tier + entry-relative offsets + detail
Offsets are taken verbatim from the DISASM_*.txt files (entry-relative +0xNN).
"""
import json
from pathlib import Path

OUT = Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED4')
WORK, EV = OUT/'work', OUT/'EVIDENCE'
CHOSEN = ['004E2830','00557830','00565B00','00577920','006568A0','006A7D70','00723EC0','006D02B0']

ar=json.load(open(WORK/'attrib_raw.json'))
feat=json.load(open(WORK/'features.json'))
svc={r['entry']:r for r in json.load(open(WORK/'s09_A_remaining.json'))}

def strip(n): return n.replace('.?AV','').replace('.?AU','').replace('@@','') if n else 'None'

with (EV/'VTABLES_ALL8.tsv').open('w',encoding='utf-8') as f:
    f.write('entry\tholding_vt\tslot\tCOL\tTD\tTD8_inline_name\tname_class\tattributed_common_base\n')
    for eh in CHOSEN:
        cb=strip(feat[eh]['common_base'])
        for h in ar[eh]['hits']:
            nc=strip(h['name'])
            f.write('%s\t%s\t%d\t%s\t%s\t%s\t%s\t%s\n'%(
                eh,h['vt'],h['slot'],h['col'],h['td'],h['name'],nc,cb))

with (EV/'CLASS_ATTRIB8.tsv').open('w',encoding='utf-8') as f:
    f.write('entry\tn_holding_tables\tslots\tall_class_names\tcommon_base_16\tdelta_name\tatlas_size\n')
    for eh in CHOSEN:
        cb=strip(feat[eh]['common_base']); slot=feat[eh]['slots'][0]
        names=';'.join(strip(h['name']) for h in ar[eh]['hits'])
        f.write('%s\t%d\t%s\t%s\t%s\t%s::slot%d\t%d\n'%(
            eh,ar[eh]['n_hits'],';'.join(map(str,feat[eh]['slots'])),names,cb,cb,slot,svc[eh]['size']))

print('wrote VTABLES_ALL8.tsv and CLASS_ATTRIB8.tsv')
for eh in CHOSEN:
    print(eh,'n=',ar[eh]['n_hits'],'slots=',feat[eh]['slots'],'base=',strip(feat[eh]['common_base']),
          'name=',f"{strip(feat[eh]['common_base'])}::slot{feat[eh]['slots'][0]}")
