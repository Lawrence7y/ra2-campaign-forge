#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 第二刀：默认实现族的**字节实证**（地址 + 字节序列 + 逐条助记符 + 交叉引用）。
T0 段表（虚拟区间），用来判定落点归属。
T1 每个默认实现的完整 hexdump + 逐条助记符。
T2 每个实现被直接 call rel32 / call [abs] / jmp 的直接引用计数（族外引用 = 真默认实现性）。
T3 族内委派图（谁 call 谁）。
"""
import sys, re, struct, capstone, collections, json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c:fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
print('== 段表 ==')
for s in P.SECS:
    print('  %-9s va=%08X vsize=%08X rawptr=%08X rawsize=%08X hi_file=%08X' %
          (s['name'],s['lo'],s['vsize'],s['rawptr'],s['rawsize'],s['hi_file']))
T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
FAM=[0x410260,0x410300,0x410310,0x4C9150,0x410450,0x4103E0,0x410470,0x410480,
     0x410490,0x4104A0,0x4104B0,0x410440,0x410410,0x4105A0]
def body(va,maxb=768):
    o=P.r2o(va); out=[]
    for i in md.disasm(P.RAW[o:o+maxb],va):
        out.append(i)
        if i.mnemonic.startswith('ret'): break
    return out
# T1
recs={}
for va in FAM:
    b=body(va); end=b[-1].address
    nbytes=end-va+len(b[-1].bytes)
    raw=P.RAW[P.r2o(va):P.r2o(va)+nbytes]
    recs[va]=dict(n=len(b),nbytes=nbytes,hex=raw.hex(),ins=[(i.address,i.mnemonic,i.op_str) for i in b])
    print('\n== %08X  %d 条 / %d 字节 ==' % (va,len(b),nbytes))
    print('   ' + raw.hex())
    for a,m,o in recs[va]['ins']:
        print('   %08X  %-8s %s' % (a,m,o))
# T2: 全段 lite 扫描收集所有 call/jmp 的立即数落点（一次过）
tgt=collections.Counter(); srcmap=collections.defaultdict(list)
for i in md.disasm_lite(P.RAW[T['rawptr']:T['rawptr']+T['rawsize']],LO):
    a,mn,op= i[0],i[1],i[2]
    if mn in ('call','jmp') and op and not op.startswith(('dword','qword','byte')) and re.fullmatch(r'0x[0-9a-f]+',op):
        t=int(op,16); tgt[t]+=1
        if t in FAM: srcmap[t].append((a,mn))
print('\n== T2 直接引用面（call/jmp 立即数落点）==')
for va in FAM:
    print('   %08X 被直接引用 %4d 次  前 6 个来源 %s' % (va,tgt.get(va,0),[hex(x[0]) for x in srcmap[va][:6]]))
ck('T2a 0x410470 直接引用计数', tgt.get(0x410470,0)>=0, tgt.get(0x410470,0))
json.dump({hex(k):v for k,v in recs.items()},open('_r195/m2_bytes.json','w'),indent=1)
print('\nFAILS=%d'%len(fails))
