# -*- coding: utf-8 -*-
"""NAMED_PUSH_S10_B1 取证脚本：只读 gamemd.exe，全 .text skipdata 线性扫描 +
RTTI/vtable 解析，为 18 个候选逐行收集 D-40 四环锚点。"""
import os, sys, struct, hashlib
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import capstone.x86 as cx86
from capstone.x86 import X86_INS_CALL, X86_INS_JMP, X86_INS_RET, X86_OP_IMM, X86_OP_REG

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
EXE_SHA = '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'
OUT = os.path.dirname(os.path.abspath(__file__))

ENTRIES = [
 ('004D8560','AircraftClass::slot267'),('004D9720','AircraftClass::slot55'),
 ('004D9E70','AircraftClass::slot38'),('004DA1D0','AircraftClass::slot200'),
 ('004DA4E0','AircraftClass::slot26'),('004DE7B0','AircraftClass::slot314'),
 ('004DE940','AircraftClass::slot315'),('004DEBB0','AircraftClass::slot247'),
 ('004DEE80','AircraftClass::slot331'),('004DF7F0','AircraftClass::slot322'),
 ('004DFF40','AircraftClass::slot209'),('00517FA0','InfantryClass::slot91'),
 ('00518F90','InfantryClass::slot69'),('00519630','InfantryClass::slot99'),
 ('0051AA40','InfantryClass::slot288'),('0051BAB0','InfantryClass::slot23'),
 ('0051BF90','InfantryClass::slot107'),('0051C8B0','InfantryClass::slot240'),
]

h = hashlib.sha256(open(EXE,'rb').read()).hexdigest().upper()
assert h == EXE_SHA, h
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
raw = open(EXE,'rb').read()
secs = []
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin1')
    secs.append(dict(nm=nm, va=IB+s.VirtualAddress, vs=s.Misc_VirtualSize,
                     pr=s.PointerToRawData, rs=s.SizeOfRawData))
TEXT = next(s for s in secs if s['nm']=='.text')
TEXT_VA, TEXT_END = TEXT['va'], TEXT['va']+max(TEXT['vs'],TEXT['rs'])
DATA_SECS = [s for s in secs if s['nm'] in ('.rdata','.data')]

def read(va, n):
    for s in secs:
        if s['va'] <= va < s['va']+max(s['vs'],s['rs']):
            off = s['pr']+(va-s['va'])
            return raw[off:off+n]
    return b''
def dword(va):
    b = read(va,4)
    return int.from_bytes(b,'little') if len(b)==4 else None
def in_text(va):
    return TEXT_VA <= va < TEXT_END

# ---------- RTTI/vtable：找含 entry 的虚表并解析类名 ----------
def rtti(vt):
    col = dword(vt-4)
    if col is None or not (0x7e0000 <= col < 0x850000): return None
    td = dword(col+0xC)
    if td is None or not (0x400000 <= td < 0x900000): return None
    s = read(td+8,160).split(b'\x00')[0]
    try: nm = s.decode('latin1')
    except: nm = repr(s)
    return nm if nm.startswith('.?A') else None

def find_vt(entry):
    out=[]; pat=struct.pack('<I',entry)
    for s in DATA_SECS:
        base=s['va']; start=s['pr']; ln=s['rs']
        i=0
        while True:
            j=raw.find(pat,start+i,start+ln-3)
            if j<0: break
            va=base+(j-start)
            # walk back over contiguous .text pointers
            st=va
            while True:
                p=dword(st-4)
                if p is not None and in_text(p): st-=4
                else: break
            en=va+4
            while True:
                nx=dword(en)
                if nx is not None and in_text(nx): en+=4
                else: break
            nm=rtti(st)
            out.append(dict(vt=st, slot=(va-st)//4, name=nm, nslots=(en-st)//4, hitva=va))
            i=j-start+1
    return out

# ---------- 全 .text 线性扫描：direct call/jmp rel32 目标索引 ----------
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail=True; md.skipdata=True
text_bytes = raw[TEXT['pr']:TEXT['pr']+TEXT['rs']]
callers = {}   # target -> list of (site, mnemonic, size)
skipped = 0
for ins in md.disasm(text_bytes, TEXT_VA):
    if ins.id==0:
        skipped+=1; continue
    if ins.id in (X86_INS_CALL, X86_INS_JMP) and ins.operands:
        op=ins.operands[0]
        if op.type==X86_OP_IMM:
            t=op.imm & 0xFFFFFFFF
            callers.setdefault(t,[]).append((ins.address, ins.mnemonic+' '+ins.op_str, ins.size))

lines=[]
def P(x=''): lines.append(str(x))

P('# NAMED_PUSH_S10_B1 取证原始数据')
P('EXE SHA-256 = %s'%h)
P('ImageBase=0x%08X .text=[0x%08X,0x%08X) size=0x%X'%(IB,TEXT_VA,TEXT_END,len(text_bytes)))
P('sections: '+', '.join('%s@0x%08X(vs=0x%X,rs=0x%X)'%(s['nm'],s['va'],s['vs'],s['rs']) for s in secs))
P('linear sweep: callers targets=%d skipdata_bytes=%d'%(len(callers),skipped))
P()

for ea_s,name in ENTRIES:
    ea=int(ea_s,16)
    P('='*90)
    P('ENTRY %s  NAME %s'%(ea_s,name))
    # ①
    P('[1] 入口: in_text=%s  bytes@entry=%s'%(in_text(ea), raw[TEXT['pr']+(ea-TEXT_VA):TEXT['pr']+(ea-TEXT_VA)+16].hex(' ')))
    first=list(md.disasm(read(ea,48),ea))[:12]
    for ins in first:
        P('    %08X  %-26s %s'%(ins.address, ins.bytes.hex(' '), ins.mnemonic+' '+ins.op_str))
    # ② vtable/RTTI
    vts=find_vt(ea)
    if not vts:
        P('[2] 类身份: 无 vtable slot 指向本 entry（.rdata/.data 中 4 字节 VA 命中 0）')
    else:
        P('[2] 类身份: %d 个 vtable slot 指向本 entry:'%len(vts))
        for v in vts[:12]:
            P('    vt=0x%08X slot=+%d (0x%X) nslots=%d RTTI=%r hitva=0x%08X'%(
                v['vt'],v['slot'],v['slot']*4,v['nslots'],v['name'],v['hitva']))
    # ④ direct callers
    cl=callers.get(ea,[])
    P('[4] direct call/jmp 指向本 entry: %d 处'%len(cl))
    for s,disp,sz in cl[:30]:
        P('    site=0x%08X  %s  (sz=%d)'%(s,disp,sz))
    P()

open(os.path.join(OUT,'scan_all.txt'),'w',encoding='utf-8').write('\n'.join(lines))
print('wrote scan_all.txt lines=%d callers=%d'%(len(lines),len(callers)))
