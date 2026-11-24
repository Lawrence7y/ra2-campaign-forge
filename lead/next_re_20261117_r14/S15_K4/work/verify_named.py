#!/usr/bin/env python3
"""S15-K4 focused verification for the two new names.

All outputs are untruncated. capstone skipdata=True throughout.
"""
from __future__ import annotations
import bisect, csv, hashlib, pathlib, re, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM, CS_OP_MEM, x86_const

ROOT=pathlib.Path(r'D:\Project\ra2-campaign-forge')
EXE=ROOT/'ra2youli/gamemd.exe'
ATLAS=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
OUT=pathlib.Path(__file__).resolve().parents[1]/'EVIDENCE'
DEEP=ROOT/'docs/re/trigger_tag_abi_deep_dive.md'
GOAL=ROOT/'lead/GOAL_THREE_TARGETS_20261018.md'

pe=pefile.PE(str(EXE)); IB=pe.OPTIONAL_HEADER.ImageBase
def rd(va,n):
    try:return pe.get_data(va-IB,n)
    except Exception:return b''
def u32(va):
    b=rd(va,4);return struct.unpack('<I',b)[0] if len(b)==4 else None
def cstr(va,n=100):
    b=rd(va,n);o=bytearray()
    for c in b:
        if c==0:break
        if 32<=c<127:o.append(c)
        else:break
    return o.decode('ascii','replace')
def sec(va):
    for s in pe.sections:
        a=IB+s.VirtualAddress; z=max(s.Misc_VirtualSize,s.SizeOfRawData)
        if a<=va<a+z:return s.Name.rstrip(b'\0').decode('latin1')
    return '?'
def rtti(vt):
    col=u32(vt-4); td=u32(col+0xC) if col else None
    nm=cstr(td+8) if td else ''
    return col,td,nm
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
tsec=[s for s in pe.sections if s.Name.rstrip(b'\0').decode()=='.text'][0]
tbase=IB+tsec.VirtualAddress; tsize=max(tsec.Misc_VirtualSize,tsec.SizeOfRawData)
ins=list(md.disasm(pe.get_data(tbase-IB,tsize),tbase))
byaddr={i.address:i for i in ins}; ends={i.address+i.size for i in ins}
def tsv(p):
    with p.open('r',encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
atlas=tsv(ATLAS); cov={r['entry'].upper():r for r in tsv(COV)}
ints=sorted((int(r['entry'],16),int(r['size'],0),r) for r in atlas); starts=[x[0] for x in ints]
def owner(va):
    k=bisect.bisect_right(starts,va)-1
    if k>=0 and va<ints[k][0]+ints[k][1]:return ints[k]
    return None
def covname(va):
    r=cov.get('%08X'%(va&0xffffffff)); return r['name'] if r else '<none>'
def fmt(i):
    ann=''
    try:
        ops=i.operands
    except Exception:
        ops=[]
    if len(ops) and ops[0].type==CS_OP_IMM:
        t=ops[0].imm&0xffffffff
        if ('%08X'%t) in cov: ann=' ; '+covname(t)
    return '%08X  %-18s %-7s %s%s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str,ann)
L=[]; A=L.append
sha=hashlib.sha256(EXE.read_bytes()).hexdigest().upper()
A('S15-K4 focused verification - two new names')
A('target: %s  bytes=%d  sha256=%s  ImageBase=%08X'%(EXE,EXE.stat().st_size,sha,IB))
A('.text linear sweep skipdata=True: %d instructions / %d bytes'%(len(ins),tsize))
A('')
A('== 1. Target entry bytes and instruction boundaries ==')
for va,expect in [(0x71FA30,'8b4154c3'),(0x726910,'8b412cc3')]:
    b=rd(va,8); prev=rd(va-8,8)
    A('%08X bytes[0:8]=%s expected-prefix=%s prev8=%s sweep_entry=%s prev_insn_ends_here=%s cov=%s'%(
        va,b.hex(),expect,prev.hex(),va in byaddr,(va in ends),covname(va)))
    A('  bytes[0:4]==%s : %s'%(expect,b[:4].hex()==expect))
    for i in md.disasm(b[:8],va): A('  '+fmt(i))
A('')
A('== 2. Corrected static vtable init chain: vtable[-1] -> COL -> COL+0xC -> TD -> TD+8 INLINE name ==')
for vt,who in [(0x7F5578,'TEventClass vtable installed by ctor 0x71E6A0'),(0x7F5858,'TriggerClass vtable installed by ctor 0x725FA0')]:
    col,td,nm=rtti(vt)
    A('%s: vt=%08X col=%08X td=%08X TD+8=%r sec(col)=%s sec(td)=%s'%(who,vt,col or 0,td or 0,nm,sec(col) if col else '?',sec(td) if td else '?'))
A('vptr-write sites from EVIDENCE/vtable_rtti_fixed.txt (independent full-sweep replay):')
for line in (OUT/'vtable_rtti_fixed.txt').read_text(encoding='utf-8').splitlines():
    if re.search(r'\s(cls=TEventClass|cls=TriggerClass)\s',line) and ('fn=0071E6A0' in line or 'fn=00725FA0' in line):
        A('  '+line.strip())
A('')
A('== 3. Source-symbol channel (YRpp headers + project ABI doc) ==')
for rel,needles in [
    ('YRpp/TEventClass.h',['TEventClass','int               indexInArray','HouseClass*       House;']),
    ('YRpp/TriggerClass.h',['HouseClass* GetHouse() const','return this->House;','HouseClass*\t\t\tHouse;']),
]:
    lines=(ROOT/rel).read_text(encoding='utf-8').splitlines()
    for n in needles:
        hits=[(i+1,l.strip()) for i,l in enumerate(lines) if n in l]
        A('%s %r -> %s'%(rel,n,hits[:4] or 'NO HIT'))
dlines=DEEP.read_text(encoding='utf-8').splitlines()
for n in ['GetHouse 0x726910','GetHouse / SetHouse']:
    A('docs/re/trigger_tag_abi_deep_dive.md %r -> %s'%(n,[(i+1,l.strip()) for i,l in enumerate(dlines) if n in l][:4] or 'NO HIT'))
A('GOAL_THREE_TARGETS pre-write grep: TEventClass::GetHouse=%s TriggerClass::GetHouse=%s'%(
    'TEventClass::GetHouse' in GOAL.read_text(encoding='utf-8'),
    'TriggerClass::GetHouse' in GOAL.read_text(encoding='utf-8')))
A('')
A('== 4. Field write/read double support ==')
A('TEventClass +0x54: ctor 0x71E6BE bytes=%s ; getter 0x71FA30 bytes=%s'%(rd(0x71E6BE,4).hex(),rd(0x71FA30,4).hex()))
for a,n in ((0x71E6BE,3),(0x71FA30,4)):
    for i in md.disasm(rd(a,n),a): A('  '+fmt(i))
A('TriggerClass +0x2C: ctor 0x725FB5 bytes=%s ; getter 0x726910 bytes=%s'%(rd(0x725FB5,4).hex(),rd(0x726910,4).hex()))
for a,n in ((0x725FB5,3),(0x726910,4)):
    for i in md.disasm(rd(a,n),a): A('  '+fmt(i))
A('')
A('== 5. thiscall ecx provenance ==')
A('0x71FA30: both xrefs are inside consumer 0x7264C0; same ecx=edi is passed to TEventClass::HasOccured first.')
for i in md.disasm(rd(0x726538,0x30),0x726538): A('  '+fmt(i))
A('=> ecx for 0x71FA30 is the same TEventClass* used for TEventClass::HasOccured.')
A('')
A('0x726910: callers are TActionClass action bodies; ecx is read from [esp+N] before later pushes.')
A('stack-arg discipline: original [esp+0xC] = 3rd stack arg = TriggerClass* pTrigger (YRpp TActionClass.h:57).')
for site in (0x6E0AB8,0x6E0B7B,0x6E0CB7,0x6E0D17):
    ow=owner(site)
    if not ow: A('  site %08X <no atlas interval>'%site); continue
    st,sz,_=ow
    body=list(md.disasm(rd(st,sz),st)); idx=next(k for k,i in enumerate(body) if i.address==site)
    found=None
    for j in range(idx-1,max(-1,idx-12),-1):
        i=body[j]
        if i.mnemonic=='mov' and len(i.operands)==2 and i.operands[0].type==x86_const.X86_OP_REG and i.operands[0].reg==x86_const.X86_REG_ECX and i.operands[1].type==CS_OP_MEM and i.operands[1].mem.base==x86_const.X86_REG_ESP:
            found=(i,j,int(i.operands[1].mem.disp)); break
    if found:
        i,j,d=found; pushes=sum(1 for k in range(0,j) if body[k].mnemonic=='push'); orig=d-4*pushes
        A('  site %08X owner=%08X ecx-read @%08X %s pushes_before=%d disp=0x%X -> original [esp+0x%X]=0x%X expected 0xC : %s'%(
            site,st,i.address,fmt(i).strip(),pushes,d,orig,orig,'PASS' if orig==0xC else 'FAIL'))
    else:
        A('  site %08X ecx-read NOT FOUND in preceding 12 instructions'%site)
A('')
(OUT/'verify_named_k4.txt').write_text('\n'.join(L)+'\n',encoding='utf-8')
print('WROTE',OUT/'verify_named_k4.txt','lines',len(L))
print('\n'.join(L[:8]))
