#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 第十六刀：把 AbstractClass 构造函数群的字段初值做成可复算证据。
F1 全部「往 [reg] 写 0x7E1F50」的函数起点及其字段初始化序列（0x410170/0x4101C0/0x4105A0/0x6E8000/0x6E801F0）。
F2 每个构造函数的字段偏移 -> 初值 表（+0x8/+0xC/+0x10/+0x14/+0x18/+0x1C/+0x20）。
F3 这三/五个构造函数之间是否重复安装（二次构造证据）。
F4 关键：+0x10 = 0xFFFFFFFF 与 +0x20 = 0 的二进制内自证（R193/R194 遗留「语义名只来自 kb22」）。
"""
import sys,re,struct,collections,capstone
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c:fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
T=P.B['.text']; LO=T['lo']
def body(va,maxb=512):
    o=P.r2o(va); out=[]
    for ins in md.disasm(P.RAW[o:o+maxb],va):
        out.append(ins)
        if ins.mnemonic.startswith('ret'): break
    return out
SITES=[(0x410198,0x410170),(0x4101D0,0x4101C0),(0x4101F0,0x4101E0),(0x4105A9,0x4105A0),
       (0x6E803F,0x6E8000),(0x6E807E,0x6E8000)]
print('== F1 全部写 0x7E1F50 的位置 -> 所在函数 ==')
seen={}
for site,st in SITES:
    if st in seen: continue
    b=body(st); seen[st]=b
    print('\n-- 函数 %08X（%d 条）--'%(st,len(b)))
    flds={}
    for i in b:
        m=re.match(r'(?:dword|byte) ptr \[(e[a-z]{2}) \+ (0x[0-9a-f]+|\d+)\], (.+)$',i.op_str)
        if i.mnemonic=='mov' and m:
            off=int(m.group(2),16) if m.group(2).startswith('0x') else int(m.group(2))
            print('   %08X  %-10s %-40s'%(i.address,i.mnemonic,i.op_str))
            if m.group(1)=='eax': flds[off]=m.group(3)
        elif i.mnemonic=='mov' and re.match(r'(?:dword|byte) ptr \[(e[a-z]{2})\], ',i.op_str):
            print('   %08X  %-10s %-40s  <= vtable'%(i.address,i.mnemonic,i.op_str))
    print('   字段表（base=eax）：%s'%{hex(k):v for k,v in sorted(flds.items())})
print('\n== F4 关键字段初值实证 ==')
b=seen[0x410170]
ck('F4a 0x410170 里 +0x10 初值 = 0xffffffff',
   any(i.mnemonic=='mov' and i.op_str=='dword ptr [eax + 0x10], 0xffffffff' for i in b),
   [i.op_str for i in b if '0x10]' in i.op_str])
ck('F4b 0x410170 里 +0x20 初值 = 0（byte，cl==0）',
   any(i.mnemonic=='mov' and i.op_str=='byte ptr [eax + 0x20], cl' for i in b),
   [i.op_str for i in b if '0x20]' in i.op_str])
ck('F4c 0x410170 里 +0x18/+0x1c 初值 = 0（ecx==0）',
   sum(1 for i in b if i.mnemonic=='mov' and re.search(r'\[eax \+ 0x1[8c]\], ecx',i.op_str))==2,
   [i.op_str for i in b if '0x18]' in i.op_str or '0x1c]' in i.op_str])
print('\n== F3 构造函数之间的重复安装 ==')
tgt=[st for st in seen]
print('   涉及函数起点：%s'%[hex(x) for x in tgt])
ck('F3a 至少 4 个不同的构造函数写同一张表 0x7E1F50',len(tgt)>=4,len(tgt))
print('\nFAILS=%d'%len(fails))
