# -*- coding: utf-8 -*-
"""逐行深挖：①边界 ②已在scan ③b②站点全上下文+eax陷阱+错误码 ④raw E8/E9直接调用+ctor装vptr+派发站点"""
import os, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import capstone.x86 as cx86
from capstone.x86 import (X86_INS_CALL, X86_INS_JMP, X86_INS_RET, X86_INS_TEST,
    X86_INS_OR, X86_INS_CMP, X86_INS_MOV, X86_INS_XOR, X86_INS_SUB, X86_INS_AND,
    X86_INS_XCHG, X86_OP_REG, X86_OP_IMM, X86_OP_MEM, X86_REG_EAX, X86_REG_INVALID,
    X86_INS_PUSH)

EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
OUT=os.path.dirname(os.path.abspath(__file__))
ENTRIES=[('004D8560','AircraftClass::slot267',106),('004D9720','AircraftClass::slot55',120),
 ('004D9E70','AircraftClass::slot38',247),('004DA1D0','AircraftClass::slot200',89),
 ('004DA4E0','AircraftClass::slot26',67),('004DE7B0','AircraftClass::slot314',396),
 ('004DE940','AircraftClass::slot315',412),('004DEBB0','AircraftClass::slot247',434),
 ('004DEE80','AircraftClass::slot331',442),('004DF7F0','AircraftClass::slot322',601),
 ('004DFF40','AircraftClass::slot209',311),('00517FA0','InfantryClass::slot91',3509),
 ('00518F90','InfantryClass::slot69',1689),('00519630','InfantryClass::slot99',5083),
 ('0051AA40','InfantryClass::slot288',1953),('0051BAB0','InfantryClass::slot23',1239),
 ('0051BF90','InfantryClass::slot107',2291),('0051C8B0','InfantryClass::slot240',741)]

pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
raw=open(EXE,'rb').read()
secs=[dict(nm=s.Name.rstrip(b'\x00').decode('latin1'),va=IB+s.VirtualAddress,
      vs=s.Misc_VirtualSize,pr=s.PointerToRawData,rs=s.SizeOfRawData) for s in pe.sections]
TEXT=next(s for s in secs if s['nm']=='.text')
TV=TEXT['va']; TB=raw[TEXT['pr']:TEXT['pr']+TEXT['rs']]; TE=S2=TV+len(TB)
def read(va,n):
    for s in secs:
        if s['va']<=va<s['va']+max(s['vs'],s['rs']):
            o=s['pr']+(va-s['va']); return raw[o:o+n]
    return b''
def u32(va):
    b=read(va,4); return int.from_bytes(b,'little') if len(b)==4 else None
def in_text(va): return TV<=va<TE

md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True

JCC={getattr(cx86,n) for n in dir(cx86) if n.startswith('X86_INS_J') and n!='X86_INS_JMP' and isinstance(getattr(cx86,n),int)}
CTRL=JCC|{X86_INS_JMP,X86_INS_RET,X86_INS_CALL,cx86.X86_INS_LOOP,cx86.X86_INS_LOOPE,cx86.X86_INS_LOOPNE}
IDEM={X86_INS_OR,X86_INS_AND,X86_INS_MOV,X86_INS_XCHG,X86_INS_TEST}
def iseax(op): return op.type==X86_OP_REG and op.reg==X86_REG_EAX
def writes_eax(ins):
    if ins.id==X86_INS_CALL: return True
    try: _,wr=ins.regs_access()
    except: return True
    if X86_REG_EAX in wr:
        if ins.id in IDEM and len(ins.operands)==2 and iseax(ins.operands[0]) and iseax(ins.operands[1]):
            return False
        return True
    return False
def testkind(ins):
    if ins.id==X86_INS_TEST and len(ins.operands)==2 and iseax(ins.operands[0]) and iseax(ins.operands[1]): return ('TEST_EAX',0)
    if ins.id==X86_INS_OR and len(ins.operands)==2 and iseax(ins.operands[0]) and iseax(ins.operands[1]): return ('OR_EAX',0)
    if ins.id==X86_INS_CMP and len(ins.operands)==2 and iseax(ins.operands[0]) and ins.operands[1].type==X86_OP_IMM: return ('CMP_IMM',ins.operands[1].imm&0xFFFFFFFF)
    return None
def pathsig(insns,s,n=14):
    calls=set(); rets=set(); hasret=False; eax=None; end=None
    for j in range(s,min(s+n,len(insns))):
        ins=insns[j]
        if ins.id==0: continue
        if ins.id==X86_INS_CALL:
            if ins.operands and ins.operands[0].type==X86_OP_IMM: calls.add(ins.operands[0].imm&0xFFFFFFFF)
            eax=None
        elif ins.id in (X86_INS_XOR,X86_INS_SUB) and len(ins.operands)==2 and iseax(ins.operands[0]) and iseax(ins.operands[1]): eax=0
        elif ins.id==X86_INS_MOV and len(ins.operands)==2 and iseax(ins.operands[0]):
            eax=(ins.operands[1].imm&0xFFFFFFFF) if ins.operands[1].type==X86_OP_IMM else None
        elif ins.id==X86_INS_RET:
            hasret=True
            if eax is not None: rets.add(eax)
            end=eax; break
        elif ins.id==X86_INS_JMP: end=eax; break
        else: end=eax
    return dict(calls=sorted(calls),rets=sorted(rets),hasret=hasret,end=end)
SK=('calls','rets','hasret','end')

# raw E8/E9 rel32 scan for direct calls/jmps to each entry (independent of capstone)
def raw_direct(target):
    hits=[]
    for off in range(0,len(TB)-5):
        op=TB[off]
        if op in (0xE8,0xE9):
            rel=int.from_bytes(TB[off+1:off+5],'little',signed=True)
            site=TV+off; t=(site+5+rel)&0xFFFFFFFF
            if t==target: hits.append((site,'E8' if op==0xE8 else 'E9'))
    return hits

lines=[]
def P(x=''): lines.append(str(x))

# ctor-install site search: instructions writing immediate vtable VA to [reg]/[reg+disp] = vptr install
VTBLS={0x7E22A4:'AircraftClass',0x7E8C94:'FootClass',0x7EB058:'InfantryClass',0x7F5C70:'UnitClass'}
# scan all .text for mov [mem],imm where imm in VTBLS, and push imm (alternate)
installs={v:[] for v in VTBLS}
for ins in md.disasm(TB,TV):
    if ins.id==X86_INS_MOV and len(ins.operands)==2 and ins.operands[0].type==X86_OP_MEM and ins.operands[1].type==X86_OP_IMM:
        im=ins.operands[1].imm&0xFFFFFFFF
        if im in installs: installs[im].append((ins.address,ins.mnemonic+' '+ins.op_str))
    if ins.id==X86_INS_PUSH and ins.operands and ins.operands[0].type==X86_OP_IMM:
        im=ins.operands[0].imm&0xFFFFFFFF
        if im in installs: installs[im].append((ins.address,'PUSH '+hex(im)))
P('# vptr install sites (mov [mem],vt / push vt) in .text')
for v,nm in VTBLS.items():
    P('  vt=%08X %s : %d sites %s'%(v,nm,len(installs[v]),['%08X'%a for a,_ in installs[v][:12]]))
P()

for ea_s,name,size in ENTRIES:
    ea=int(ea_s,16)
    P('='*92); P('ROW %s %s size=%d'%(ea_s,name,size))
    code=read(ea,size)
    insns=list(md.disasm(code,ea))
    idx={ins.address:i for i,ins in enumerate(insns)}
    # ③b② sites
    P('[3] ③b② 站点:')
    nsite=0
    for i,ins in enumerate(insns):
        if ins.id!=X86_INS_CALL: continue
        k=None
        for j in range(i+1,min(i+4,len(insns))):
            mid=insns[j]
            if mid.id==0 or mid.id in CTRL or writes_eax(mid): break
            if testkind(mid): k=j; break
        if k is None: continue
        tk=testkind(insns[k])
        for m in range(k+1,min(k+3,len(insns))):
            jc=insns[m]
            if jc.id in JCC:
                gap=insns[k+1:m]; bad=any(g.id==0 or g.id in CTRL or writes_eax(g) for g in gap)
                tgt=jc.operands[0].imm&0xFFFFFFFF if jc.operands and jc.operands[0].type==X86_OP_IMM else None
                ti=idx.get(tgt); sig_t=pathsig(insns,ti) if ti is not None else dict(calls=[],rets=[],hasret=False,end='OUT')
                sig_f=pathsig(insns,m+1)
                diff=tuple(sig_t[x] for x in SK)!=tuple(sig_f[x] for x in SK)
                nsite+=1
                P('  site%d call@%08X %s'%(nsite,ins.address,ins.op_str))
                P('    test@%08X %s %s kind=%s'%(insns[k].address,insns[k].mnemonic,insns[k].op_str,str(tk)))
                P('    jcc @%08X %s -> %08X  gap_eax_overwrite=%s'%(jc.address,jc.mnemonic+jc.op_str,tgt or 0,bad))
                P('    taken sig=%s'%str(sig_t)); P('    fall  sig=%s'%str(sig_f)); P('    paths_diff=%s'%diff)
                # callee profile: first bytes of callee if imm
                if ins.operands and ins.operands[0].type==X86_OP_IMM:
                    ca=ins.operands[0].imm&0xFFFFFFFF
                    P('    callee@%08X bytes=%s'%(ca,read(ca,12).hex(' ')))
                break
            if writes_eax(jc) or jc.id==0:
                if m+1<len(insns) and insns[m+1].id in JCC:
                    P('  [TRAP] test@%08X 后 @%08X %s 覆写eax再分支'%(insns[k].address,jc.address,jc.mnemonic+' '+jc.op_str))
                break
            if jc.id in CTRL: break
    if nsite==0: P('  (无 ③b② 机械站点)')
    # ④ raw direct
    rd=raw_direct(ea)
    P('[4] raw E8/E9 direct to entry: %d %s'%(len(rd),[(hex(a),op) for a,op in rd[:10]]))
    P()

open(os.path.join(OUT,'deep.txt'),'w',encoding='utf-8').write('\n'.join(lines))
print('wrote deep.txt lines=%d'%len(lines))
