"""
S10-K2 T2-core: fresh RTTI enumeration for Mission-related classes + vtable delim from .rdata.
No function_atlas for discovery. capstone skipdata=True. Class name ONLY from COL+0xC -> TD+8.
Reads .rdata for TD/COL/vtable; delimits slots by COL/SEP/non-code boundary (discipline 7).
Outputs EVIDENCE/t2_rtti_vtables.txt and JSON.
"""
import re, json, struct, os
from pehelp import (IMAGE_BASE, rd, u32, u16, u8, sections, section_of, in_section,
                    is_code, disasm, fmt, MD)

OUT = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10-K2'
EVID = os.path.join(OUT, 'EVIDENCE')
L=[]
def P(s=''):
    L.append(str(s)); print(s)

SEC_RANGES=[(nm, IMAGE_BASE+vaoff, IMAGE_BASE+vaoff+max(vsize,rsize))
            for nm,vaoff,vsize,rsize,praw in sections()]

def read_cstr(va, maxb=128):
    b=rd(va,maxb); z=b.find(b'\x00')
    if z<0: return None
    try: return b[:z].decode('latin1')
    except: return None

# ---- 1) Enumerate ALL TypeDescriptors in .rdata/.data ----
# TD layout: [vfptr][spare=0][name cstr at +8]
# name like .?AVMissionClass@@  / .?AUMissionClass@@
P('===== T2-CORE RTTI ENUMERATION (fresh, class name from TD+8 only) =====')
pat = re.compile(rb'\.\?A[UV][A-Za-z0-9_]+@@\x00')
td={}   # td_va -> name
for nm,lo,hi in SEC_RANGES:
    if nm not in ('.rdata','.data'): continue
    blob=rd(lo,hi-lo)
    for m in pat.finditer(blob):
        nav=lo+m.start()
        t=nav-8   # TD base = nameptr location - 8
        try:
            vf=u32(t); spare=u32(t+4)
        except: continue
        if in_section(vf,'.rdata') and spare==0:
            nmv=read_cstr(t+8)
            if nmv and nmv.endswith('@@') and len(nmv)>5:
                td[t]=nmv
P('all valid TD count = %d' % len(td))

# target classes of interest
KEY=('MissionClass','FootClass','InfantryClass','AircraftClass','BuildingClass',
     'TechnoClass','ObjectClass','AbstractClass','UnitClass','VehicleClass')
key_td={t:n for t,n in td.items() if any(k in n for k in KEY)}
P('\nTDs matching Mission-related keys = %d' % len(key_td))
for t,n in sorted(key_td.items(), key=lambda x:x[1]):
    P('  TD %08X  %s' % (t,n))

# ---- 2) Collect ALL COLs whose TD is in tdset (COL+0xC -> TD) ----
tdset=set(td)
cols=[]  # (col,td,off,cdoff,chd)
for nm,lo,hi in SEC_RANGES:
    if nm not in ('.rdata','.data'): continue
    for va in range(lo,hi-0x14+1,4):
        try: v=u32(va+0xC)   # COL+0xC
        except: continue
        if v in tdset:
            sig=u32(va); off=u32(va+4); cdoff=u32(va+8); chk=u32(va+0xC); chd=u32(va+0x10)
            if sig==0:
                cols.append((va,v,off,cdoff,chd))
colset={c[0] for c in cols}
P('\nCOL count (all TDs) = %d' % len(cols))

# map col -> td name
col2td={c[0]: td.get(c[1],'?') for c in cols}

# ---- 3) vtables: vtable[-1]==COL, in .rdata, slot0 is code ----
SEP={0x00004E40,0x399D52A2,0x469D913F}
vts=[]
for nm,lo,hi in SEC_RANGES:
    if nm!='.rdata': continue
    for va in range(lo,hi-4+1,4):
        try: v=u32(va)
        except: continue
        if v in colset:
            vt=va+4
            if section_of(vt)!='.rdata': continue
            try:
                if not is_code(u32(vt)): continue
            except: continue
            col=v
            tdv=[c[1] for c in cols if c[0]==col][0]
            off=[c[2] for c in cols if c[0]==col][0]
            vts.append((vt,col,tdv,off,td.get(tdv,'?')))

def count_slots(vt,maxn=300):
    n=0
    for i in range(maxn):
        a=vt+4*i
        if section_of(a)!='.rdata': break
        try: v=u32(a)
        except: break
        if v in colset or v in SEP or not is_code(v): break
        n+=1
    return n

# only vts for target classes
kvts=[x for x in vts if any(k in x[4] for k in KEY)]
P('\nMission-related vtables found = %d' % len(kvts))
for vt,col,tdv,off,name in sorted(kvts):
    n=count_slots(vt); end=vt+4*n
    try: delim=u32(end) if section_of(end)=='.rdata' else None
    except: delim=None
    dtxt=('COL' if delim in colset else ('SEP' if delim in SEP else ('noncode' if delim is not None and not is_code(delim) else (hex(delim) if delim is not None else '?'))))
    P('  %-40s off=%-3d VT=%08X slots=%-3d end=%08X delim=%s COL=%08X TD=%08X' %
      (name,off,vt,n,end,dtxt,col,tdv))

# ---- 4) Dump slots 0..N for primary (off=0) MissionClass vtable and derived ----
P('\n===== PRIMARY VTABLE SLOT DUMP (off=0) for target classes =====')
def dump_slots(vt, n):
    out=[]
    for i in range(n):
        v=u32(vt+4*i)
        ins=disasm(v,16,stop_ret=True)
        dis=(' / '.join('%s %s'%(x.mnemonic,x.op_str) for x in ins[:2])) if ins else '?'
        out.append((i,v,dis))
    return out

# pick one primary vtable per class (off=0)
prim={}
for vt,col,tdv,off,name in kvts:
    if off==0 and name not in prim:
        prim[name]=(vt,count_slots(vt))

for name in sorted(prim):
    vt,n=prim[name]
    P('\n--- %s : VT=%08X slots=%d ---' % (name,vt,n))
    for i,v,dis in dump_slots(vt,n):
        marker=''
        if 129<=i<=156: marker=' <== MISSION RANGE'
        P('  v[%3d] +0x%03X = %08X  %s%s' % (i,4*i,v,dis,marker))

# Save JSON
jout={
 'td_count':len(td), 'col_count':len(cols),
 'key_tds':{'%08X'%t:n for t,n in key_td.items()},
 'kvts':[dict(vt='%08X'%vt,col='%08X'%col,td='%08X'%tdv,off=off,slots=count_slots(vt),name=name)
         for vt,col,tdv,off,name in kvts],
}
with open(os.path.join(EVID,'t2_rtti_vtables.json'),'w') as f: json.dump(jout,f,indent=2)
with open(os.path.join(EVID,'t2_rtti_vtables.txt'),'w',encoding='utf-8') as f: f.write('\n'.join(L)+'\n')
print('\nWROTE t2_rtti_vtables.txt/.json')
