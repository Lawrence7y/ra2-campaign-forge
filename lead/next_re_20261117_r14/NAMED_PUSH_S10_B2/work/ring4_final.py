# -*- coding: utf-8 -*-
"""④ 独立见证终检（B2）：
A) entry VA 立即数/位移引用
B) entry VA 全镜像 dword 出现
C) 相关类虚表 vptr 安装点上下文（静态 global 接收者 exact 派发 vs 实例 this）
D) 005F5E80 的 12 个 direct E8 caller 逐点上下文 + 返回消费 + 可达性
"""
import os, struct, csv
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_INS_CALL, X86_INS_MOV

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, 'work')
HITS = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv'
rows = [r for r in csv.DictReader(open(HITS, encoding='utf-8'), delimiter='\t')
        if r['subsystem'] == 'S10' and r['p3b2_named'] == 'True']
rows.sort(key=lambda r: int(r['entry'], 16))
sel = rows[18:36]
ENTRIES = [r['entry'] for r in sel]
NAMES = {r['entry']: r['name'] for r in sel}

pe = pefile.PE(EXE, fast_load=True); IB = pe.OPTIONAL_HEADER.ImageBase
raw = open(EXE, 'rb').read()
secs = [dict(nm=s.Name.rstrip(b'\x00').decode('latin1'), va=IB+s.VirtualAddress, vs=s.Misc_VirtualSize, pr=s.PointerToRawData, rs=s.SizeOfRawData) for s in pe.sections]
TEXT = next(s for s in secs if s['nm'] == '.text'); TV = TEXT['va']; TB = raw[TEXT['pr']:TEXT['pr']+TEXT['rs']]; TRAW = TEXT['pr']
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True
def read(va, n):
    for s in secs:
        if s['va'] <= va < s['va']+max(s['vs'], s['rs']):
            o = s['pr']+(va-s['va']); return raw[o:o+n]
    return b''
def u32(va):
    b=read(va,4); return int.from_bytes(b,'little') if len(b)==4 else None
def dis(va, n=48):
    off = TEXT['pr']+(va-TV)
    return list(md.disasm(raw[off:off+n], va))

lines=[]
def P(x=''): lines.append(str(x))

P('# ④ 独立见证终检（B2）')
# A) immediate refs
imm_ref = {e:[] for e in ENTRIES}
for ins in md.disasm(TB, TV):
    if ins.id==0: continue
    for op in ins.operands:
        if op.type==X86_OP_IMM:
            k='%08X'%(op.imm&0xFFFFFFFF)
            if k in imm_ref: imm_ref[k].append((ins.address, ins.mnemonic+' '+ins.op_str))
        elif op.type==X86_OP_MEM and op.mem.disp:
            k='%08X'%(op.mem.disp&0xFFFFFFFF)
            if k in imm_ref: imm_ref[k].append((ins.address, ins.mnemonic+' '+ins.op_str+' [disp]'))
P('## A) entry VA 作为立即数/位移在 .text 被引用')
for e in ENTRIES:
    r=imm_ref[e]
    P('  %s %-28s : %d 处 %s'%(e,NAMES[e],len(r),['%08X:%s'%(a,d) for a,d in r[:6]]))

P('## B) entry VA 全镜像 4字节出现次数')
for e in ENTRIES:
    pat=struct.pack('<I',int(e,16)); cnt=0; txt=[]; other=[]
    for s in secs:
        base=s['pr']; ln=s['rs']; i=0
        while True:
            j=raw.find(pat,base+i,base+ln-3)
            if j<0: break
            va=s['va']+(j-base)
            if s['nm']=='.text': txt.append(va)
            else: other.append((s['nm'],va))
            cnt+=1; i=j-base+1
    P('  %s %-28s : dword %d 次, .text内 %d %s, 非代码 %s'%(e,NAMES[e],cnt,len(txt),['%08X'%v for v in txt[:6]],[(nm,'%08X'%v) for nm,v in other[:5]]))

# C) vptr install context
P('## C) 相关类虚表 vptr 安装点上下文（接收者类型）')
VT_SITES = {
 0x7EB058:['00517ACC','00517D9D','00521A11'],
 0x7E22A4:['00413D87','0041408A','0041B4E1'],
 0x7EF060:['005F39BA','005F3B5D','005F3B87'],
 0x7EDCC0:['005B2DE9','005B3A63','0065AF12','006F4775'],
 0x7F66A8:['0074C443','0074C669','0074C9FD'],
 0x7F31C8:['006AF1F2','006AF39B','006AF479','006AF4A5','006B11C5'],
 0x7F3650:['006B6CEF','006B6EE6','006B6FE5','006B7015','006B7F5F'],
}
for vt,sites in VT_SITES.items():
    P('  vt=%08X:'%vt)
    for hs in sites:
        va=int(hs,16); seq=dis(va-12,30)
        P('    near %s:'%hs)
        for ins in seq:
            P('      %08X %-22s %s'%(ins.address,ins.bytes.hex(' '),ins.mnemonic+' '+ins.op_str))

# D) 005F5E80 direct caller 上下文
P('## D) 005F5E80 MissionClass::slot5 的 12 个 direct E8 caller 逐点上下文')
CALLERS = ['0x42528c','0x43695c','0x46ae7c','0x54399c','0x5fd8fc','0x62d7ab','0x62ff2f','0x65ab8d','0x6b4eac','0x71ce79','0x74a97c','0x75f65f']
# raw==boundary 校验
def raw_bytes_at(va,n): return read(va,n)
for hs in CALLERS:
    va=int(hs,16)
    seq=dis(va-8,40)
    P('  --- caller @ %s ---'%hs)
    P('    raw@site = %s'%(raw_bytes_at(va,5).hex(' ')))
    for ins in seq:
        P('    %08X %-22s %s'%(ins.address,ins.bytes.hex(' '),ins.mnemonic+' '+ins.op_str))

open(os.path.join(OUT,'ring4_final.txt'),'w',encoding='utf-8').write('\n'.join(lines))
print('wrote ring4_final.txt lines=%d'%len(lines))
