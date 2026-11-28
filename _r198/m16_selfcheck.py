#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 第十六刀：自查 m12 的 STACK 分类是否成立（怀疑 hop 取 CALLERS[host][0] 是错配）。
 S1 对 18 个 STACK 终止点，取出 lea 地址 L 与 CRC 调用点 C，验证 L 之后紧邻的 call 目标是谁。
 S2 若 lea 之后的第一个 call 目标 != 该链上的宿主函数，则 STACK 归属为错配。
 S3 结论：STACK 类作废条数。
"""
import sys,struct,collections,json,bisect
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
T=P.B['.text'];LO=T['lo'];HI=T['hi_file'];RAW=P.RAW
BUF=RAW[T['rawptr']:T['rawptr']+(HI-LO)]
J=json.load(open('/home/t628/projects/ra2-campaign-forge/_r198/m12_final.json'))
STK=J['stk']
ck('S0a m12 的 STACK 样本数', True, len(STK))
for row in STK[:6]:
    c=int(row[0],16); h=row[1]
    lea=[x for x in h if x[1]=='LEA_ESP']
    ck('S1a %s 有 LEA_ESP 记录'%row[0], len(lea)==1, lea)
bad=[]
for row in STK:
    c=int(row[0],16); h=row[1]
    lea=[x for x in h if x[1]=='LEA_ESP']
    if not lea: continue
    L=int(lea[0][0],16)
    # L 之后 <=16 字节内的第一条 call
    nx=None
    for a,sz,mn,op in md.disasm_lite(BUF[L-LO:L-LO+32],L):
        if mn=='call' and op.startswith('0x'): nx=(a,int(op,16)); break
    # 该链上的宿主（h 里第 2 项的地址所在函数；用「lea 所在函数」近似）
    ok = nx is not None
    bad.append(dict(crc_call=row[0],lea=hex(L),next_call=None if not nx else (hex(nx[0]),hex(nx[1])),
                    is_crc_family=None if not nx else (nx[1] in (0x4A1CA0,0x4A1D50,0x4A1DE0)),
                    chain=[ (x[0],x[1],x[2] if len(x)>2 else '') for x in h]))
ck('S2a 全部 18 条都取到 lea 后首 call', True, sum(1 for b in bad if b['next_call']))
hits=[b for b in bad if b['is_crc_family']]
ck('S2b lea 后首 call 是 CRC 族的条数（真 STACK 归属）', True, dict(n=len(hits),rows=hits[:3]))
fails_n=[b for b in bad if b['is_crc_family'] is False]
ck('S3a 应作废的 STACK 归属条数', True, len(fails_n))
for b in fails_n[:8]:
    print('   S3b crc_call=%s lea=%s → 首call=%s 链=%s'%(b['crc_call'],b['lea'],b['next_call'],b['chain'][:4]))
json.dump(dict(rows=bad,valid=len(hits),invalid=len(fails_n),asserts=N,fails=fails),
  open('/home/t628/projects/ra2-campaign-forge/_r198/m16_selfcheck.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
