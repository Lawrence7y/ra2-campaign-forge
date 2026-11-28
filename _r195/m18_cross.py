#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 第十八刀：L 的槽 18..23 的**内部互相调用**实证（R194 只做到槽 0..17）。
H1 0x7E1F50 的槽 18 目标 = 0x4104C0，槽 19/22 体内 call [eax+0x48]（= 槽 18）。
H2 全 1214 张表里 call [reg+0x48] 的调用点数（跨表验证槽 18 是「取三元组」的接口方法）。
H3 槽 18 从 0x887680/0x887684/0x887688 三个全局取初值 —— 这三个全局的字节与归属。
H4 三个全局是否在 .data 内被其它地方写（初值来源）。
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
print('== H1 槽 18 目标与 19/22 的复用 ==')
for s in (18,19,20,21,22,23):
    t=P.dw(0x7E1F50+4*s)
    b=body(t)
    calls=[i.op_str for i in b if i.mnemonic=='call']
    print('   槽 %2d -> %08X  calls=%s'%(s,t,calls))
ck('H1a 槽 18 == 0x4104C0',P.dw(0x7E1F50+4*18)==0x4104C0,hex(P.dw(0x7E1F50+4*18)))
ck('H1b 槽 19 与槽 22 都 call [eax+0x48]',
   all(any(i.op_str=='dword ptr [eax + 0x48]' for i in body(P.dw(0x7E1F50+4*s))) for s in (19,22)),True)
print('\n== H2 全段 call [reg+0x48] 调用点数 ==')
cnt=0;addrs=[]
CH=262144;o=0;tot=T['rawsize']
while o<tot:
    n=min(CH,tot-o);buf=P.RAW[T['rawptr']+o:T['rawptr']+o+n];va=LO+o;i=0
    while i<len(buf):
        got=False
        for ins in md.disasm_lite(buf[i:i+16],va+i):
            if ins[2]=='call' and re.match(r'dword ptr \[e[a-z]{2} \+ (0x48|72)\]',ins[3]):
                cnt+=1; addrs.append(ins[0])
            i+=ins[1];got=True;break
        if not got:i+=1
    o+=n
print('   %d 处  前 8 %s'%(cnt,[hex(a) for a in addrs[:8]]))
ck('H2a call [reg+0x48] 存在',cnt>0,cnt)
print('\n== H3/H4 三个全局 0x887680/4/8 ==')
for g in (0x887680,0x887684,0x887688):
    print('   %08X = %08X  (%s)'%(g,P.dw(g) or 0,P.where(P.dw(g))))
print('   全段对这些全局的 imm 引用：')
for g in (0x887680,0x887684,0x887688):
    hits=[];o2=T['rawptr']
    pat=struct.pack('<I',g); i=o2
    while True:
        i=P.RAW.find(pat,i,T['rawptr']+T['rawsize'])
        if i<0:break
        hits.append(LO+(i-T['rawptr']));i+=1
    print('      %08X : %d 处 %s'%(g,len(hits),[hex(x) for x in hits[:6]]))
print('\n== H5 0x887680 附近（.data 起始段）数据形态 ==')
base=P.r2o(0x887670)
print('   '+P.RAW[base:base+48].hex())
for k in range(0,48,4):
    v=struct.unpack_from('<I',P.RAW,base+k)[0]
    print('   %08X = %08X  %s'%(0x887670+k,v,P.where(v)))
print('\nFAILS=%d'%len(fails))
