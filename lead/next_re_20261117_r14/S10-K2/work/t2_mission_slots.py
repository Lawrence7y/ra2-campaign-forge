"""
S10-K2 T2: dump mission slots v[129..156] for MissionClass + derived classes;
classify base stubs vs implementations; align with parent vtables slot-by-slot.
Delim vtables from .rdata. capstone skipdata=True. No atlas for discovery.
"""
import json, os
from pehelp import (IMAGE_BASE, rd, u32, sections, section_of, in_section, is_code, disasm, fmt)

OUT = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10-K2'
EVID = os.path.join(OUT,'EVIDENCE')
L=[]
def P(s=''):
    L.append(str(s)); print(s)

# Load vtables from T2 JSON
with open(os.path.join(EVID,'t2_rtti_vtables.json')) as f: j=json.load(f)
kvts=j['kvts']

# Primary off=0 vtable per class; use known good slot counts
# For derived large vtables, maxn needs to be >=157
def count_slots(vt,maxn=400):
    SEP={0x00004E40,0x399D52A2,0x469D913F}
    colset={int(x['col'],16) for x in kvts}
    n=0
    for i in range(maxn):
        a=vt+4*i
        if section_of(a)!='.rdata': break
        try: v=u32(a)
        except: break
        if v in SEP or v in colset or not is_code(v): break
        n+=1
    return n

prim={}
for x in kvts:
    if x['off']==0 and x['name'] not in prim:
        vt=int(x['vt'],16)
        prim[x['name']]={'vt':vt,'n':count_slots(vt)}

P('===== PRIMARY VTABLES (off=0), recounted =====')
for name in sorted(prim):
    P('  %-40s VT=%08X slots=%d' % (name,prim[name]['vt'],prim[name]['n']))

# Determine stub pattern: base stubs are 0x5B2E10..0x5B2FC0 step 0x10B? Let's dump that region.
P('\n===== BASE STUB REGION 0x5B2E10..0x5B3060 (candidate stubs) =====')
for va in range(0x5B2E10,0x5B3060,4):
    # look at every 4 bytes; but stubs likely 267B apart. Instead scan 'mov eax,0x1C2; ret' signature
    pass
# find B8 C2 01 00 00 C3 pattern in .text
def scan_bytes(needle, sec='.text'):
    nm,vaoff,vsize,rsize,praw=[s for s in sections() if s[0]==sec][0]
    lo=IMAGE_BASE+vaoff; hi=lo+min(vsize,rsize)
    blob=rd(lo,hi-lo)
    out=[]
    st=0
    while True:
        k=blob.find(needle,st)
        if k<0: break
        out.append(lo+k); st=k+1
    return out
stub_sites=scan_bytes(b'\xB8\xC2\x01\x00\x00\xC3')
P('B8 C2 01 00 00 C3 (mov eax,0x1C2;ret) sites = %d' % len(stub_sites))
P('  addresses: %s' % ', '.join('%08X'%a for a in stub_sites))
# also B8 imm32 C3 generic near 0x5B2Exx
for a in stub_sites:
    if 0x5B2E00<=a<=0x5B3100:
        P('  in-base-stub-range: %08X  bytes=%s' % (a, rd(a,16).hex()))

# Dump mission slots for each class
MISSION_SLOTS=range(129,157)
all_slots={}
P('\n===== MISSION SLOTS v[129..156] BY CLASS (addr + first 3 insns) =====')
for name in sorted(prim):
    vt=prim[name]['vt']
    if prim[name]['n'] < 157:
        P('\n--- %s VT=%08X slots=%d : NO MISSION RANGE (<157) ---' % (name,vt,prim[name]['n']))
        continue
    P('\n--- %s VT=%08X slots=%d ---' % (name,vt,prim[name]['n']))
    rows=[]
    for i in MISSION_SLOTS:
        a=vt+4*i
        v=u32(a)
        ins=disasm(v,24,stop_ret=True)
        d=' / '.join('%s %s'%(x.mnemonic,x.op_str) for x in ins[:3]) if ins else '?'
        is_stub = (v in stub_sites) or (rd(v,6)==b'\xB8\xC2\x01\x00\x00\xC3')
        rows.append((i,v,d,is_stub))
        P('  v[%3d] +0x%03X = %08X %s %s' % (i,4*i,v,'[STUB]' if is_stub else '      ',d))
    all_slots[name]=rows

with open(os.path.join(EVID,'t2_mission_slots.json'),'w') as f:
    json.dump({n:[dict(slot=i,addr='%08X'%v,dis=d,stub=s) for i,v,d,s in rows]
               for n,rows in all_slots.items()}, f, indent=2)
with open(os.path.join(EVID,'t2_mission_slots.txt'),'w',encoding='utf-8') as f: f.write('\n'.join(L)+'\n')
print('\nWROTE t2_mission_slots.txt/.json')
