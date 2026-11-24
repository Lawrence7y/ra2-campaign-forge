# -*- coding: utf-8 -*-
"""④ 独立见证终检：全镜像查 entry VA 的立即数引用（push/mov addr），以及 4 张类 vt 的 ctor 装表上下文。"""
import os, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_INVALID

EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
OUT=os.path.dirname(os.path.abspath(__file__))
ENTRIES=['004D8560','004D9720','004D9E70','004DA1D0','004DA4E0','004DE7B0','004DE940',
 '004DEBB0','004DEE80','004DF7F0','004DFF40','00517FA0','00518F90','00519630',
 '0051AA40','0051BAB0','0051BF90','0051C8B0']
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
raw=open(EXE,'rb').read()
secs=[dict(nm=s.Name.rstrip(b'\x00').decode('latin1'),va=IB+s.VirtualAddress,vs=s.Misc_VirtualSize,pr=s.PointerToRawData,rs=s.SizeOfRawData) for s in pe.sections]
TEXT=next(s for s in secs if s['nm']=='.text'); TV=TEXT['va']; TB=raw[TEXT['pr']:TEXT['pr']+TEXT['rs']]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True

lines=[]
def P(x=''): lines.append(str(x))

# 1) immediate references: linear sweep .text, any operand IMM == entry, and any memory disp/imm == entry
imm_ref={e:[] for e in ENTRIES}
for ins in md.disasm(TB,TV):
    if ins.id==0: continue
    for op in ins.operands:
        if op.type==X86_OP_IMM:
            v=op.imm&0xFFFFFFFF
            k='%08X'%v
            if k in imm_ref: imm_ref[k].append((ins.address,ins.mnemonic+' '+ins.op_str))
        elif op.type==X86_OP_MEM:
            for v in (op.mem.disp&0xFFFFFFFF,):
                k='%08X'%v
                if k in imm_ref: imm_ref[k].append((ins.address,ins.mnemonic+' '+ins.op_str+' [disp]'))
P('# ④ 独立见证终检')
P('## A) entry VA 作为立即数/位移在 .text 被引用（除虚表外的直接证据）')
for e in ENTRIES:
    r=imm_ref[e]
    P('  %s : %d 处 %s'%(e,len(r),['%08X:%s'%(a,d) for a,d in r[:8]]))

# 2) raw dword occurrence of entry VA anywhere in image (vtable slots + any immediate encoding)
P('## B) entry VA 全镜像 4字节出现次数（.rdata/.data 虚表槽为主）')
for e in ENTRIES:
    pat=struct.pack('<I',int(e,16)); cnt=0; locs=[]
    for s in secs:
        base=s['pr']; ln=s['rs']; i=0
        while True:
            j=raw.find(pat,base+i,base+ln-3)
            if j<0: break
            cnt+=1
            if s['nm']=='.text' and len(locs)<6: locs.append('%08X'%(s['va']+(j-base)))
            i=j-base+1
    P('  %s : dword出现 %d 次, .text内 %s'%(e,cnt,locs))

# 3) ctor install sites context (the 12 sites found earlier)
P('## C) 4 张类虚表 vptr 安装点上下文（是否静态 global 接收者）')
VTS={0x7E22A4:['00413D87','0041408A','0041B4E1'],0x7E8C94:['004D345D','004D3568','004D359D'],
     0x7EB058:['00517ACC','00517D9D','00521A11'],0x7F5C70:['0073543A','00735794','00744521']}
def dis(va,n=40):
    off=TEXT['pr']+(va-TV); return list(md.disasm(raw[off:off+n],va))
for vt,sites in VTS.items():
    P('  vt=%08X'%vt)
    for hs in sites:
        va=int(hs,16)
        seq=dis(va-16,48)
        P('    near %s:'%hs)
        for ins in seq:
            P('      %08X %-22s %s'%(ins.address,ins.bytes.hex(' '),ins.mnemonic+' '+ins.op_str))

open(os.path.join(OUT,'ring4_final.txt'),'w',encoding='utf-8').write('\n'.join(lines))
print('wrote ring4_final.txt lines=%d'%len(lines))
