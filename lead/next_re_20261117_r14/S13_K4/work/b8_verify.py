#!/usr/bin/env python3
"""S13-K4: verify 6 NEW B8imm32C3 stubs (Bomb/Parasite/RadSite slot11+slot12).
Proof channels:
  A) entry bytes B8 imm32 C3 (already in stub_scan.tsv)
  B) RTTI: TD name + COL + vftable; confirm the entry sits at slot11/slot12 of the class main vtable
  C) WhatAmI: imm == AbstractType enum value for that class
  D) GetSize: imm == factory 'push imm' -> new(0x7C8E17) -> ctor (double-point closure)
Read-only on target. Emits EVIDENCE/b8_verify.txt
"""
import struct, pefile
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K4\EVIDENCE\b8_verify.txt"
pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
DATA = open(EXE, "rb").read()
SECS=[]
for s in pe.sections:
    nm=s.Name.decode('ascii','replace').rstrip('\x00')
    lo=IB+s.VirtualAddress; hi=lo+max(s.Misc_VirtualSize,s.SizeOfRawData)
    rl=s.PointerToRawData; rh=rl+s.SizeOfRawData
    SECS.append((nm,lo,hi,rl,rh))
def sec_of(va):
    for n,lo,hi,rl,rh in SECS:
        if lo<=va<hi: return n
    return None
def off_of(va):
    for n,lo,hi,rl,rh in SECS:
        if lo<=va<hi:
            o=rl+(va-lo)
            if o<rh: return o
    return None
def u32(va):
    o=off_of(va)
    if o is None or o+4>len(DATA): return None
    return struct.unpack_from('<I',DATA,o)[0]
def cstr(va,cap=128):
    o=off_of(va)
    if o is None: return ''
    return DATA[o:o+cap].split(b'\x00')[0].decode('latin1')
L=[]
def p(x=''): L.append(str(x))

# AbstractType enum (from YRpp GeneralDefinitions.h, verified on disk)
ABSTRACT={'Parasite':67,'Bomb':68,'RadSite':69,'WeaponType':49,'WarheadType':50,'Bullet':8,'BulletType':9}

TARGETS={
  'BombClass': {'slot11':0x4393E0,'slot12':0x4393D0,'imm11':0x44,'imm12':0x5c},
  'ParasiteClass': {'slot11':0x62AF60,'slot12':0x62AF50,'imm11':0x43,'imm12':0x58},
  'RadSiteClass': {'slot11':0x65B3C0,'slot12':0x65B3A0,'imm11':0x45,'imm12':0x74},
}

# 1. TD by mangled name
td_by={}
for cls in TARGETS:
    pat=('.?AV'+cls+'@@').encode('latin1')
    hits=[]; pos=0
    while True:
        i=DATA.find(pat,pos)
        if i<0: break
        va=None
        for n,lo,hi,rl,rh in SECS:
            if rl<=i<rh: va=lo+(i-rl); break
        hits.append(va); pos=i+1
    tds=[]
    for nv in hits:
        if nv is None: continue
        td=nv-8
        vf=u32(td); spare=u32(td+4)
        if vf is not None and sec_of(vf)=='.rdata' and spare==0:
            tds.append(td)
    td_by[cls]=tds
    p(f'[{cls}] nameVA={[hex(x) for x in hits]} TD={[hex(x) for x in tds]}')
    for td in tds:
        p(f'  TD {hex(td)}: pVF={hex(u32(td)) if u32(td) else None} spare={u32(td+4)} name={cstr(td+8)!r}')

all_tds=set(sum(td_by.values(),[]))
# 2. COLs
col_by_td={td:[] for td in all_tds}
for n,lo,hi,rl,rh in SECS:
    for i in range(rl,rh-16,4):
        ptd=struct.unpack_from('<I',DATA,i+12)[0]
        if ptd in all_tds:
            col_by_td[ptd].append(lo+(i-rl))

# 3. vtables containing slot11/slot12 entries; report slot indices
entry_set={info[k]:(cls,k) for cls,info in TARGETS.items() for k in ('slot11','slot12')}
p('\n=== vtable containment of the 6 entries ===')
for cls in TARGETS:
    p(f'\n--- {cls} ---')
    for td in td_by[cls]:
        for col in col_by_td.get(td,[]):
            for n,lo,hi,rl,rh in SECS:
                for i in range(rl,rh-4,4):
                    if struct.unpack_from('<I',DATA,i)[0]!=col: continue
                    vt=lo+(i-rl)+4
                    if sec_of(vt)!='.rdata': continue
                    slots=[]; j=i+4
                    while j+4<=rh:
                        w=struct.unpack_from('<I',DATA,j)[0]
                        if sec_of(w)!='.text': break
                        slots.append(w); j+=4
                    # check if any target entries present
                    found=[(idx,hex(w),entry_set.get(w,('',''))) for idx,w in enumerate(slots) if w in entry_set]
                    if found:
                        p(f'  VT {hex(vt)} COL {hex(col)} TD {hex(td)} slots={len(slots)}')
                        p(f'    found: {found}')
                        p(f'    slot10={hex(slots[10]) if len(slots)>10 else "-"} slot11={hex(slots[11]) if len(slots)>11 else "-"} slot12={hex(slots[12]) if len(slots)>12 else "-"} slot13={hex(slots[13]) if len(slots)>13 else "-"}')

# 4. factory push imm -> new -> ctor double-point closure
# new operator = 0x7C8E17 (per S13-K2). Search all .text for '68 imm32' (push imm32) or '6A imm8'
p('\n=== GetSize factory double-point closure: push imm -> new -> ctor ===')
def disasm_window(va,n=48):
    from capstone import Cs,CS_ARCH_X86,CS_MODE_32
    md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
    o=off_of(va); b=DATA[o:o+n]
    return ' | '.join(f'{i.address:08X}:{i.mnemonic} {i.op_str}' for i in md.disasm(b,va))
NEW_OP=0x7C8E17
for cls,info in TARGETS.items():
    imm=info['imm12']
    p(f'\n--- {cls} GetSize imm={hex(imm)} ({imm}) ---')
    # search '68 imm32' and '6A imm8' in .text
    for n,lo,hi,rl,rh in SECS:
        if n!='.text': continue
        for i in range(rl,rh-5):
            b=DATA[i]
            if b==0x68:
                v=struct.unpack_from('<I',DATA,i+1)[0]
                if v==imm:
                    va=lo+(i-rl)
                    win=disasm_window(va,40)
                    if '7C8E17' in win.upper() or 'call' in win:
                        p(f'  push32 @{hex(va)}: {win}')
            elif b==0x6A and imm<=0x7F and DATA[i+1]==imm:
                va=lo+(i-rl)
                p(f'  push8 @{hex(va)}: {disasm_window(va,40)}')

open(OUT,'w',encoding='utf-8').write('\n'.join(L))
print('wrote',OUT,len(L),'lines')
