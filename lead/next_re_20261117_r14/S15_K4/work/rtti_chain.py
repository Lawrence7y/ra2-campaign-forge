#!/usr/bin/env python3
"""S15-K4 channel 1: vtable init-chain + RTTI class recovery.
Implements C7 05 <obj><vt> (and register-relative variants) -> vtable[-1] -> COL -> TD+8 (COL+0xC -> TD)."""
import pathlib,struct,collections,re,bisect
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM, CS_OP_MEM
ROOT=pathlib.Path(r'D:\Project\ra2-campaign-forge'); EXE=ROOT/'ra2youli/gamemd.exe'
OUT=pathlib.Path(__file__).resolve().parents[1]/'EVIDENCE'
pe=pefile.PE(str(EXE)); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    secs.append((s.Name.rstrip(b'\0').decode('latin1'),IB+s.VirtualAddress,max(s.Misc_VirtualSize,s.SizeOfRawData)))
def sec(va):
    for n,a,z in secs:
        if a<=va<a+z:return n
    return '?'
def rd(va,n):
    try:return pe.get_data(va-IB,n)
    except:return b''
def u32(va):
    b=rd(va,4);return struct.unpack('<I',b)[0] if len(b)==4 else None
def cstr(va,n=120):
    b=rd(va,n);o=bytearray()
    for c in b:
        if c==0:break
        if 32<=c<127:o.append(c)
        else:break
    return o.decode('ascii','replace')
def rtti_name(vt):
    col=u32(vt-4)
    if col is None or sec(col)!='.rdata':return None,None
    td=u32(col+0xC)
    if td is None or sec(td)!='.rdata':return None,col
    nmva=u32(td+8)
    nm=cstr(nmva) if nmva else ''
    m=re.match(r'^\.\?AV(.+)@@$',nm)
    return (m.group(1) if m else (nm or None)),col
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
tsec=[s for s in secs if s[0]=='.text'][0]
code=pe.get_data(tsec[1]-IB,tsec[2])
ins=list(md.disasm(code,tsec[1]))
vt_classes={}
abs_writes=[]
reg_writes=[]
for i in ins:
    if i.mnemonic!='mov' or len(i.operands)!=2:continue
    op0,op1=i.operands
    if op1.type!=CS_OP_IMM:continue
    vt=op1.imm&0xffffffff
    if sec(vt)!='.rdata':continue
    if op0.type==CS_OP_MEM and op0.mem.base==0 and op0.mem.index==0:
        obj=op0.mem.disp&0xffffffff
        nm,col=rtti_name(vt)
        if nm:
            abs_writes.append((i.address,obj,vt,nm,col))
            vt_classes.setdefault(vt,nm)
    elif op0.type==CS_OP_MEM and op0.mem.base!=0 and op0.mem.disp is not None:
        nm,col=rtti_name(vt)
        if nm:
            reg_writes.append((i.address,i.op_str,vt,nm,col))
            vt_classes.setdefault(vt,nm)
lines=['S15-K4 vtable initialization chain + RTTI recovery (capstone skipdata=True)']
lines.append('绝对 C7-05-form writes with valid RTTI=%d; register-relative vptr writes with valid RTTI=%d; distinct vtables=%d'%(len(abs_writes),len(reg_writes),len(vt_classes)))
lines.append('\n[TActionClass size anchor]')
for a in (0x6E4630,0x71FA50,0x726930,0x6E5890,0x6E64A0,0x727CB0):
    b=rd(a,5)
    lines.append('  %08X bytes=%s imm=%s name=%s'%(a,b.hex(),struct.unpack('<I',b[1:5])[0] if len(b)==5 and b[0]==0xB8 and b[-1]==0xC3 else '-',''))
lines.append('\n[absolute C7 05 writes, sample/all if <=200]')
for w in abs_writes[:200]:lines.append('  site=%08X obj=%08X vt=%08X COL=%s class=%s'%w)
lines.append('\n[register-relative vptr writes whose class is one of S15 trigger types]')
keep=('TActionClass','TEventClass','TagClass','TagTypeClass','TriggerClass','TriggerTypeClass')
for w in reg_writes:
    if w[3] in keep:lines.append('  site=%08X %-30s vt=%08X COL=%08X class=%s'%(w[0],w[1],w[2],w[4] or 0,w[3]))
lines.append('\n[targets and their direct callees: vptr writes / class evidence]')
TARGETS=['006D0F00','006D6070','006E1830','006E2A10','006E2AA0','006E4790','006E47C0','006E6310','006EA3E0','006F1920','0070F120','0071FA30','00721270','00726910','00727AA0','0072DDB0','0072DEF0','00751590','00752460','00763610','00763690']
byaddr={i.address:i for i in ins}
for t in TARGETS:
    va=int(t,16); start=bisect.bisect_right([i.address for i in ins],va)-1
    # disassemble 256 bytes from target for callees
    body=list(md.disasm(rd(va,512),va))
    callees=[]
    for i in body:
        if i.mnemonic=='call' and len(i.operands) and i.operands[0].type==CS_OP_IMM:callees.append(i.operands[0].imm&0xffffffff)
    evid=[]
    for dest in callees:
        cb=list(md.disasm(rd(dest,512),dest))
        for j in cb:
            if j.mnemonic!='mov' or len(j.operands)!=2 or j.operands[1].type!=CS_OP_IMM:continue
            vt=j.operands[1].imm&0xffffffff
            if vt in vt_classes:evid.append((dest,j.address,vt,vt_classes[vt]))
    lines.append('  %s callees=%s class_vptr_writes=%s'%(t,' '.join('%08X'%x for x in callees),evid or 'NONE'))
(OUT/'rtti_init_chain.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines[:14]))
print('WROTE',OUT/'rtti_init_chain.txt')
