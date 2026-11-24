"""Categorize all 41 S05 A-set rows by ③b tier / holder count / site count for UNKNOWNS."""
import sys, os, json, csv
sys.path.insert(0, os.path.dirname(__file__))
from pe_helpers import *
from capstone import *
from capstone.x86 import *
import pickle

MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True; MD.skipdata=True
CFG=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED2\work\cfg_features.json"))
HOLD=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED2\work\rtti_holders.json"))
D=pickle.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED2\work\call_sites.pkl",'rb'))
call_sites=D['call_sites']

SELECTED={'00413F80','006F4AB0','006F6AC0','0070C270','007077C0','00716DC0','007162F0','00700600'}

out=[]
for k,x in CFG.items():
    f=x['features']
    body=[[int(off.replace('+0x',''),16)+int(k,16),m,o] for off,m,o,hx in x['body']]
    jt=any(m=='jmp' and 'dword ptr' in o and '*' in o for a,m,o in body)
    err=any(m=='cmp' and o.strip().endswith('-1') for a,m,o in body)
    back=any(m.startswith('j') and m!='jmp' and o.startswith('0x') and int(o,16)<=a for a,m,o in body)
    io=any(m.startswith('call') for a,m,o in body)
    vtw=sum(1 for a,m,o in body if m=='mov' and 'dword ptr' in o and ('0x7e' in o or '0x7f' in o))
    guard_tgts=[int(o,16) for a,m,o in body if m.startswith('j') and m!='jmp' and o.startswith('0x')]
    gc = len(guard_tgts)>=3 and len(set(guard_tgts))>=3
    strict=jt or err or (back and io and len(body)>=20) or vtw>=2
    loose=strict or gc
    nh=len(HOLD[k]); nd=len(call_sites.get(int(k,16),[]))
    status = 'SELECTED' if k in SELECTED else ('③b-strict(backlog)' if strict else ('③b-loose-only(细则#1)' if loose else '③a-no③b'))
    out.append(dict(entry=k,name=x['name'],nins=x['nins'],holders=nh,dir=nd,
                    jt=jt,err=err,back=back,vtw=vtw,guardchain=gc,strict=strict,loose=loose,status=status))

json.dump(out,open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED2\work\categorize.json",'w'),indent=1)
print(f"{'entry':8} {'nins':>5} {'hold':>4} {'dir':>3} jt err bk gc strict loose status")
for r in sorted(out,key=lambda z:z['entry']):
    print(f"{r['entry']:8} {r['nins']:5} {r['holders']:4} {r['dir']:3}  {int(r['jt'])}  {int(r['err'])} {int(r['back'])} {int(r['guardchain'])}   {int(r['strict'])}    {int(r['loose'])}   {r['status']}")
