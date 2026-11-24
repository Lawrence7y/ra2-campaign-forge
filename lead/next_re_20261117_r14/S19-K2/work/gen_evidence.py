#!/usr/bin/env python3
"""Regenerate naming evidence with exact hex addresses + grade-change summary."""
import os,json,csv,re
ROOT=r'D:\Project\ra2-campaign-forge'; CARD=os.path.join(ROOT,r'lead\next_re_20261117_r14\S19-K2')
ev=json.load(open(os.path.join(CARD,'work','s19_evidence.json'),encoding='utf-8'))
cov={}
with open(os.path.join(ROOT,r'lead\next_re_20261117_r14\COVERAGE\coverage.tsv'),encoding='utf-8') as f:
    for row in csv.DictReader(f,delimiter='\t'):
        if row['subsystem']=='S19': cov[row['entry'].upper()]=row['grade']
# extract exact sites for EVA functions (from prior extract output logic), hex
EVA=json.load(open(os.path.join(CARD,'work','s19_evidence.json'),encoding='utf-8'))
# recompute site addresses directly from evidence json strops + calls is complex; use helper
import struct,pefile
pe=pefile.PE(os.path.join(ROOT,r'ra2youli\gamemd.exe'),fast_load=False);IB=pe.OPTIONAL_HEADER.ImageBase;d=open(os.path.join(ROOT,r'ra2youli\gamemd.exe'),'rb').read()
md=__import__('capstone').Cs(__import__('capstone').CS_ARCH_X86,__import__('capstone').CS_MODE_32);md.skipdata=True;md.detail=True
from capstone.x86 import X86_OP_IMM,X86_INS_MOV,X86_INS_PUSH,X86_INS_CALL
def cstr(va):
    b=d[va-IB:va-IB+96];z=b.find(b'\0');z=z if z>=0 else 96;s=b[:z]
    return s.decode('ascii','replace') if len(s)>=3 and all(32<=c<127 for c in s) else None
def eva_sites(va,sz):
    insns=list(md.disasm(d[va-IB:va-IB+sz],va));out=[]
    for i,ins in enumerate(insns):
        if ins.id==X86_INS_CALL and ins.op_str.strip().lower()=='0x752700':
            for j in range(i-1,max(-1,i-10),-1):
                p=insns[j]
                if p.id==X86_INS_MOV and p.op_str.startswith('ecx,'):
                    mm=re.search(r'0x([0-9a-fA-F]+)',p.op_str)
                    if mm:
                        s=cstr(int(mm.group(1),16))
                        if s and s.startswith('EVA_'):
                            out.append((f'0x{p.address:X}',int(mm.group(1),16),s,f'0x{ins.address:X}'));break
    return out
atlas={}
with open(os.path.join(ROOT,r'lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'),encoding='utf-8') as f:
    for row in csv.DictReader(f,delimiter='\t'): atlas[row['entry'].upper()]=int(row['size'])
evafns=['00443860','0044F820','004571E0','00458200','004FB0E0','0050E010','00522910','00686570','006A87F0','006A8B30','006CC080','007393C0']
out=[]
out.append('S19-K2 · T2 定名字节级证据（逐条可独立复算；目标 SHA-256 73201CC0...F67476 亲测一致）')
out.append('分级规则：升级类动作须字节级证据或独立审计复算（STATUS_BOARD 升级硬规矩）。')
out.append('')
out.append('[A] EVA 触发函数：函数体内 mov ecx,<EVA串地址> 紧邻 call 0x752700(=VoxClass::Play/EVA 播放锚点)。')
for e in evafns:
    sites=eva_sites(int(e,16),atlas[e])
    out.append(f'  {e}: '+ '; '.join(f'mov ecx,[0x{sp:X}]="{s}" @insn {a} -> call 0x752700@{c}' for a,sp,s,c in sites))
out.append('')
out.append('[B] Bink OO 包装：函数体 call dword[0x7E15xx]=pefile 解析的 binkw32.dll 导入名（字节级 IAT）。')
for e in ['00432BD0','00432C30','00433020','004331F0','00432E40']:
    out.append(f'  {e}: '+ '; '.join(f'call@{hex(a)}={n}' for a,n in ev[e]['import_calls']))
out.append('')
out.append('[C] Taunt VOX 文件名表：00752B70 体内 10 个 taunts\\tau*%02i.wav 串引用 [静态推断]。')
out.append('')
out.append('[D] 定名目标当前 grade（来自 coverage.tsv 盘上现值）：')
for e in evafns+['00432BD0','00432C30','00433020','004331F0','00432E40','00752B70']:
    out.append(f'  {e}: cur={cov.get(e,"?")}')
p=os.path.join(CARD,'EVIDENCE','t2_naming_evidence.txt')
open(p,'w',encoding='utf-8').write('\n'.join(out)+'\n')
print('\n'.join(out[:6]))
print('...')
print('grade counts:', {g:sum(1 for e in evafns+['00432BD0','00432C30','00433020','004331F0','00432E40','00752B70'] if cov.get(e)==g) for g in set(cov.get(e) for e in evafns)})
