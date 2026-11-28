#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 主会话第一刀：L 的默认实现族（0x4102xx..0x4105B0 区块）逐函数字节本体。
只对个别地址开 detail，不做全段 detail 扫描（OOM 红线）。
T1 每个默认实现的入口/体长/指令数/首个 ret 立即数。
T2 体内 call/jmp 的直接落点，标出哪些落在本族内（族内委派图）。
T3 族内成员是否被非族内代码直接 call（即是否是真正的默认实现而非共享工具）。
T4 每个实现的「读写字段偏移」集合（[reg+imm]）。
"""
import sys, re, struct, collections, json, capstone
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c:fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
FAM=[0x410260,0x410300,0x410310,0x4C9150,0x410450,0x4103E0,0x410470,0x410480,
     0x410490,0x4104A0,0x4104B0,0x410440,0x410410,0x4105A0]
def body(va,maxb=768):
    o=P.r2o(va); out=[]
    for i in md.disasm(P.RAW[o:o+maxb],va):
        out.append(i)
        if i.mnemonic.startswith('ret'): break
    return out
B={va:body(va) for va in FAM}
rows={}
for va in FAM:
    b=B[va]
    ret_imm=None
    for i in b:
        if i.mnemonic=='ret':
            ret_imm=(i.op_str if i.op_str else '0')
    calls=[]
    for i in b:
        if i.mnemonic in ('call','jmp') and i.operands and i.operands[0].type==capstone.x86.X86_OP_IMM:
            calls.append((i.address,i.mnemonic,i.operands[0].imm))
    offs=sorted({int(m,16) for i in b for m in re.findall(r'\[(?:e[a-z]{2}|[a-z]{2}) \+ (0x[0-9a-f]+)\]',i.op_str)})
    rows[va]=dict(n=len(b),bytes=b[-1].address+ (4 if ret_imm and ret_imm not in('0',) else 1)-va,
                  ret=ret_imm,calls=calls,offs=offs,
                  mn=[(i.address,i.mnemonic,i.op_str) for i in b])
    print('%08X n=%2d end=%08X ret=%s' % (va,len(b),b[-1].address,ret_imm))
    for a,m,t in calls:
        tag='FAM' if t in B else ('TEXT' if LO<=t<HI else P.where(t))
        print('        %08X %s -> %08X %s' % (a,m,t,tag))
    print('        offs=%s' % ([hex(x) for x in offs]))

ck('T1a 14 个默认实现入口全部落 .text', all(LO<=v<HI for v in FAM), len(FAM))
ck('T1b 族内 ret 立即数齐全', all(rows[v]['ret'] is not None for v in FAM),
   {hex(v):rows[v]['ret'] for v in FAM})
json.dump({hex(k):{kk:(vv if kk!='mn' else [(a,m,o) for a,m,o in vv]) for kk,vv in r.items()} for k,r in rows.items()},
          open('_r195/m1_deffam.json','w'),indent=1)
print('\nFAILS=%d' % len(fails))
