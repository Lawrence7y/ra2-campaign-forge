#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 第十四刀：0x4A1CA0 / 0x4A1DE0 / 0x4A1FB0 三例程的**逐条字节本体**（detail 单址）。
核对 R194 报的「状态对象四槽 +0/+4/+8/+0xC」是否成立；若不成立给实测定稿。
"""
import sys,re,capstone
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c:fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
def body(va,maxb=1200):
    o=P.r2o(va); out=[]
    for ins in md.disasm(P.RAW[o:o+maxb],va):
        out.append(ins)
        if ins.mnemonic.startswith('ret'): break
    return out
for va in (0x4A1CA0,0x4A1D50,0x4A1DE0,0x4A1FB0):
    b=body(va); nb=b[-1].address+len(b[-1].bytes)-va
    print('\n===== %08X  %d 条 / %d 字节 ====='%(va,len(b),nb))
    print('    '+P.RAW[P.r2o(va):P.r2o(va)+nb].hex())
    for i in b:
        print('    %08X  %-10s %s'%(i.address,i.mnemonic,i.op_str))
    print('    -- 寄存器偏移图 --')
    for reg in ('ecx','esi','edx','eax'):
        offs=sorted({int(m,16) for i in b for m in re.findall(r'\[%s \+ (0x[0-9a-f]+)\]'%reg,i.op_str)})
        if offs: print('       [%s+..] = %s'%(reg,[hex(x) for x in offs]))
print('\nFAILS=%d'%len(fails))
