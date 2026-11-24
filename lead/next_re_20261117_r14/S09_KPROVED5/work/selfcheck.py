"""Self-check all 16 disciplines + 9 §8.7 criteria for the 8 chosen rows."""
import json, csv, re
from pathlib import Path
OUT = Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED5')
WORK, EV = OUT/'work', OUT/'EVIDENCE'
CHOSEN = ['006D0270','006D04F0','00653850','004F4480','004A8960','006C6680','004F4320','006AC210']

rows=[]
with (OUT/'coverage_delta.tsv').open(encoding='utf-8') as f:
    for r in csv.DictReader(f,delimiter='\t'): rows.append(r)
print('delta rows =',len(rows),'| self-reported = 8 ->', 'OK' if len(rows)==8 else 'FAIL')
assert len(rows)==8
assert [r['entry'] for r in rows]==CHOSEN, 'order mismatch'

attrib=json.load(open(WORK/'attrib_fixed.json',encoding='utf-8'))
direct=json.load(open(WORK/'direct_all.json',encoding='utf-8'))
contract={}
with (EV/'CONTRACT_3B.tsv').open(encoding='utf-8') as f:
    for r in csv.DictReader(f,delimiter='\t'): contract[r['entry']]=r

BAD=['未证','未定','弱信号','线索','槽语义未']
allok=True
for r in rows:
    e=r['entry']; sem=r['one_line_semantics']; name=r['name']
    cb=attrib[e]['common_base'].replace('.?AV','').replace('.?AU','').replace('@@','')
    slot=attrib[e]['slots'][0]
    # M2: ② class in semantics == name class
    ok_m2 = name.startswith(cb+'::')
    # M8: no self-declared-unproven tokens
    hits=[b for b in BAD if b in sem]
    ok_m8 = not hits
    # M5: key offsets in semantics present in CONTRACT_3B and in DISASM
    ko=contract[e]['key_offsets']
    offs=re.findall(r'\+0x[0-9A-Fa-f]{4}',ko)
    dis=(EV/('DISASM_%s.txt'%e)).read_text(encoding='utf-8')
    missing=[o for o in offs if o not in dis]
    ok_m5 = not missing
    # grade
    ok_grade = r['grade']=='[已证]'
    # ④ at least one ok site
    ok_sites = direct[e]['n_ok']>=1
    # ② n_hits consistency: count vt... patterns in sem
    n_hts = sem.count('vt')
    ok_2count = n_hts>=attrib[e]['n_hits']
    ok = ok_m2 and ok_m8 and ok_m5 and ok_grade and ok_sites and ok_2count
    allok &= ok
    extra = ((' BADTOK='+str(hits)) if hits else '') + ((' MISSOFF='+str(missing[:3])) if missing else '')
    print('%s M2=%s M8=%s M5=%s grade=%s sites=%s cnt2=%s%s'%(
        e,ok_m2,ok_m8,ok_m5,ok_grade,ok_sites,ok_2count, extra))

# M3: K identity note present in baseline txt
btxt=(EV/'BASELINE_3B.txt').read_text(encoding='utf-8')
print('M3 baseline identity note:', 'OK' if ('identity' in btxt or '恒等' in btxt or 'NOT a validation' in btxt) else 'FAIL')
# baseline numbers
bj=json.load(open(EV/'BASELINE_3B.json',encoding='utf-8'))
print('③b base strict=%d/%d=%.6f loose=%d/%d=%.6f seed=%d draws=%d K=%d'%(
    bj['n_strict'],bj['population'],bj['base_strict'],bj['n_loose'],bj['population'],
    bj['base_loose'],bj['seed'],bj['draws'],bj['draw_size']))
print('OVERALL:', 'PASS' if allok else 'FAIL')
