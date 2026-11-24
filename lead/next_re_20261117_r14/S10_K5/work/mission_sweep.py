#!/usr/bin/env python3
"""Mission RTTI/vtable sweep + scalar-deleting-dtor detector (independent of atlas sizes)."""
import re,struct,csv,sys
from pathlib import Path
from re_lib import *
ROOT=Path(r'D:\Project\ra2-campaign-forge')
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
DELETE=0x7C8B3D

def is_code(va):
    for s in PE.sections:
        b=PE.OPTIONAL_HEADER.ImageBase+s.VirtualAddress
        if b<=va<b+max(s.Misc_VirtualSize,s.SizeOfRawData) and (s.Characteristics & 0x20):
            return True
    return False

def data_sections():
    for s in PE.sections:
        if not (s.Characteristics & 0x40000040): continue
        base=PE.OPTIONAL_HEADER.ImageBase+s.VirtualAddress
        n=min(s.SizeOfRawData,s.Misc_VirtualSize or s.SizeOfRawData)
        if n<=0 or s.PointerToRawData<=0: continue
        yield base,read(base,n)

def tds_with_substr(sub):
    res={}
    pat=re.compile(rb'\.\?AV[A-Za-z0-9_@\?\$]{1,160}@@')
    for base,data in data_sections():
        for m in pat.finditer(data):
            nm=m.group().decode('latin1')
            if sub.lower() not in nm.lower(): continue
            td=base+m.start()-8
            try:
                if cstr(td+8,200)==nm: res[td]=nm
            except Exception: pass
    return res

def dword_refs(values):
    valset=set(values); hits={v:[] for v in values}
    for base,data in data_sections():
        for j in range(0,len(data)-3,4):
            v=struct.unpack_from('<I',data,j)[0]
            if v in valset: hits[v].append(base+j)
    return hits

def cols_for(tds):
    refs=dword_refs(tds.keys()); out={}
    for td,hits in refs.items():
        arr=[]
        for h in hits:
            col=h-12
            try: r=rtti_from_col(col)
            except Exception: continue
            if r and r[0]==td and col not in arr: arr.append(col)
        out[td]=arr
    return out

def vtables_for(cols):
    refs=dword_refs(cols); out={}
    for col,hits in refs.items():
        arr=[]
        for h in hits:
            vb=h+4; slots=[]
            for i in range(2048):
                try: f=u32(vb+4*i)
                except Exception: break
                if not is_code(f): break
                slots.append(f)
            arr.append((vb,slots))
        out[col]=arr
    return out

RE_TEST=re.compile(r'test byte ptr \[esp \+ (?:0x)?([0-9a-f]+)\], 1')
RE_DELETE=re.compile(r'\bcall 0x7c8b3d\b')
RE_RET4=re.compile(r'\bret 4$')
RE_CALL=re.compile(r'\bcall 0x([0-9a-f]+)\b')

def features(va):
    ins=disasm(va,count=300,stop_ret=False,max_bytes=6144)
    lines=[fmt_insn(i) for i in ins]
    test=[]; dele=[]; ret4=[]; calls=[]
    for line in lines:
        a=int(line.split()[0],16)
        if RE_TEST.search(line): test.append((a,line))
        if RE_DELETE.search(line): dele.append((a,line))
        if RE_RET4.search(line): ret4.append((a,line))
        m=RE_CALL.search(line)
        if m: calls.append((a,int(m.group(1),16),line))
    taddr=test[0][0] if test else None
    before=[x for x in calls if taddr and x[0]<taddr and x[1]!=DELETE]
    after=[x for x in calls if taddr and x[0]>taddr and x[1]==DELETE]
    strong=bool(test and dele and ret4 and before and after)
    return strong,dict(test=test[:3],dele=dele[:3],ret4=ret4[:3],before=before[:3],after=after[:3],lines=lines)

rows={}
with COV.open('r',encoding='utf-8',newline='') as fh:
    for r in csv.DictReader(fh,delimiter='\t'):
        rows[r['entry'].strip().lower()]=r

print('=== MISSION RTTI ===')
tds=tds_with_substr('mission')
for td,n in sorted(tds.items()): print(f'TD 0x{td:08X} {n}')
cols=cols_for(tds)
print('\n=== MISSION COLS ===')
for td,arr in sorted(cols.items()):
    print(f'{tds[td]} TD=0x{td:08X} COLS=' + ','.join(f'0x{x:08X}' for x in sorted(arr)))
vts=vtables_for([c for arr in cols.values() for c in arr])

print('\n=== MISSION VTABLES / DELETE SIGNATURE ===')
hits=[]
for td,arr in sorted(cols.items()):
    for col in arr:
        for vb,slots in sorted(vts.get(col,[])):
            print(f'CLASS={tds[td]} TD=0x{td:08X} COL=0x{col:08X} VBASE=0x{vb:08X} SLOTS={len(slots)}')
            for i,f in enumerate(slots):
                strong,feat=features(f)
                if strong:
                    row=rows.get(f'{f:08x}')
                    print(f'  HIT slot={i} func=0x{f:08X} grade={row["grade"] if row else "NO_ROW"} name={row["name"] if row else "-"}')
                    for k in ['test','dele','ret4','before']:
                        print('    '+k+'='+str([x[1] if len(x)>1 and isinstance(x[1],str) else x for x in feat[k][:2]]))
                    hits.append((tds[td],col,vb,i,f,row))
print('TOTAL_MISSION_DELETE_HITS='+str(len(hits)))

print('\n=== S10 NONPROVED DELETE SIGNATURE (all rows) ===')
n=0
for e,r in sorted(rows.items()):
    if r['subsystem'].strip().upper()!='S10' or r['grade'].strip()=='[已证]': continue
    va=int(e,16); strong,feat=features(va)
    if strong:
        n+=1
        print(f'0x{va:08X} {r["grade"]} {r["name"]} test={feat["test"][:1]} delete={feat["dele"][:1]} ret={feat["ret4"][:1]}')
print('S10_NONPROVED_DELETE_SIGNATURE_COUNT='+str(n))
