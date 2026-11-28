#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 第十七刀：把 +0x10 / +0x20 两字段的「八、字节、读、写」四面闭合。
G1 +0x10 的写入面：全 .text 里 [reg+0x10] 的 mov 立即数 -1 / 0 写入点。
G2 +0x10 的读取面：L 血统里槽 4 目标就读 [this+0x20]（R193 已闭合）；本轮补 +0x10 的读取实现。
G3 +0x20 的写入面：byte 写 0 / 1 的点。
G4 槽 18..23（0x4104C0/0x4104F0/0x410520/0x410530/0x410540/0x410570）字节本体：
   它们不在 R194 的 11 核里，但属于 L 的槽 18-23 默认实现，本轮补齐。
G5 断言：0x7E1F50 的槽 18..23 目标就是 G4 的六个地址。
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
def in_text(x): return x is not None and LO<=x<P.B['.text']['hi_file']
print('== G4 槽 18..23 的默认实现字节本体 ==')
VT=0x7E1F50
for s in range(18,24):
    t=P.dw(VT+4*s)
    b=body(t); nb=b[-1].address+len(b[-1].bytes)-t
    print('\n-- 槽 %d  %08X  %d 条 / %d 字节 --'%(s,t,len(b),nb))
    print('   '+P.RAW[P.r2o(t):P.r2o(t)+nb].hex())
    for i in b: print('   %08X  %-10s %s'%(i.address,i.mnemonic,i.op_str))
print('\n== G1 +0x10 的立即数写 ==')
w10=[]
CH=262144;o=0;tot=T['rawsize']
while o<tot:
    n=min(CH,tot-o);buf=P.RAW[T['rawptr']+o:T['rawptr']+o+n];va=LO+o;i=0
    while i<len(buf):
        got=False
        for ins in md.disasm_lite(buf[i:i+16],va+i):
            if ins[2]=='mov' and re.match(r'dword ptr \[e[a-z]{2} \+ (0x10|16)\], (0xffffffff|0)$',ins[3]):
                w10.append((ins[0],ins[3]))
            i+=ins[1];got=True;break
        if not got:i+=1
    o+=n
print('   [reg+0x10] 写 -1 或 0 的点：%d 处  前 8 %s'%(len(w10),[hex(a) for a,_ in w10[:8]]))
ck('G1a 存在 [reg+0x10] <- 0xffffffff 的写入点',any('0xffffffff' in o for _,o in w10),len(w10))
print('\nFAILS=%d'%len(fails))
