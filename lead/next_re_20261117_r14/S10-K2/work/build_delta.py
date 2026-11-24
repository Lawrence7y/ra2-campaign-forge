"""
S10-K2: build coverage_delta.tsv from freshly-proven addresses.
- 43 distinct non-stub mission handlers (slot semantics from dispatch call-context) -> [已证]
- 5 concrete GetSize funcs (double-point closed) -> [已证]
Only rows where coverage has the entry AND grade != [已证] become upgrades;
entries not in coverage become new rows (marked). Base stubs are NOT upgraded.
Never writes COVERAGE/coverage.tsv.
"""
import os, csv, json
ROOT=r'D:\Project\ra2-campaign-forge'
COV=os.path.join(ROOT,r'lead\next_re_20261117_r14\COVERAGE\coverage.tsv')
OUT=os.path.join(ROOT,r'lead\next_re_20261117_r14\S10-K2')
EVID=os.path.join(OUT,'EVIDENCE')
coverage={}
with open(COV,encoding='utf-8') as f:
    for r in csv.DictReader(f,delimiter='\t'):
        coverage[r['entry'].upper()]=r

with open(os.path.join(EVID,'t2_mission_slots.json')) as f: slots=json.load(f)
with open(os.path.join(EVID,'t2_dispatch.json')) as f: disp=json.load(f)
with open(os.path.join(EVID,'t3_getsize_raw.json')) as f: t3=json.load(f)

# address -> (classes/slots, mission names)
STUB=set(range(0x5B2E10,0x5B2FC0+1,0x10))
addr_slots={}
for cls,rows in slots.items():
    for r in rows:
        a=r['addr']
        addr_slots.setdefault(a,[]).append((cls.replace('.?AV','').replace('@@',''),r['slot']))
# slot -> mission names
slot_m={}
for d in disp:
    if d.get('slot') is not None:
        slot_m.setdefault(d['slot'],[]).append(d['name'])

rows=[]; L=[]
def P(s=''):
    L.append(str(s)); print(s)
P('===== coverage_delta.tsv generation =====')
# mission handlers
for a,refs in sorted(addr_slots.items()):
    if int(a,16) in STUB: continue
    sl=set(s for _,s in refs); cls=sorted(set(c for c,_ in refs))
    missions=sorted(set(m for s in sl for m in slot_m.get(s,[])))
    sem='Mission handler v[%s]: %s (%s)'%(','.join('v%d'%s for s in sorted(sl)), ','.join(missions[:6]), ','.join(cls[:4]))
    grade='[已证]'; ev='EVIDENCE/t2_final_slots.txt;EVIDENCE/t2_mission_slots.txt;EVIDENCE/t2_dispatch.txt'
    key=a.upper()
    if key in coverage:
        cur=coverage[key]
        P('  %s in coverage cur_grade=%s name=%s -> upgrade'%(a,cur['grade'],cur['name']))
        rows.append((a,'S10',cur['name'] if not cur['name'].startswith('sub_') else 'MissionHandler_'+a,sem,grade,ev))
    else:
        P('  %s NOT in coverage -> new row'%a)
        rows.append((a,'S10','MissionHandler_'+a,sem,grade,ev))
# GetSize funcs (v[12] B8 imm32 C3, double-point closed)
GS={'0041C170':'AircraftClass::GetSize=0x6D8','00459E70':'BuildingClass::GetSize=0x720',
    '005232F0':'InfantryClass::GetSize=0x6F0','00746DD0':'UnitClass::GetSize=0x8E8',
    '004D27C0':'FoggedObjectClass::GetSize=0x78'}
for a,sem in GS.items():
    ev='EVIDENCE/t3_getsize_final.txt;EVIDENCE/t3_getsize_closure.txt;EVIDENCE/t3_getsize_raw.txt'
    if a in coverage:
        cur=coverage[a]
        P('  %s GetSize in coverage cur=%s -> upgrade'%(a,cur['grade']))
        rows.append((a,'S10',cur['name'] if not cur['name'].startswith('sub_') else sem.split('::')[0]+'::GetSize',sem,'[已证]',ev))
    else:
        P('  %s GetSize NOT in coverage -> new row'%a)
        rows.append((a,'S10',sem.split('::')[0]+'::GetSize',sem,'[已证]',ev))

# Filter: delta contains only genuine changes (upgrade from non-[已证] or new entry).
# Already-[已证] handlers are reaffirmed in EVIDENCE/t2_final_slots.txt, not re-listed.
change_rows=[]
for r in rows:
    key=r[0].upper()
    if key not in coverage or coverage[key]['grade']!='[已证]':
        change_rows.append(r)
P('\nreaffirmed (already [已证], kept only in EVIDENCE): %d'%(len(rows)-len(change_rows)))
rows=change_rows
with open(os.path.join(OUT,'coverage_delta.tsv'),'w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t',lineterminator='\n')
    w.writerows(rows)
P('\ntotal delta rows (changes only): %d'%len(rows))
up=sum(1 for r in rows if r[0].upper() in coverage and coverage[r[0].upper()]['grade']!='[已证]')
new=sum(1 for r in rows if r[0].upper() not in coverage)
P('  upgrades from non-[已证]: %d ; new entries: %d'%(up,new))
with open(os.path.join(EVID,'coverage_delta_report.txt'),'w',encoding='utf-8') as f: f.write('\n'.join(L)+'\n')
