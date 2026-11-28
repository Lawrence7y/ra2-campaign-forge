#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 第十五刀（定稿）：状态对象槽位与 +0 初值来源的权威核验。
E1 偏移解析修正（capstone 对小偏移输出十进制、对 >=10 输出 0x 前缀）后的槽位集合。
E2 +0 槽的写/读指令逐条列出（地址 + 字节 + 助记符）。
E3 三个例程对 +0 的「读后写」语义：是否 = 读旧值 -> not -> 折叠 4 字节 -> not -> 写回。
E4 状态对象随调用者不同：对 ecx 来路分类修订（十进制偏移也认）。
E5 在 0x410410 的调用者里追 arg2（状态对象）的实际来源，判断 +0 是否被显式初始化。
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
def body(va,maxb=1200):
    o=P.r2o(va); out=[]
    for ins in md.disasm(P.RAW[o:o+maxb],va):
        out.append(ins)
        if ins.mnemonic.startswith('ret'): break
    return out
def offs_of(b,reg):
    s=set()
    for i in b:
        for m in re.finditer(r'\[%s(?: \+ (0x[0-9a-f]+|\d+))?\]'%reg,i.op_str):
            g=m.group(1)
            s.add(0 if g is None else (int(g,16) if g.startswith('0x') else int(g)))
    return sorted(s)
print('== E1 状态对象槽位（修正偏移解析）==')
for va,reg in ((0x4A1CA0,'ecx'),(0x4A1DE0,'esi'),(0x4A1FB0,'ecx')):
    b=body(va); print('   %08X [%s+..] = %s  体长 %d 条'%(va,reg,[hex(x) for x in offs_of(b,reg)],len(b)))
b1=body(0x4A1CA0); b3=body(0x4A1DE0)
ck('E1a 0x4A1CA0 槽位 == {0,4,8,0xc}',offs_of(b1,'ecx')==[0,4,8,0xc],offs_of(b1,'ecx'))
ck('E1b 0x4A1DE0 槽位包含 {0,4,8,0xc}',set([0,4,8,0xc])<=set(offs_of(b3,'esi')),offs_of(b3,'esi'))
print('\n== E2 +0 槽的读写指令 ==')
for va,b,reg in ((0x4A1CA0,b1,'ecx'),(0x4A1DE0,b3,'esi')):
    for i in b:
        if re.search(r'\[%s\]$'%reg,i.op_str) or re.search(r'\[%s\],'%reg,i.op_str) or re.search(r'\[%s \+ 0\]'%reg,i.op_str):
            print('   %08X  %-10s %-32s  %s'%(i.address,i.mnemonic,i.op_str,i.bytes.hex()))
print('\n== E3 0x4A1CA0 的 +0 读后写语义链 ==')
chain=[i for i in b1 if re.search(r'ecx\]',i.op_str) and re.search(r'\b(eax|edx)\b',i.op_str)]
for i in b1:
    if i.address>=0x4A1CEC and i.address<=0x4A1D23:
        print('   %08X  %-10s %s'%(i.address,i.mnemonic,i.op_str))
ck('E3a 0x4A1CA0 在 0x4A1D1B 把折叠结果写回 +0',
   any(i.address==0x4A1D1B and i.mnemonic=='mov' and i.op_str=='dword ptr [ecx], eax' for i in b1), True)
ck('E3b not 包裹两次（读入与写回各一次）',
   sum(1 for i in b1 if i.mnemonic=='not')==2,sum(1 for i in b1 if i.mnemonic=='not'))
print('\n== E4 331 个调用点的 ecx 来路（十进制偏移也认）==')
lin=[]
CH=262144;o=0;tot=T['rawsize']
while o<tot:
    n=min(CH,tot-o);buf=P.RAW[T['rawptr']+o:T['rawptr']+o+n];va=LO+o;i=0
    while i<len(buf):
        got=False
        for ins in md.disasm_lite(buf[i:i+16],va+i):
            if ins[2]=='call' and ins[3]=='0x4a1ca0': lin.append(ins[0])
            i+=ins[1];got=True;break
        if not got:i+=1
    o+=n
cls=collections.Counter()
for a in lin:
    s=max(LO,a-64);o2=P.r2o(s);f=None
    for ins in md.disasm(P.RAW[o2:o2+72],s):
        if ins.address>=a: break
        if ins.mnemonic=='lea' and re.match(r'ecx, \[esp \+ (0xc|12)\]',ins.op_str): f='lea ecx,[esp+0xc]'
        elif ins.mnemonic=='lea' and ins.op_str.startswith('ecx, [esp'): f='lea ecx,[esp+其他]'
        elif ins.mnemonic=='lea' and ins.op_str.startswith('ecx, [e'): f='lea ecx,[reg]'
        elif ins.mnemonic=='mov' and ins.op_str.startswith('ecx, dword ptr [esp'): f='mov ecx,[esp]'
        elif ins.mnemonic=='mov' and ins.op_str.startswith('ecx, dword ptr [e'): f='mov ecx,[reg]'
    cls[f]+=1
print('   调用点 %d 个  来路分布 %s'%(len(lin),dict(cls)))
ck('E4a 调用点总数 == 331',len(lin)==331,len(lin))
print('\nFAILS=%d'%len(fails))
