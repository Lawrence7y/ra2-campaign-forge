# -*- coding: utf-8 -*-
"""R216 m1：逐槽反汇编 AbstractClass 主视图 0x7e1f50 的 24 个目标。
防 OOM：仅对 24 个命中地址各开 detail=True，单地址 <=256B 线性扫；不做全段 detail。
输出：每槽字节序列、指令、调用目标、全局/字段访问指纹。"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import *
from capstone.x86 import *
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
SLOTS=[0x00410260,0x00410300,0x00410310,0x004c9150,0x00410450,0x004c9150,0x004c9150,
       0x004103e0,0x004105a0,0x00410470,0x00410480,0x004c9150,0x004c9150,0x00410410,
       0x00410490,0x004104a0,0x004104b0,0x00410440,0x004104c0,0x004104f0,0x00410520,
       0x00410530,0x00410540,0x00410570]
def off(va):
    r=P.r2o(va)
    assert r is not None,hex(va)
    return r
def body(va,maxb=256):
    o=off(va); out=[]; end=None
    for i in md.disasm(P.RAW[o:o+maxb],va):
        out.append(i)
        if i.mnemonic.startswith('ret') or i.mnemonic=='jmp' and i.operands and i.operands[0].type==X86_OP_IMM:
            end=i.address+i.size; break
    return out,end
def fp(ins):
    calls=[];mems=[];imms=[]
    for op in ins.operands:
        if op.type==X86_OP_MEM:
            m=op.mem
            if m.base==X86_REG_INVALID and m.index==X86_REG_INVALID:
                mems.append('G%08x'%(m.disp&0xffffffff))
            else:
                mems.append('[%s%s+%d]'%(ins.reg_name(m.base) if m.base else '',
                          '+'+ins.reg_name(m.index) if m.index else '',m.disp))
    if ins.mnemonic in ('call','jmp'):
        o0=ins.operands[0]
        if o0.type==X86_OP_IMM: calls.append('I%08x'%(o0.imm&0xffffffff))
        elif o0.type==X86_OP_MEM: calls.append('M'+mems[0] if mems else 'M?')
        else: calls.append('R')
    return calls,mems
res=[]
for si,va in enumerate(SLOTS):
    ins,end=body(va)
    calls=[];mems=[]
    for i in ins:
        c,m=fp(i)
        calls+=c; mems+=m
    bx=P.RAW[off(va):off(va)+((end or va+64)-va)]
    res.append(dict(slot=si,va='0x%08x'%va,end='0x%08x'%(end or 0),n=len(ins),
        nbytes=(end or va)-va,bx=bx.hex(),calls=calls,mems=mems))
    print('--- slot%-2d 0x%08x  bytes=%d ins=%d'%(si,va,(end or va)-va,len(ins)))
    print('    bytes: %s'%(bx.hex() if len(bx)<=96 else bx[:96].hex()+'...'))
    for i in ins: print('    %08x  %-8s %s'%(i.address,i.mnemonic,i.op_str))
    print('    calls=%s mems=%s'%(calls[:8],mems[:10]))
json.dump(res,open('/home/t628/projects/ra2-campaign-forge/_r216/m1.json','w'),indent=1)
# 交叉统计
cb=collections.Counter(r['bx'] for r in res)
print('\n=== 汇总 ===')
print('distinct bytes=%d ; 相同字节组的槽=%s'%(len(cb),
      [[r['slot'] for r in res if r['bx']==k] for k,c in cb.items() if c>1]))
print('ret 形态:',collections.Counter([i.mnemonic+' '+i.op_str for r in res for i in [] ]))
gc=collections.Counter()
for r in res:
    for m in r['mems']:
        if m.startswith('G'): gc[m]+=1
print('全局引用 top20:',gc.most_common(20))
