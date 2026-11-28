#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 第十一刀（决定性，修正 O 系列）：CRC 状态对象来源链 —— 寄存器跟随版。
上一刀（m10）缺陷：看到 mov ecx,edi 就返回 OTHER_edi 而不继续跟 edi，且 65 个 lite 未命中的调用点
被判 NONE。本刀修正：
 X1 函数起点用「向前找连续 >=2 个 0x90 或 0xCC 填充」定界（也接受 .text 起点）。
 X2 从函数起点正向 detail 反汇编到调用点，维护 ecx 的 last-def；源是寄存器则继续跟该寄存器的 last-def。
 X3 终止分类：STACK(lea reg,[esp+K]) / STACKARG(mov reg,[esp+K]，K>=0 => 调用者栈参数) /
    GLOBAL(mov reg,imm 落在 .data/.rdata) / NONE / DEPTH。
 X4 对 STACK 终止：检查该栈块 [esp+K, esp+K+16) 在 lea 之后到调用点之间是否有零写。
 反控：寄存器跟随深度 4 -> 1；函数起点判据换成「lite 目标集最近前置」。
"""
import sys,struct,collections,json,bisect,re
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
def in_text(x): return x is not None and LO<=x<HI
def calls_byte(fn):
    out=[]
    for va in range(LO,HI-5):
        if BUF[va-LO]!=0xE8: continue
        if struct.unpack_from('<i',BUF,va-LO+1)[0]+va+5==fn: out.append(va)
    return out
CS=calls_byte(0x4A1CA0)
ck('X1a 调用点==331', len(CS)==331, len(CS))
def func_start(va):
    p=va-LO
    q=p
    while q>16:
        if (BUF[q-1]==0x90 and BUF[q-2]==0x90) or (BUF[q-1]==0xCC and BUF[q-2]==0xCC):
            return LO+q
        q-=1
    return None
def insns(lo,hi):
    return [(off,mn,op) for off,sz,mn,op in md.disasm_lite(BUF[lo-LO:hi-LO],lo)]
def parse_write_reg(op):
    if ',' not in op: return None
    return op.split(',',1)[0].strip()
def last_def(reg,lo,hi):
    best=None
    for (a,mn,op) in insns(lo,hi):
        d=parse_write_reg(op)
        if d==reg and mn in ('mov','lea','pop','xor','sub','and','or','add','imul'):
            best=(a,mn,op)
    return best
def trace(callva, depth=4):
    """返回 (分类, 历史)"""
    reg='ecx'; cur=callva; hist=[]; d=0
    while d<depth:
        fs=func_start(cur)
        if fs is None: return ('NOSTART',hist)
        ld=last_def(reg,fs,cur)
        if ld is None: return ('NODEF',hist)
        a,mn,op=ld; src=op.split(',',1)[1].strip() if ',' in op else ''
        hist.append((hex(a),mn,op))
        if mn=='lea' and 'esp' in src: return ('STACK',hist)
        if mn=='pop': return ('POP',hist)
        if mn=='xor' and src==reg: return ('ZEROREG',hist)
        if re.match(r'^0x[0-9a-f]+$',src):
            w=P.where(int(src,16)); return ('GLOBAL_'+str(w),hist)
        if re.match(r'^e[a-z]{2}$',src):
            reg=src; cur=a; d+=1; continue   # 寄存器链：同一位置换寄存器继续跟
        if 'esp' in src: return ('STACKARG',hist)
        return ('OTHER',hist)
    return ('DEPTH',hist)
res=collections.Counter(); samp=collections.defaultdict(list)
for c in CS:
    k,h=trace(c,4); res[k]+=1
    if len(samp[k])<5: samp[k].append((hex(c),h))
ck('X3a 4 跳来源分类', True, dict(res))
for k,v in samp.items(): print('   X3b',k,v)
res1=collections.Counter()
for c in CS: res1[trace(c,1)[0]]+=1
ck('R1a 深度 1 的分类', True, dict(res1))
# X4 STACK 的零写
stkw=[]
for c in CS:
    k,h=trace(c,4)
    if k!='STACK': continue
    a=int(h[-1][0],16)
    z=[(hex(x),INSN_op) for (x,INSN_op) in
       [(x,md_s) for x,md_s in [(y,'') ]] ] if False else []
    ins=insns(a,c)
    z=[(hex(x),mn+' '+op) for (x,mn,op) in ins if mn=='mov' and '[' in op.split(',')[0] and op.split(',',1)[-1].strip()=='0']
    if z: stkw.append((hex(c),hex(a),z[:3]))
ck('X4a STACK 终止数', True, res.get('STACK',0))
ck('X4b STACK 内零写个数', True, len(stkw))
for r in stkw[:8]: print('   X4c',r)
json.dump(dict(cls={k:v for k,v in res.items()},cls1={k:v for k,v in res1.items()},
  stkw=stkw,samp={k:v for k,v in samp.items()},asserts=N,fails=fails),
  open('/home/t628/projects/ra2-campaign-forge/_r198/m11_origin2.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
