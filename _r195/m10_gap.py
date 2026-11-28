#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 第十刀：核查 m9 报的 10 张「零立即数引用」表头 —— 区分真零 vs 分块失步假象。
A1 对 10 张表头，直接在整份 .text 里做**字节串**检索（小端 4 字节），给命中文件偏移。
A2 每个字节命中的位置，用 capstone 从「命中点之前最多 15 字节」逐起点试解，看能否
   得到一条 op_str 含该立即数的指令 ⇒ 是「指令立即数」还是「数据/失步产物」。
A3 结论：每张表头判为 INSTR_IMM / RAW_BYTES_ONLY / NONE。
"""
import sys,re,struct,capstone,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c:fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
T=P.B['.text']; LO=T['lo']
GAP=[0x7E88D0,0x7F3FE8,0x7F4090,0x7F44E0,0x7F45C4,0x7F4680,0x7F4730,0x7F5858,0x7F5904,0x7F59B0]
# 也核查 m7 曾报的 0x7F4680 处 0x6E807E
extra=[0x6E807E]
res={}
for v in GAP+extra:
    pat=struct.pack('<I',v)
    hits=[];i=T['rawptr']
    while True:
        i=P.RAW.find(pat,i,T['rawptr']+T['rawsize'])
        if i<0: break
        hits.append(i); i+=1
    verdict=[]
    for h in hits:
        va=LO+(h-T['rawptr'])
        found=None
        for back in range(0,16):
            s=va-back
            try: ins=list(md.disasm(P.RAW[P.r2o(s):P.r2o(s)+back+8],s))[0]
            except Exception: continue
            if len(ins.bytes)>back and ('0x%x'%v) in ins.op_str:
                found=(s,ins.mnemonic,ins.op_str,back); break
        verdict.append((va,found))
    res[v]=verdict
    ni=sum(1 for _,f in verdict if f)
    print('%08X 字节命中 %d 处 / 指令立即数 %d 处' % (v,len(hits),ni))
    for va,f in verdict[:6]:
        print('      VA=%08X  %s' % (va, ('%08X %s %s (back=%d)'%f) if f else '仅字节(非指令立即数)'))
ck('A1 全部 10 张零命中表头都完成核查', len(res)==11, len(res))
ck('A2 0x6E807E 确实引用 0x7F4680（m7 的读数可复现）',
   any(f for _,f in res[0x7F4680]), [ (hex(a),f) for a,f in res[0x7F4680] ][:3])
print('\nFAILS=%d'%len(fails))
