#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 第六刀：调用约定实证（关键：槽 4 = 0x410450 用 [esp+4] 取对象，槽 13 = 0x410410 用 ecx 取 this）。
W1 逐个默认实现的「对象指针来路」：是 ecx（thiscall）还是 [esp+N]（显式 this 的 stdcall）。
W2 反汇编扫描：找出所有间接调用的 vtbl 偏移，统计 [reg+0x10]（槽 4）与 [reg+0x34]（槽 13）的调用点数。
W3 对 [reg+0x34] 的调用点反汇编前 24 字节，看 push 了什么（是否把对象压栈）。
W4 结论断言。
"""
import sys, re, struct, collections, capstone
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c:fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def body(va,maxb=256):
    o=P.r2o(va); out=[]
    for i in md.disasm(P.RAW[o:o+maxb],va):
        out.append(i)
        if i.mnemonic.startswith('ret'): break
    return out
FAM=[0x410260,0x410300,0x410310,0x4C9150,0x410450,0x4103E0,0x410470,0x410480,
     0x410490,0x4104A0,0x4104B0,0x410440,0x410410,0x4105A0]
print('== W1 对象指针来路 ==')
for va in FAM:
    b=body(va)
    ecx_use=[i for i in b if re.search(r'\becx\b',i.op_str) and i.mnemonic in ('mov','lea')]
    # 是否一进来就 mov esi,ecx / 直接把 ecx 当 this
    this_ecx=any(i.mnemonic=='mov' and i.op_str.startswith(('esi, ecx','edi, ecx','eax, ecx')) for i in b[:3])
    stack_this=any(i.mnemonic=='mov' and re.match(r'e[a-z]{2}, dword ptr \[esp \+ (0x)?(4|8|c)\]',i.op_str) for i in b[:4])
    print('   %08X this_ecx=%-5s stack_this=%-5s 首3条=%s' %
          (va,this_ecx,stack_this,' ; '.join('%s %s'%(i.mnemonic,i.op_str) for i in b[:3])))
# W2 间接调用面：全段 lite 扫描 call/jmp [reg+off]
ind=collections.defaultdict(list)
for ins in md.disasm_lite(P.RAW[T['rawptr']:T['rawptr']+T['rawsize']],LO):
    a,mn,op=ins[0],ins[2],ins[3]
    if mn in ('call','jmp') and op.startswith(('dword ptr [',)):
        m=re.search(r'\+ (0x[0-9a-f]+)\]',op)
        if m: ind[int(m.group(1),16)].append((a,mn,op))
print('\n== W2 间接调用 vtbl 偏移 Top12 ==')
for off,c in collections.Counter({k:len(v) for k,v in ind.items()}).most_common(12):
    print('   +%03X (%2d 号槽) %4d 处  首个 %s' % (off,off//4,c,[hex(x[0]) for x in ind[off][:3]]))
print('\n== W3 槽 4 (+0x10) 与槽 13 (+0x34) 的调用点上下文 ==')
for off in (0x10,0x34):
    for a,mn,op in ind.get(off,[])[:3]:
        s=max(LO,a-24); o=P.r2o(s)
        ctx=[]
        for i in md.disasm(P.RAW[o:o+40],s):
            ctx.append('%s %s'%(i.mnemonic,i.op_str))
            if i.address>=a: break
        print('   +0x%02X @%08X : %s' % (off,a,' ; '.join(ctx[-5:])))
ck('W2a 槽 4 间接调用存在', len(ind.get(0x10,[]))>0, len(ind.get(0x10,[])))
ck('W2b 槽 13 间接调用存在', len(ind.get(0x34,[]))>0, len(ind.get(0x34,[])))
print('\nFAILS=%d'%len(fails))
