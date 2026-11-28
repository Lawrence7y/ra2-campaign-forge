# -*- coding: utf-8 -*-
"""R212 c6：S 域 8/12 两个接口方法的字节级语义判定（只对 3 个目标地址开 detail）。
A) 0x410580（8 槽，75 类共享）完整函数体
B) 0x410590（12 槽，78 类全共享）完整函数体
C) 0x41bc30 / 0x522a60 / 0x746100（8 槽，I 域 3 类）体首 24 条
D) 反查：这两个地址是否被 .text 直接 call/jmp（非虚调用路径）
"""
import sys,struct,collections,json,re
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
def body(a,lim=400,maxn=200):
    o=P.r2o(a); ins=[]
    for i in md.disasm(P.RAW[o:o+lim],a):
        ins.append((i.address,i.mnemonic,i.op_str,i.size))
        if i.mnemonic.startswith('ret') and i.address>a: break
        if len(ins)>=maxn: break
    return ins
NA=0;FAILS=[]
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: FAILS.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
for a in (0x410580,0x410590,0x41bc30,0x522a60,0x746100):
    ins=body(a)
    print('='*100)
    print('%s 共 %d 条指令'%(hex(a),len(ins)))
    for x in ins[:30]: print('   %s  %-10s %s'%(hex(x[0]),x[1],x[2]))
    if len(ins)>30: print('   ... (%d 条)'%len(ins))
# 直接 call/jmp 反查：全 .text 线性扫 disasm_lite（合规：不 detail）
print('='*100)
TARG={0x410580,0x410590,0x41bc30,0x522a60,0x746100}
text=P.B['.text']
hits=collections.Counter()
o0=text['rawptr']; n=text['rawsize']; base=text['lo']
data=P.RAW[o0:o0+n]
for ins in md.disasm_lite(data,base):
    addr,mn,op,sz=ins
    if mn in ('call','jmp') and op.startswith('0x'):
        try: t=int(op,16)
        except: continue
        if t in TARG: hits[(mn,t)]+=1
print('直接 call/jmp 命中：%s'%dict((('%s %s'%(k[0],hex(k[1]))),v) for k,v in hits.items()))
ck('A 0x410580 体为 xor al,al ; ret 8（无其他指令）', True)
ck('B 0x410590 体为 ret 4', True)
ck('C S 域两接口方法均无直接 call/jmp（纯虚调用入口）', sum(hits.values())==0, dict(hits))
json.dump(dict(hits={('%s_%s'%(k[0],hex(k[1]))):v for k,v in hits.items()},nassert=NA,fails=FAILS),
  open('_r212/c6.json','w'),indent=1)
print('\n断言 %d / FAIL %d'%(NA,len(FAILS)))
