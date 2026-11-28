#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 第三刀：CFG 感知的体提取（修 m2 的「遇首个 ret 即停」缺陷）。
跟着 jcc/jmp 的立即数目标继续解，直到所有可达路径都 ret；给出完整指令序列。
同时核验 0x4105A0 体内四个虚表安装立即数的身份（是不是 COL、修饰名是什么）。
"""
import sys, re, struct, collections, capstone, json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c:fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def dis1(va):
    o=P.r2o(va)
    if o is None: return None
    for i in md.disasm(P.RAW[o:o+16],va): return i
    return None
def cfg(va, maxins=120, maxb=1024):
    """从 va 起 BFS，跟 jcc/jmp 立即目标，全部路径 ret / 无出边时停。返回按地址排序的指令列表。"""
    seen={}; work=[va]; start=va
    while work:
        a=work.pop()
        while True:
            if a in seen or len(seen)>=maxins: break
            if a<start or a>=start+maxb: break
            i=dis1(a)
            if i is None: break
            seen[a]=i
            if i.mnemonic.startswith('ret'): break
            if i.mnemonic=='jmp' and i.operands and i.operands[0].type==capstone.x86.X86_OP_IMM:
                a=i.operands[0].imm; continue
            if i.mnemonic.startswith('j') and i.operands and i.operands[0].type==capstone.x86.X86_OP_IMM:
                work.append(i.operands[0].imm)
            a=i.address+len(i.bytes)
    return [seen[k] for k in sorted(seen)]
FAM=[0x410260,0x410300,0x410310,0x4C9150,0x410450,0x4103E0,0x410470,0x410480,
     0x410490,0x4104A0,0x4104B0,0x410440,0x410410,0x4105A0]
out={}
for va in FAM:
    ins=cfg(va)
    nb=ins[-1].address+len(ins[-1].bytes)-va
    raw=P.RAW[P.r2o(va):P.r2o(va)+nb]
    rets=[(i.address,i.op_str or '0') for i in ins if i.mnemonic.startswith('ret')]
    out[hex(va)]=dict(n=len(ins),nbytes=nb,hex=raw.hex(),rets=rets,
        ins=[[i.address,i.mnemonic,i.op_str] for i in ins])
    print('\n== %08X  %d 条 / %d 字节  ret=%s ==' % (va,len(ins),nb,rets))
    print('   '+raw.hex())
    for i in ins:
        print('   %08X  %-8s %s' % (i.address,i.mnemonic,i.op_str))
json.dump(out,open('_r195/m3_cfg.json','w'),indent=1)
# 0x4105A0 安装的四个立即数身份
print('\n== 0x4105A0 安装的虚表立即数身份 ==')
for imm in (0x7E1F50,0x7E1F34,0x7E1F2C,0x7E1F24):
    # COL 地址 = 该 dword 之前的 4 字节
    colva=P.dw(imm-4)
    nm=P.cstr(colva+8,160) if colva else None
    mdisp=P.dw(colva+4) if colva else None
    print('   imm=%08X  COL=%08X  mdisp=%s  name=%s' % (imm,colva or 0,mdisp,
          nm.decode('latin1') if nm else None))
print('\nFAILS=%d'%len(fails))
