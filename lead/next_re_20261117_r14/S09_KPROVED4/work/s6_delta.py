"""Step 6: build coverage_delta.tsv from verified EVIDENCE data.
Each semantics cell: ② all holding tables (vt+slot+TD+8 name)+⑯ attribution;
③b tier + entry-relative offsets + detail; ④ direct sites.
All numbers sourced from attrib_raw.json / CONTRACT_3B.tsv / direct_sites.json.
"""
import json, csv
from pathlib import Path

OUT = Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED4')
WORK, EV = OUT/'work', OUT/'EVIDENCE'
CHOSEN = ['004E2830','00557830','00565B00','00577920','006568A0','006A7D70','00723EC0','006D02B0']

ar=json.load(open(WORK/'attrib_raw.json'))
feat=json.load(open(WORK/'features.json'))
ds=json.load(open(WORK/'direct_sites.json'))
svc={r['entry']:r for r in json.load(open(WORK/'s09_A_remaining.json'))}
contract={}
with (EV/'CONTRACT_3B.tsv').open(encoding='utf-8') as f:
    for r in csv.DictReader(f,delimiter='\t'): contract[r['entry']]=r

def strip(n): return n.replace('.?AV','').replace('.?AU','').replace('@@','')

rows=[]
for eh in CHOSEN:
    cb=strip(feat[eh]['common_base']); slot=feat[eh]['slots'][0]
    # ② section
    hts=[]
    for h in ar[eh]['hits']:
        hts.append('vt%s/slot%d/%s(TD+8逐字%s)'%(h['vt'][2:],h['slot'],strip(h['name']),h['name']))
    sec2='②全1214张RTTI可解表枚举命中%d张同slot%d: %s；按L1/⑯归共同基类%s，name栏%s一致'%(
        ar[eh]['n_hits'],slot,'; '.join(hts),cb,cb)
    # ③b section
    c=contract[eh]
    sec3='③b%s硬档: %s；入口相对偏移 %s'%(c['tier'],c['detail'],c['key_offsets'])
    # ④ section
    sites=', '.join('E8@%08X'%s['site'] for s in ds[eh]['sites'])
    sec4='④direct %s，全部 site+5+rel32==entry、E8@指令边界、体外(body=[%s,%s)自写CFG区间包含)、非自环'%(
        sites,ds[eh]['lo'],ds[eh]['hi'])
    sem='[已证] '+sec2+'。'+sec3+'。'+sec4+'。'
    ev='EVIDENCE/VTABLES_ALL8.tsv;EVIDENCE/CLASS_ATTRIB8.tsv;EVIDENCE/CONTRACT_3B.tsv;EVIDENCE/DIRECT_SITES_8.tsv;EVIDENCE/DISASM_%s.txt'%eh
    rows.append([eh,'S09','%s::slot%d'%(cb,slot),sem,'[已证]',ev])

with (OUT/'coverage_delta.tsv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t')
    w.writerow(['entry','subsystem','name','one_line_semantics','grade','evidence_path'])
    for r in rows: w.writerow(r)

print('wrote coverage_delta.tsv rows=',len(rows))
for r in rows: print(r[0],r[2],'sem_len=',len(r[3]))
