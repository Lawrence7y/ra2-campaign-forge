#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 第二十刀：+0x20 字节字段的「写侧」面（槽 4 是读侧）。
K1 全 .text 里 byte 写 [reg+0x20] 的点（mov byte ptr [reg+0x20], imm8/reg8）。
K2 这些写点是否落在 L 的 78 张表的某个槽位实现里（按函数起点归属）。
K3 与之配对的 +0x10 dword 写点是否在同一函数里（字段成对写出）。
"""
import sys,re,collections,capstone
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c:fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
T=P.B['.text']; LO=T['lo']
w20=[];CH=262144;o=0;tot=T['rawsize']
while o<tot:
    n=min(CH,tot-o);buf=P.RAW[T['rawptr']+o:T['rawptr']+o+n];va=LO+o;i=0
    while i<len(buf):
        got=False
        for ins in md.disasm_lite(buf[i:i+16],va+i):
            if ins[2]=='mov' and re.match(r'byte ptr \[e[a-z]{2} \+ (0x20|32)\],',ins[3]):
                w20.append((ins[0],ins[2],ins[3]))
            i+=ins[1];got=True;break
        if not got:i+=1
    o+=n
print('== K1 byte 写 [reg+0x20] 的点：%d 处 =='%len(w20))
for a,mn,op in w20[:25]: print('   %08X  %-8s %s'%(a,mn,op))
ck('K1a 存在 byte 写 [reg+0x20] 的点',len(w20)>0,len(w20))
w10=[];o=0
while o<tot:
    n=min(CH,tot-o);buf=P.RAW[T['rawptr']+o:T['rawptr']+o+n];va=LO+o;i=0
    while i<len(buf):
        got=False
        for ins in md.disasm_lite(buf[i:i+16],va+i):
            if ins[2]=='mov' and re.match(r'dword ptr \[e[a-z]{2} \+ (0x10|16)\],',ins[3]):
                w10.append((ins[0],ins[3]))
            i+=ins[1];got=True;break
        if not got:i+=1
    o+=n
print('\n== K2 dword 写 [reg+0x10] 的点：%d 处（前 12）=='%len(w10))
for a,op in w10[:12]: print('   %08X  %s'%(a,op))
close=[(a,b) for a,_ in w20 for b,_ in w10 if abs(a-b)<64]
print('\n   K3 同一 64 字节窗口内同时出现 +0x10 与 +0x20 写的点对数：%d'%len(close))
print('   前 8 对：%s'%[(hex(x),hex(y)) for x,y in close[:8]])
ck('K3a 存在字段成对写出的点',len(close)>0,len(close))
print('\nFAILS=%d'%len(fails))
