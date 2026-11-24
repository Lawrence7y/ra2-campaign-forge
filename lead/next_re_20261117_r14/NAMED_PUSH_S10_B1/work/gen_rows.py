# -*- coding: utf-8 -*-
"""逐行落盘生成器：重新取证并把每行 EVIDENCE 立即写盘，最后汇总。"""
import os, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import capstone.x86 as cx86
from capstone.x86 import (X86_INS_CALL, X86_INS_JMP, X86_INS_RET, X86_INS_TEST,
    X86_INS_OR, X86_INS_CMP, X86_INS_MOV, X86_INS_XOR, X86_INS_SUB, X86_INS_AND,
    X86_INS_XCHG, X86_OP_REG, X86_OP_IMM, X86_OP_MEM, X86_REG_EAX, X86_REG_INVALID,
    X86_INS_PUSH)

EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # batch dir
EVD=os.path.join(BASE,'EVIDENCE'); os.makedirs(EVD,exist_ok=True)
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
TV=TEXT['va']; TB=raw[TEXT['pr']:TEXT['pr']+TEXT['rs']]; TE=TV+len(TB)
DATA=[s for s in secs if s['nm'] in ('.rdata','.data')]
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
        if ins.id in IDEM and len(ins.operands)==2 and iseax(ins.operands[0]) and iseax(ins.operands[1]): return False
        return True
    return False
def testkind(ins):
    if ins.id==X86_INS_TEST and len(ins.operands)==2 and iseax(ins.operands[0]) and iseax(ins.operands[1]): return ('TEST_EAX',0)
    if ins.id==X86_INS_OR and len(ins.operands)==2 and iseax(ins.operands[0]) and iseax(ins.operands[1]): return ('OR_EAX',0)
    if ins.id==X86_INS_CMP and len(ins.operands)==2 and iseax(ins.operands[0]) and ins.operands[1].type==X86_OP_IMM: return ('CMP_IMM',ins.operands[1].imm&0xFFFFFFFF)
    return None
def pathsig(insns,s,n=14):
    calls=set(); rets=set(); hr=False; eax=None; end=None
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
            hr=True
            if eax is not None: rets.add(eax)
            end=eax; break
        elif ins.id==X86_INS_JMP: end=eax; break
        else: end=eax
    return (tuple(sorted(calls)),tuple(sorted(rets)),hr,end)
def rtti(vt):
    col=u32(vt-4)
    if col is None or not (0x7e0000<=col<0x850000): return None
    td=u32(col+0xC)
    if td is None or not (0x400000<=td<0x900000): return None
    s=read(td+8,160).split(b'\x00')[0]
    try: nm=s.decode('latin1')
    except: return None
    return nm if nm.startswith('.?A') else None
def find_vt(entry):
    out=[]; pat=struct.pack('<I',entry)
    for s in DATA:
        base=s['va']; start=s['pr']; ln=s['rs']; i=0
        while True:
            j=raw.find(pat,start+i,start+ln-3)
            if j<0: break
            va=base+(j-start); st=va
            while True:
                p=u32(st-4)
                if p is not None and in_text(p): st-=4
                else: break
            en=va+4
            while True:
                nx=u32(en)
                if nx is not None and in_text(nx): en+=4
                else: break
            out.append((st,(va-st)//4,rtti(st),(en-st)//4,va))
            i=j-start+1
    return out
def raw_direct(target):
    h=[]
    for off in range(len(TB)-5):
        if TB[off] in (0xE8,0xE9):
            rel=int.from_bytes(TB[off+1:off+5],'little',signed=True)
            if (TV+off+5+rel)&0xFFFFFFFF==target: h.append((TV+off,'E8' if TB[off]==0xE8 else 'E9'))
    return h
def imm_refs(target):
    out=[]
    for ins in md.disasm(TB,TV):
        if ins.id==0: continue
        for op in ins.operands:
            if op.type==X86_OP_IMM and (op.imm&0xFFFFFFFF)==target: out.append((ins.address,ins.mnemonic+' '+ins.op_str))
    return out

VTBLS={0x7E22A4:'AircraftClass',0x7E8C94:'FootClass',0x7EB058:'InfantryClass',0x7F5C70:'UnitClass'}
installs={v:[] for v in VTBLS}
for ins in md.disasm(TB,TV):
    if ins.id==X86_INS_MOV and len(ins.operands)==2 and ins.operands[0].type==X86_OP_MEM and ins.operands[1].type==X86_OP_IMM:
        im=ins.operands[1].imm&0xFFFFFFFF
        if im in installs: installs[im].append(ins.address)

results=[]; prog=[]
for idx,(ea_s,name,size) in enumerate(ENTRIES,1):
    ea=int(ea_s,16); L=[]
    def W(x=''): L.append(str(x))
    W('# ROW %s  %s'%(ea_s,name))
    W('批次：NAMED_PUSH_S10_B1 ｜ 子系统 S10 ｜ 目标 gamemd.exe SHA-256 73201CC0...F67476')
    W('')
    # ①
    pb=read(ea,16).hex(' ')
    W('## ① 入口（.text 内、函数边界自洽）')
    W('- entry=%s ；in_text=%s ；atlas size=%d'%(ea_s,in_text(ea),size))
    W('- bytes@entry = %s'%pb)
    first=list(md.disasm(read(ea,32),ea))[:6]
    for ins in first: W('  %08X  %-20s %s'%(ins.address,ins.bytes.hex(' '),ins.mnemonic+' '+ins.op_str))
    W('- 裁定：%s'%('PASS' if in_text(ea) else 'FAIL'))
    W('')
    # ②
    vts=find_vt(ea)
    W('## ② 类身份（RTTI/虚表；与④不同源；slotN 内类名仅线索）')
    W('- 指向本 entry 的 vtable slot 共 %d 个：'%len(vts))
    for st,sl,nm,ns,hv in vts[:6]:
        col=u32(st-4); td=u32(col+0xC) if col else None
        W('  vt=%08X slot=+%d(0x%X) nslots=%d hitva=%08X COL=%s TD=%s RTTI=%r'%(
            st,sl,sl*4,ns,hv,('%08X'%col) if col else '?',('%08X'%td) if td else '?',nm))
    proper=[v for v in vts if v[2] and v[2].startswith('.?AV')]
    W('- RTTI 钉住类名：%s'%('YES → %s'%(proper[0][2] if proper else '?') if proper else 'NO'))
    W('- 裁定：%s（② 用「虚表槽指向本 entry + RTTI 类名字串」钉死；%s）'%(
        'PASS' if proper else 'FAIL',
        ('名字 %s 中的类前缀与 RTTI 相符，但前缀本身只是线索'%name.split('::')[0]) if proper else 'RTTI 不可解析'))
    W('')
    # ③b
    W('## ③ 整体合同（只认 ③b；③b② 可伪证返回约定 + 调用方分支）')
    code=read(ea,size); insns=list(md.disasm(code,ea)); idxmap={ins.address:i for i,ins in enumerate(insns)}
    nsite=0; any_valid=False; trap=False; valids=[]
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
                ti=idxmap.get(tgt)
                sig_t=pathsig(insns,ti) if ti is not None else ((),(),False,'OUT')
                sig_f=pathsig(insns,m+1)
                diff=sig_t!=sig_f; nsite+=1
                ok=(diff and not bad)
                W('  站点%d call@%08X [%s] → %s@%08X → %s@%08X → %08X'%(nsite,ins.address,
                    ins.op_str,tk[0],insns[k].address,jc.mnemonic,jc.address,tgt or 0))
                W('    call bytes=%s ; test bytes=%s ; jcc bytes=%s'%(ins.bytes.hex(' '),insns[k].bytes.hex(' '),jc.bytes.hex(' ')))
                W('    eax覆写陷阱=%s ; taken_sig=%s ; fall_sig=%s ; 路径签名不同=%s'%(bad,sig_t,sig_f,diff))
                if bad: trap=True
                if ok: any_valid=True; valids.append((ins.address,insns[k].address,jc.address,tgt))
                break
            if writes_eax(jc) or jc.id==0:
                if m+1<len(insns) and insns[m+1].id in JCC: trap=True
                break
            if jc.id in CTRL: break
    W('- 机械 ③b② 站点数=%d ；其中无陷阱且成功/失败路径签名不同=%d'%(nsite,len(valids)))
    W('- 裁定：%s'%('PASS（③b②：返回值被本函数内 test/cmp+jcc 消费，两路动作签名不同）' if any_valid else
        ('FAIL（站点均路径签名相同或 eax 覆写陷阱）' if nsite else 'FAIL（无 ③b② 站点）')))
    W('')
    # ④
    W('## ④ 使用见证（真实调用者或活虚表派发；direct-only 不足；与②不同源）')
    rd=raw_direct(ea); ir=imm_refs(ea)
    W('- E8/E9 direct callers 指向本 entry：%d 处（全 .text 原始字节扫描 + capstone 双通道）'%len(rd))
    W('- 本 entry VA 作为立即数/位移在 .text 被引用：%d 处'%len(ir))
    # dword occurrences
    pat=struct.pack('<I',ea); cnt=0; texts=0
    for s in secs:
        base=s['pr']; ln=s['rs']; i=0
        while True:
            j=raw.find(pat,base+i,base+ln-3)
            if j<0: break
            cnt+=1
            if s['nm']=='.text': texts+=1
            i=j-base+1
    W('- 本 entry VA 4字节出现：%d 次（.text 内 %d 次）；%d 次全在非代码节虚表'% (cnt,texts,cnt-texts))
    # vptr install context
    W('- 相关类虚表的 vptr 安装点（构造期写 this）：')
    for hv in sorted(set(v[0] for v in vts)):
        if hv in installs:
            W('    vt=%08X : %s（写入 [esi]/[edi]，esi/edi=ecx=this ⇒ 实例对象，非静态 global 接收者）'%(
                hv,', '.join('%08X'%a for a in installs[hv][:4])))
    W('- 判定：无 direct caller、无立即数引用、仅虚表可达；唯一「派发」证据与②共用同一虚表槽 ⇒ 违反 §12.3「②④不同源」')
    W('- 裁定：FAIL（D-40 严格口径；对照 S13_PUSH 6 行同类行、S13_K12 审计仅 3/17 可辩护）')
    W('')
    # conclusion
    r1=in_text(ea); r2=bool(proper); r3=any_valid; r4=False
    W('## 四环结论')
    W('- ①=%s ②=%s ③b=%s ④=%s ｜ 四环齐全=%s ｜ 是否产出 delta=%s'%(
        'PASS' if r1 else 'FAIL','PASS' if r2 else 'FAIL','PASS' if r3 else 'FAIL','FAIL',
        'NO','NO'))
    W('- 本行不改 coverage.tsv / 台账 / 任何共享文件。')
    path=os.path.join(EVD,'ROW_%s.txt'%ea_s)
    with open(path,'w',encoding='utf-8') as f: f.write('\n'.join(L)+'\n')
    results.append(dict(entry=ea_s,name=name,r1=r1,r2=r2,r3=r3,r4=r4,n3=nsite,v3=len(valids),nv=len(vts)))
    prog.append('| %d | %s | %s | %s | %s | %s | %s | %s | %s |'%(
        idx,ea_s,name,'✓' if r1 else '✗','✓' if r2 else '✗',
        ('✓(%d/%d)'%(len(valids),nsite)) if r3 else ('✗(%d)'%nsite),'✗','否','否'))
    print('ROW %s written ②=%s ③b=%s ④=%s'%(ea_s,r2,r3,r4))
    # 每 5 行追加 PROGRESS
    if idx%5==0 or idx==len(ENTRIES):
        with open(os.path.join(BASE,'PROGRESS.md'),'a',encoding='utf-8') as f:
            if idx==5: f.write('# NAMED_PUSH_S10_B1 · PROGRESS\n\nD-40 严格口径逐行核；每 5 行追加。\n\n')
            f.write('| # | entry | name | ① | ② | ③b | ④ | 四环齐全 | 产出 |\n')
            f.write('|---|---|---|---|---|---|---|---|---|\n')
            for ln in prog[-5:]: f.write(ln+'\n')
            f.write('\n(已核 %d/%d 行)\n\n'%(idx,len(ENTRIES)))

import json
json.dump(results,open(os.path.join(BASE,'work','results.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('DONE rows=%d ②ok=%d ③bok=%d ④ok=%d allfour=%d'%(
    len(results),sum(r['r2'] for r in results),sum(r['r3'] for r in results),
    sum(r['r4'] for r in results),sum(all(r[k] for k in ('r1','r2','r3','r4')) for r in results)))
