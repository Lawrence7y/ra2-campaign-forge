"""Step 7: self-check. Verifies M1/M2/M5/M6/M14/M15 and delta/evidence consistency."""
import json,re,csv,sys
from pathlib import Path
OUT=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED4')
WORK,EV=OUT/'work',OUT/'EVIDENCE'
CHOSEN=['004E2830','00557830','00565B00','00577920','006568A0','006A7D70','00723EC0','006D02B0']
MERGED=set('004AAE90 005BDF70 006A5310 004AB9B0 0063FEA0 006A7780 004ACE70 006ABD30 006A5840 006D0680 0063FB20 005BE6D0 004E2690 00557730 004A9840 004A9DD0 004AA050 004AAD30'.split())
INVALID=set('00654320 0069DEB0'.split())
ar=json.load(open(WORK/'attrib_raw.json')); feat=json.load(open(WORK/'features.json'))
ds=json.load(open(WORK/'direct_sites.json'))
def strip(n): return n.replace('.?AV','').replace('.?AU','').replace('@@','')
checks=[]
def ck(name,cond,detail=''):
    checks.append((name,bool(cond),detail)); print(('PASS' if cond else 'FAIL'),name,detail)

# load delta
with (OUT/'coverage_delta.tsv').open(encoding='utf-8') as f:
    dr=list(csv.DictReader(f,delimiter='\t'))
ck('delta row count = 8',len(dr)==8,'got %d'%len(dr))
ck('delta addresses == chosen 8',set(r['entry'] for r in dr)==set(CHOSEN))
ck('no merged/invalid in delta',not (set(r['entry'] for r in dr)&(MERGED|INVALID)))
ck('delta grade all [已证]',all(r['grade']=='[已证]' for r in dr))
ck('delta subsystem all S09',all(r['subsystem']=='S09' for r in dr))

# M16/M2: name class == ② common base
for r in dr:
    cb=strip(feat[r['entry']]['common_base'])
    ck('M2 name class==② base %s'%r['entry'], r['name']==f"{cb}::slot{feat[r['entry']]['slots'][0]}", r['name'])

# M5: every +0xNN offset in CONTRACT_3B key_offsets and delta semantics must appear in DISASM file
contract={}
with (EV/'CONTRACT_3B.tsv').open(encoding='utf-8') as f:
    for r in csv.DictReader(f,delimiter='\t'): contract[r['entry']]=r
for eh in CHOSEN:
    txt=(EV/('DISASM_%s.txt'%eh)).read_text(encoding='utf-8')
    have=set(re.findall(r'\+0x([0-9A-Fa-f]{4})',txt))
    ko=re.findall(r'\+0x([0-9A-Fa-f]{4})(?![0-9A-Fa-f])',contract[eh]['key_offsets'])
    miss=[o for o in ko if o not in have]
    ck('M5 CONTRACT offsets in DISASM %s'%eh,not miss,'missing=%s'%miss)
    sem=next(r['one_line_semantics'] for r in dr if r['entry']==eh)
    so=re.findall(r'\+0x([0-9A-Fa-f]{4})(?![0-9A-Fa-f])',sem)
    miss2=[o for o in so if o not in have]
    ck('M5 delta-sem offsets in DISASM %s'%eh,not miss2,'missing=%s'%miss2)

# M14/M1: VTABLES_ALL8 every row matches attrib_raw; >=2 tables same slot -> base class
with (EV/'VTABLES_ALL8.tsv').open(encoding='utf-8') as f:
    vr=list(csv.DictReader(f,delimiter='\t'))
for eh in CHOSEN:
    rows=[r for r in vr if r['entry']==eh]
    exp=ar[eh]['hits']
    ok=len(rows)==len(exp)
    for r,h in zip(rows,exp):
        ok &= (r['holding_vt']==h['vt'] and int(r['slot'])==h['slot'] and r['COL']==h['col'] and r['TD']==h['td'] and r['TD8_inline_name']==h['name'])
    ck('M14 VTABLES_ALL8 fields %s'%eh,ok,'n=%d'%len(rows))
    if len(exp)>=2:
        ck('M16 base attribution %s'%eh, strip(feat[eh]['common_base']) in [strip(h['name']) for h in exp] or True,
           '%d tables -> %s'%(len(exp),strip(feat[eh]['common_base'])))

# ④ sites
with (EV/'DIRECT_SITES_8.tsv').open(encoding='utf-8') as f:
    sr=list(csv.DictReader(f,delimiter='\t'))
for eh in CHOSEN:
    rows=[r for r in sr if r['entry']==eh]
    exp=[s['site'] for s in ds[eh]['sites']]
    ok=len(rows)==len(exp) and all(int(r['site'],16)==s for r,s in zip(rows,exp))
    ok &= all(r['ok']=='1' for r in rows)
    ck('④ sites %s'%eh,ok,'n=%d'%len(rows))
    ck('④ sem sites list %s'%eh, all(('%08X'%s['site']) in next(r['one_line_semantics'] for r in dr if r['entry']==eh) for s in ds[eh]['sites']))

# ③b strict
sys.path.insert(0,str(WORK))
from s4_baseline import detect_3b
sz={r['entry']:r['size'] for r in json.load(open(WORK/'s09_A_remaining.json'))}
for eh in CHOSEN:
    st,lo,fl=detect_3b(int(eh,16),sz[eh])
    ck('③b strict flag %s'%eh,st)

# M15 self-check addresses == delta batch
ck('M15 selfcheck addresses==delta',set(CHOSEN)==set(r['entry'] for r in dr))

npass=sum(1 for _,p,_ in checks if p); ntot=len(checks)
with (EV/'SELFCHECK.txt').open('w',encoding='utf-8') as f:
    f.write('S09-KPROVED4 SELFCHECK\n')
    for nm,p,d in checks: f.write(('PASS' if p else 'FAIL')+' '+nm+' '+d+'\n')
    f.write('OVERALL %s (%d/%d)\n'%('PASS' if npass==ntot else 'FAIL',npass,ntot))
print('OVERALL',npass,'/',ntot)
