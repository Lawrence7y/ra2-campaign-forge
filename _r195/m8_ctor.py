#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 第八刀：L 的 78 张表全部安装路径闭合（不只 C7 立即数）。
Y1 0x410198 / 0x4101D0 / 0x6E803F / 0x6E807E 四处命中的所在函数体（CFG 感知）。
Y2 每张 L 表头的「安装路径分类」：C7 立即数 / 指针表（.rdata/.data 中指向它的 dword）/ 都不是。
Y3 指针表口径下：引用它的 dword 地址 + 该 dword 是否被 C7 立即数或 mov reg,imm 使用。
Y4 0x7E1F50 与 0x7F4680 两个 C7 安装者的关系。
"""
import sys,re,struct,collections,capstone,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c:fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI
def dis1(va,maxb=16):
    o=P.r2o(va); 
    for i in md.disasm(P.RAW[o:o+maxb],va): return i
    return None
def cfg(va,maxins=200,maxb=2048):
    seen={};work=[va]
    while work:
        a=work.pop()
        while True:
            if a in seen or len(seen)>=maxins or a<va or a>=va+maxb: break
            i=dis1(a)
            if i is None: break
            seen[a]=i
            if i.mnemonic.startswith('ret'): break
            if i.mnemonic=='jmp' and i.operands[0].type==capstone.x86.X86_OP_IMM:
                a=i.operands[0].imm; continue
            if i.mnemonic.startswith('j') and i.operands and i.operands[0].type==capstone.x86.X86_OP_IMM:
                work.append(i.operands[0].imm)
            a=i.address+len(i.bytes)
    return [seen[k] for k in sorted(seen)]
# 函数起点反推：从命中地址向前找可识别的入口
def back_start(va,limit=256):
    o=P.r2o(va)
    # 用 int3/nop 填充或 push ebp/ mov edi,edi 形态向前找
    for d in range(0,limit,1):
        a=va-d
        if a<LO: break
        i=dis1(a)
        if i is None: continue
        if i.address==a and (i.mnemonic in ('push','mov','sub','xor') ) and d>0:
            prev=P.RAW[P.r2o(a)-2:P.r2o(a)]
            if prev==b'\xcc\xcc' or prev==b'\x90\x90': return a
    return None
print('== Y1 四处 C7 命中的函数体 ==')
for a in (0x410198,0x4101D0,0x6E803F,0x6E807E):
    s=back_start(a) or (0x410190 if a<0x410200 else 0x6E7FF0)
    print('\n-- 命中 %08X  推定入口 %08X --'%(a,s))
    for i in cfg(s)[:40]:
        print('   %08X  %-8s %s'%(i.address,i.mnemonic,i.op_str))
print('\nFAILS=%d'%len(fails))
