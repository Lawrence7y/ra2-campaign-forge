import json,sys
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10-K2\work')
E=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10-K2\EVIDENCE'
with open(E+r'\t2_mission_slots.json') as f: s=json.load(f)
STUB=set(range(0x5B2E10,0x5B2FC0+1,0x10))
nonstub=set(); total=0; stubcnt=0; stubaddr=set()
for cls,rows in s.items():
    for r in rows:
        a=int(r['addr'],16); total+=1
        if a in STUB: stubcnt+=1; stubaddr.add(a)
        else: nonstub.add(a)
print('classes scanned:', list(s.keys()))
print('7 classes x 28 = total slot entries:', total)
print('stub slot entries:', stubcnt)
print('non-stub slot entries:', total-stubcnt)
print('distinct non-stub addresses:', len(nonstub))
print('distinct stub addresses used:', len(stubaddr))
print('non-stub addrs sorted:')
for a in sorted(nonstub): print('  %08X'%a)
