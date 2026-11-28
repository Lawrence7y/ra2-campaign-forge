#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 第十九刀（收口）：三个静态默认值全局的读写面 + 0x410110 函数体 + 全轮断言汇总。
J1 0x887680/4/8 的 .data 归属：rawsize 边界内外（BSS 判定）+ 文件内初值。
J2 三处 imm 引用（0x410113/0x410118/0x41011d 与 0x4104c6/0x4104d0/0x4104d9）的读写形态。
J3 是否存在对这三个全局的写（mov [abs],reg / mov [abs],imm）。
J4 0x410110 所在函数体（CFG）+ 0x4104C0 体。
J5 全轮关键数字汇总（供台账与看板引用）。
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
T=P.B['.text']; LO=T['lo']; D=P.B['.data']
G=(0x887680,0x887684,0x887688)
print('== J1 .data 段边界 ==')
print('   .data lo=%08X rawsize=%08X hi_file=%08X vsize=%08X hi_virt=%08X'%(D['lo'],D['rawsize'],D['hi_file'],D['vsize'],D['hi_virt']))
for g in G:
    print('   %08X -> where=%s  in_raw=%s'%(g,P.where(g),g<D['hi_file']))
ck('J1a 三个全局都落在 .data 的 vsize 内但 rawsize 外（BSS）',
   all(D['lo']<=g<D['hi_virt'] and g>=D['hi_file'] for g in G),
   [(hex(g),g>=D['hi_file']) for g in G])
print('\n== J2/J3 三个全局的全部 .text 引用与形态 ==')
CH=262144;o=0;tot=T['rawsize'];refs=collections.defaultdict(list)
while o<tot:
    n=min(CH,tot-o);buf=P.RAW[T['rawptr']+o:T['rawptr']+o+n];va=LO+o;i=0
    while i<len(buf):
        got=False
        for ins in md.disasm_lite(buf[i:i+16],va+i):
            for g in G:
                if '0x%x'%g in ins[3]: refs[g].append((ins[0],ins[2],ins[3]))
            i+=ins[1];got=True;break
        if not got:i+=1
    o+=n
for g in G:
    print('   %08X : %d 处'%(g,len(refs[g])))
    for a,mn,op in refs[g]: print('      %08X  %-8s %s'%(a,mn,op))
writes=[(g,a,mn,op) for g in G for a,mn,op in refs[g] if mn=='mov' and re.match(r'dword ptr \[0x',op)]
print('   写形态（mov [abs],...）：%d 条'%len(writes))
ck('J3a 三个全局在 .text 内无任何写（只读）',len(writes)==0,len(writes))
print('\n== J4 0x410110 / 0x4104C0 体 ==')
def body(va,maxb=256):
    o=P.r2o(va);out=[]
    for ins in md.disasm(P.RAW[o:o+maxb],va):
        out.append(ins)
        if ins.mnemonic.startswith('ret'):break
    return out
for va in (0x410110,0x4104C0):
    b=body(va)
    print('\n-- %08X  %d 条 --'%(va,len(b)))
    print('   '+P.RAW[P.r2o(va):P.r2o(va)+ (b[-1].address+len(b[-1].bytes)-va)].hex())
    for i in b: print('   %08X  %-10s %s'%(i.address,i.mnemonic,i.op_str))
print('\n== J5 全轮关键数字 ==')
print('   L 表头 78 / 主表 954 / 子表 260 / COL 1214 / 槽总 14044')
print('   L 表头的指令级立即数安装点 341 条 / 零命中 0 张 / 形态全为 mov[mem],imm')
print('   0x4A1CA0 调用面：线性口径 331（与 R194 上界 U=331 相等）')
print('   0x4A1CA0 体 55 条 / 134 字节 / 槽位 {0,4,8,0xC} / not 2 次')
print('   0x4A1DE0 体 174 条 / 448 字节 / 槽位 {0,4,8,0xC}')
print('   0x7E1F50 槽数 24（槽 0..23 全给出默认实现）')
print('   AbstractClass 构造函数 5 个：0x410170 / 0x4101C0 / 0x4101E0 / 0x4105A0 / 0x6E8000(+0x6E801F0)')
print('\nFAILS=%d'%len(fails))
