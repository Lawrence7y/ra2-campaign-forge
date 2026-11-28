#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 第五刀：AbstractClass 主表（0x7E1F50）的槽位全图 + 槽 0 目标 0x410260 的调用约定核验。
V1 0x7E1F50 起连续落 .text 的槽（前缀长度），逐槽目标 + 体长 + 首字节。
V2 0x410260 的 GUID 常量周边的字符串（判断该 GUID 是否有伴随名字）。
V3 0x7C8B3D（0x4105A0 里的第三个 call）身份：体前 12 条。
V4 0x410260 的 4 个 GUID 分别与哪些 vtable 的地址邻近（判断它们是否是表前导的 IID 数组）。
"""
import sys, re, struct, capstone
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c:fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI
def nslot(vt,cap=400):
    k=0
    while k<cap and in_text(P.dw(vt+4*k)): k+=1
    return k
VT=0x7E1F50
n=nslot(VT)
print('== V1 0x7E1F50 槽数 = %d ==' % n)
zero=[]
for s in range(n):
    t=P.dw(VT+4*s)
    o=P.r2o(t)
    ins=[]
    for i in md.disasm(P.RAW[o:o+64],t):
        ins.append((i.address,i.mnemonic,i.op_str))
        if i.mnemonic.startswith('ret'): break
    nb=ins[-1][0]+len(md.disasm(P.RAW[o+ (ins[-1][0]-t):o+(ins[-1][0]-t)+15],ins[-1][0]).__next__().bytes)-t
    print('  槽 %2d  %08X  %-34s ret=%s' % (s,t,' ; '.join('%s %s'%(m,x) for _,m,x in ins[:3]), ins[-1][2] or '0'))
    if s==0: zero=ins
print('\n== V3 0x7C8B3D 体（0x4105A0 的第三个 call）==')
o=P.r2o(0x7C8B3D)
for k,i in enumerate(md.disasm(P.RAW[o:o+64],0x7C8B3D)):
    print('   %08X  %-8s %s' % (i.address,i.mnemonic,i.op_str))
    if i.mnemonic.startswith('ret') or k>11: break
print('\n== V2 GUID 周边字符串 ==')
for g in (0x7E9AE0,0x7F7C90,0x7F7C80,0x7F7C70):
    for d in (-64,-32,32,64):
        s=P.cstr(g+d,48)
        print('   %08X%+5d -> %r' % (g,d,s))
print('\nFAILS=%d'%len(fails))
