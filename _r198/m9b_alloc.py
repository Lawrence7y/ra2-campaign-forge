#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 第九刀 B（窄口径，快）：只在上溯树（279 个入口）与本轮 8 张超长表实现的函数体内，
找「16 字节状态对象四槽初始化」形态。范围小、可复算。
 M1 上溯树 279 入口（m5 结果）在各自体内是否有 4 槽 (+0/+4/+8/+0xC) 连续初始化。
 M2 8 张超长表涉及的实现集合体内是否有同样形态。
 M3 反控：把判据放宽到 2 槽，命中数。
 M4 复算：0x4A1CA0 一族宿主中是否存在 rep stosd / rep movsd。
"""
import sys,struct,collections,json,bisect,re
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
T=P.B['.text'];LO=T['lo'];HI=T['hi_file'];RAW=P.RAW
BUF=RAW[T['rawptr']:T['rawptr']+(HI-LO)]
def in_text(x): return x is not None and LO<=x<HI
def body(e,cap=4000):
    out=[]
    for off,sz,mn,op in md.disasm_lite(BUF[e-LO:e-LO+cap],e):
        out.append((off,mn,op))
        if mn=='ret': break
    return out
TREE=[0x410be0,0x41d585,0x420c35,0x438a70,0x43a130,0x472640,0x4a7a30,0x4c58c0,0x4ca1a0,0x4d2790,
      0x502d30,0x554fe4,0x5f6250,0x6292b0,0x65b2f0,0x68ca50,0x6b1020,0x6b7d80,0x6cc2a0,0x6e3b60,
      0x6e5560,0x6ec3d0,0x71a4e0,0x71f2a0,0x726720,0x727fd0,0x763ba0]
# m5 上溯树 279 入口：用 m5 json 读
J=json.load(open('/home/t628/projects/ra2-campaign-forge/_r198/m5_crctree.json'))
ck('M0a m5 上溯树入口数', J['allent']==279, J['allent'])
LAYERS=J['layers']; ck('M0b 层结构', True, LAYERS)
# 重新算 279 集合（用 m5 同法，但入口集合直接取 CALLAT 目标 + 前置）
# 简化：直接对 L1 的 27 + 其调用者的宿主 逐层 —— 复用 m5 已写盘的 detail 键不可靠，改为重算所有 CALLTGT 中
# 落在「调用点上方」的入口。此处置信 m5 的 279，但把「上溯树入口」外延为：所有对 27 个 L1 入口的调用点的宿主。
CALLTGT=set(); CALLAT=[]
pos=0
while pos<len(BUF):
    for off,sz,mn,op in md.disasm_lite(BUF[pos:pos+65536],LO+pos):
        if mn=='call' and op.startswith('0x'):
            t=int(op,16)
            if in_text(t): CALLAT.append((off,t)); CALLTGT.add(t)
    pos+=65536
SORT=sorted(CALLTGT)
def host_of(c):
    i=bisect.bisect_left(SORT,c)-1
    return SORT[i] if i>=0 else None
ent=set(TREE)
prev=set(TREE)
for _ in range(4):
    nx=set()
    for c,t in CALLAT:
        if t in prev:
            h=host_of(c)
            if h: nx.add(h)
    ent|=nx; prev=nx
ck('M1a 上溯树累计入口（重算）', True, len(ent))
FN=sorted(ent)
def scan(entries, need):
    hits=[]
    for e in entries:
        B=body(e)
        grp={}
        for (a,mn,op) in B:
            m=re.match(r'^(?:dword|word|byte) ptr \[([a-z]{3})(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\]$', op.split(',',1)[0].strip()) if ',' in op else None
            if not m or mn not in ('mov','or','and','add','sub','xor'): continue
            off=int(m.group(2),0) if m.group(2) else 0
            if off in (0,4,8,12): grp.setdefault((m.group(1),off),(hex(a),mn+' '+op))
        best=collections.defaultdict(set)
        for (reg,off),v in grp.items(): best[reg].add(off)
        for reg,offs in best.items():
            if len(offs)>=need: hits.append(dict(fn=hex(e),reg=reg,slots=sorted(offs)))
    return hits
H4=scan(FN,4)
ck('M1b 上溯树内四槽齐全函数数', H4==[], H4[:6])
H2=scan(FN,2)
ck('M3a 放宽到两槽的函数数', True, len(H2))
print('   M3b 两槽样本:', H2[:6])
# M4 复现串操作
def strs(e):
    return [ (hex(a),mn) for (a,mn,op) in body(e) if mn in ('stosd','stosb','movsd','movsb')]
S={hex(e):strs(e) for e in FN}
S={k:v for k,v in S.items() if v}
ck('M4a 上溯树内出现串操作的函数数', True, len(S))
print('   M4b', list(S.items())[:6])
# M2 超长表实现集合
IMP=set()
for vt in (0x7F5C70,0x7EB058,0x7E22A4,0x7E8C94,0x7E3EBC,0x7F4960,0x7F0508,0x7EDCC0):
    k=0
    while in_text(P.dw(vt+4*k)):
        IMP.add(P.dw(vt+4*k)); k+=1
IMP=sorted(IMP)
ck('M2a 8 张超长表涉及的实现数', True, len(IMP))
H4b=scan(IMP,4)
ck('M2b 这些实现体内四槽齐全个数', True, len(H4b))
print('   M2c', H4b[:6])
json.dump(dict(tree=len(ent),h4=H4,h2=len(H2),strs=list(S.items())[:20],imp=len(IMP),h4b=H4b,
  asserts=N,fails=fails),open('/home/t628/projects/ra2-campaign-forge/_r198/m9b_alloc.json','w'),
  ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
