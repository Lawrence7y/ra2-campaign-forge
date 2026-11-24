#!/usr/bin/env python3
"""Mission RTTI/vtable sweep and scalar-deleting-dtor feature detector."""
import re,struct,sys,csv
from pathlib import Path
from re_lib import *

ROOT=Path(r'D:\Project\ra2-campaign-forge')
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
DELETE=0x7C8B3D

def code_section(va):
    for s in PE.sections:
        b=PE.OPTIONAL_HEADER.ImageBase+s.VirtualAddress
        if b<=va<b+max(s.Misc_VirtualSize,s.SizeOfRawData) and (s.Characteristics & 0x20):
            return s.Name.decode('latin1').rstrip('\0')
    return None

def all_tds():
    res={}
    for s in PE.sections:
        if not (s.Characteristics & 0x40000040): continue
        base=PE.OPTIONAL_HEADER.ImageBase+s.VirtualAddress
        n=min(s.SizeOfRawData,s.Misc_VirtualSize or s.SizeOfRawData)
        data=read(base,n)
        for m in re.finditer(rb'\.\?AV[A-Za-z0-9_@\?\$]{1,120}@@',data):
            va=base+m.start(); td=va-8
            try:
                name=cstr(td+8,160)
                if name==m.group().decode('latin1'): res[td]=name
            except Exception: pass
    return res

def cols_for_td(td):
    out=[]
    for col in find_rdata_dword_refs(td):
        r=rtti_from_col(col)
        if r and r[0]==td: out.append(col)
    return out

def vtables_for_col(col):
    out=[]
    for ref in find_rdata_dword_refs(col):
        vbase=ref+4
        slots=[]
        for i in range(1024):
            try: f=u32(vbase+4*i)
            except Exception: break
            if not code_section(f): break
            slots.append(f)
        out.append((vbase,slots))
    return out

def features(va):
    try: ins=disasm(va,count=240,stop_ret=False,max_bytes=4096)
    except Exception: return None
    txt=[fmt_insn(i) for i in ins]
    test=[x for x in txt if re.search(r'test byte ptr \[esp \+ 0x?[0-9a-f]+\], 1',x)]
    dele=[x for x in txt if re.search(r'call 0x7c8b3d',x)]
    ret4=[x for x in txt if re.search(r'\tret 4',x) or re.search(r'  ret 4$',x)]
    calls=[x for x in txt if re.search(r'\tcall ',x) or re.search(r'  call ',x)]
    vptrs=[x for x in txt if re.search(r'mov dword ptr \[esi(?:\+0x[0-9a-f]+)?\], 0x7e',x)]
    firstret=None
    for j,x in enumerate(txt):
        if re.search(r'\bret(?: 4)?$',x): firstret=(j,x); break
    return dict(test=test,dele=dele,ret4=ret4,calls=calls,vptrs=vptrs,firstret=firstret,all=txt)

def check_entry(va):
    f=features(va)
    if not f: return False,{}
    ok=bool(f['test'] and f['dele'] and f['ret4'])
    # Require base-destructor-like call before test and delete call after test
    test_addr=int(f['test'][0].split()[0],16) if f['test'] else None
    call_before=[]
    call_after=[]
    for x in f['calls']:
        a=int(x.split()[0],16)
        if test_addr and a<test_addr and '0x7c8b3d' not in x: call_before.append(x)
        if test_addr and a>test_addr and '0x7c8b3d' in x: call_after.append(x)
    strong=ok and bool(call_before and call_after)
    return strong,{k:f[k] for k in ['test','dele','ret4','calls','vptrs','firstret']}

# coverage row index
rows={}
with COV.open('r',encoding='utf-8',newline='') as fh:
    for r in csv.DictReader(fh,delimiter='\t'):
        rows[r['entry'].strip().lower()]=r

print('=== SUPPORT TARGETS ===')
for va in [0x005F3900,0x005F3B80,0x007C8B3D]:
    print(f'--- {va:08X} ---')
    print(fmt_block(va,count=100,stop_ret=True,max_bytes=2048))

print('\n=== MISSION-LIKE TYPE DESCRIPTORS ===')
tds=all_tds()
mission_tds={td:n for td,n in tds.items() if 'mission' in n.lower()}
for td,n in sorted(mission_tds.items()): print(f'TD 0x{td:08X} {n}')

print('\n=== MISSION COL/VTABLE SLOTS WITH DELETE SIGNATURE ===')
all_hits=[]
for td,n in sorted(mission_tds.items()):
    for col in cols_for_td(td):
        for vb,slots in vtables_for_col(col):
            print(f'CLASS={n} TD=0x{td:08X} COL=0x{col:08X} VBASE=0x{vb:08X} SLOTCOUNT={len(slots)}')
            for i,f in enumerate(slots):
                if f in (0,): continue
                strong,feat=check_entry(f)
                if strong:
                    row=rows.get(f'{f:08x}'.lower())
                    print(f'  HIT slot={i} func=0x{f:08X} grade={row["grade"] if row else "NO_COVERAGE_ROW"} name={row["name"] if row else "-"}')
                    print('    test='+str(feat['test'][:2])+' delete='+str(feat['dele'][:2])+' ret='+str(feat['ret4'][:2]))
                    print('    vptrs='+str(feat['vptrs'][:4]))
                    all_hits.append((n,td,col,vb,i,f,row))
print('TOTAL_HITS='+str(len(all_hits)))

print('\n=== ALL S10 NONPROVED DELETE-SIGNATURE ROWS ===')
s10hits=[]
for e,r in sorted(rows.items()):
    if r['subsystem'].strip().upper()!='S10' or r['grade'].strip()=='[已证]': continue
    va=int(e,16)
    strong,feat=check_entry(va)
    if strong:
        print(f'{va:08X} {r["grade"]} {r["name"]} test={feat["test"][:2]} delete={feat["dele"][:2]} ret={feat["ret4"][:2]}')
        s10hits.append((va,r,feat))
print('S10_NONPROVED_DELETE_HITS='+str(len(s10hits)))
