"""Categorize the 33 remaining A-set rows (41 minus 8 merged by S05_KPROVED2).
Report holder count, classes, ③b strict/loose features, direct sites.
Card S05-KPROVED3."""
import sys, os, json, pickle
sys.path.insert(0, os.path.dirname(__file__))
from pe_helpers import *

CFG=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\cfg_features.json"))
HOLD=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\rtti_holders.json"))
D=pickle.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\call_sites.pkl",'rb'))
call_sites=D['call_sites']

MERGED={'00413F80','006F4AB0','006F6AC0','0070C270','007077C0','00716DC0','007162F0','00700600'}

out=[]
for k,x in sorted(CFG.items()):
    if k in MERGED: continue
    f=x['features']
    body=[[int(off.replace('+0x',''),16)+int(k,16),m,o] for off,m,o,hx in x['body']]
    jt=any(m=='jmp' and 'dword ptr' in o and '*' in o for a,m,o in body)
    err=any(m=='cmp' and o.strip().endswith('-1') for a,m,o in body)
    back=any(m.startswith('j') and m!='jmp' and o.startswith('0x') and int(o,16)<=a for a,m,o in body)
    io=any(m.startswith('call') for a,m,o in body)
    ioloop=back and io and len(body)>=20
    vtw=sum(1 for a,m,o in body if m=='mov' and 'dword ptr' in o and ('0x7e' in o or '0x7f' in o))
    memshape=vtw>=2
    wr=len(f.get('memwrites',[]))
    guard_tgts=[int(o,16) for a,m,o in body if m.startswith('j') and m!='jmp' and o.startswith('0x')]
    gc=len(guard_tgts)>=3 and len(set(guard_tgts))>=3
    strict=jt or err or ioloop or memshape
    loose=strict or gc
    hs=HOLD.get(k,[])
    classes=sorted(set(h['name'] for h in hs))
    slots=sorted(set(h['slot'] for h in hs))
    nd=len(call_sites.get(int(k,16),[]))
    out.append(dict(entry=k,name=x['name'],nins=x['nins'],holders=len(hs),classes=classes,slots=slots,
                    dir=nd,jt=jt,err=err,back=back,ioloop=ioloop,memshape=memshape,wr=wr,
                    guardchain=gc,strict=strict,loose=loose))

json.dump(out,open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\categorize_remaining.json",'w'),indent=1)
print(f"{'entry':8} {'nins':>5} {'hold':>4} {'dir':>3} {'wr':>4} {'bk':>2} {'err':>3} {'gc':>2} {'jt':>2} {'str':>3} {'loo':>3}  name / classes")
for r in sorted(out,key=lambda z:z['entry']):
    flag='STRICT' if r['strict'] else ('LOOSE' if r['loose'] else '③a')
    print(f"{r['entry']:8} {r['nins']:5} {r['holders']:4} {r['dir']:3} {r['wr']:4} {int(r['back']):2} {int(r['err']):3} {int(r['guardchain']):2} {int(r['jt']):2} {int(r['strict']):3} {int(r['loose']):3}  {flag:6} {r['name']}")
    if r['holders']>1:
        for c in r['classes'][:6]:
            print(f"         class: {c}")
