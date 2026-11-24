# -*- coding: utf-8 -*-
"""005F5E80 ④ 终裁：body 内是否有虚表派发；12 caller 是否从 PE 入口正向可达（活链）。
照 S17_ENGFAM 口径：真实调用者需「紧接消费 + 非 direct-only 死链」。"""
import os, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import (X86_INS_CALL, X86_INS_JMP, X86_INS_RET, X86_OP_IMM, X86_OP_MEM, X86_OP_REG)

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, 'work')
pe = pefile.PE(EXE, fast_load=True); IB = pe.OPTIONAL_HEADER.ImageBase
EP = IB + pe.OPTIONAL_HEADER.AddressOfEntryPoint
raw = open(EXE, 'rb').read()
secs = [dict(nm=s.Name.rstrip(b'\x00').decode('latin1'), va=IB+s.VirtualAddress, vs=s.Misc_VirtualSize, pr=s.PointerToRawData, rs=s.SizeOfRawData) for s in pe.sections]
TEXT = next(s for s in secs if s['nm']=='.text'); TV=TEXT['va']; TB=raw[TEXT['pr']:TEXT['pr']+TEXT['rs']]; TE=TV+len(TB)
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail=True; md.skipdata=True
def read(va,n):
    for s in secs:
        if s['va']<=va<s['va']+max(s['vs'],s['rs']):
            o=s['pr']+(va-s['va']); return raw[o:o+n]
    return b''
def dis(va,n):
    off=TEXT['pr']+(va-TV); return list(md.disasm(raw[off:off+n],va))

lines=[]
def P(x=''): lines.append(str(x))
P('# 005F5E80 (MissionClass::slot5) ④ 终裁')
P('PE entry point = 0x%08X'%EP)

# 1) body 全长反汇编，找 call [reg+off]（虚表派发）
P('## 1) 函数体 005F5E80 (size=125) 全反汇编，标注间接 call')
body = dis(0x5f5e80, 125)
vdisp=0
for ins in body:
    tag=''
    if ins.id==X86_INS_CALL:
        if ins.operands and ins.operands[0].type==X86_OP_IMM:
            tag=' [DIRECT 0x%X]'%(ins.operands[0].imm&0xFFFFFFFF)
        elif ins.operands and ins.operands[0].type==X86_OP_MEM:
            tag=' [INDIRECT/vtable-dispatch]'; vdisp+=1
        else: tag=' [INDIRECT-reg]'
    P('  %08X %-22s %s%s'%(ins.address,ins.bytes.hex(' '),ins.mnemonic+' '+ins.op_str,tag))
P('body 内间接 call（虚表派发）数 = %d'%vdisp)

# 2) 正向可达性：从 PE entry 沿 E8 direct call BFS（函数级粗粒度）
P('## 2) 正向可达性（从 PE entry 沿 E8/E9 direct call BFS）')
# 建 direct call 边：caller site's function -> target。用「所有 E8/E9 目标」做粗闭包（地址级）
edges={}
for ins in md.disasm(TB,TV):
    if ins.id==0: continue
    if ins.id in (X86_INS_CALL,X86_INS_JMP) and ins.operands and ins.operands[0].type==X86_OP_IMM:
        edges.setdefault(ins.address,[]).append(ins.operands[0].imm&0xFFFFFFFF)
# 以「指令地址」为节点粗闭包太碎；改为：从 EP 出发 BFS，节点=函数区间起点集合（所有 call target）
targets=set()
for v in edges.values(): targets.update(v)
# 用「caller 落在哪个函数区间」映射：函数起点=排序后的 call target
starts=sorted(t for t in targets if TV<=t<TE)
import bisect
def func_start(addr):
    i=bisect.bisect_right(starts,addr)-1
    return starts[i] if i>=0 else addr
# 函数级调用图
fgraph={}
for site,tgts in edges.items():
    fs=func_start(site)
    for t in tgts:
        if TV<=t<TE:
            fgraph.setdefault(fs,set()).add(func_start(t))
CALLERS=['0x42528c','0x43695c','0x46ae7c','0x54399c','0x5fd8fc','0x62d7ab','0x62ff2f','0x65ab8d','0x6b4eac','0x71ce79','0x74a97c','0x75f65f']
caller_funcs=set(func_start(int(c,16)) for c in CALLERS)
P('12 caller 所属函数起点: %s'%sorted('%08X'%f for f in caller_funcs))
seen={EP}; stack=[EP]; n=0
while stack:
    cur=stack.pop(); n+=1
    for nx in fgraph.get(func_start(cur),()):
        if nx not in seen:
            seen.add(nx); stack.append(nx)
P('BFS 访问函数起点数 = %d'%len(seen))
for c in sorted(caller_funcs):
    P('  caller-func %08X reachable from EP = %s'%(c, c in seen))
P('12 caller 中从 PE entry 可达数 = %d / %d'%(sum(1 for c in caller_funcs if c in seen),len(caller_funcs)))

open(os.path.join(OUT,'ring4_row15_final.txt'),'w',encoding='utf-8').write('\n'.join(lines))
print('wrote ring4_row15_final.txt lines=%d vdisp=%d'%(len(lines),vdisp))
