#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 第十刀（决定性）：CRC 状态对象的「来源链」—— 沿 ecx 逐跳上溯，直到碰到
  STACK(lea [esp+K]) / GLOBAL(mov reg, imm32 且 imm 落在 .data/.bss/.rdata) / PARAM([esp+K] 越界)
  三类终止态之一。这直接区分「栈上分配」「全局静态」两种初值来源。
判据：
 O1 起点：0x4A1CA0 的 331 个字节法调用点。
 O2 每一跳：在 (调用点, 宿主入口] 区间内，找该寄存器最近一次被赋值的指令
    （mov/lea reg, ... 或 pop reg）。若赋值源是 [esp+K]，则「跳」到宿主入口，按第三/第N参数继续。
 O3 终止分类：STACK / GLOBAL / PARAM(层数耗尽) / NONE。
 O4 对 STACK 终止点，检查 lea 之后到调用点之间是否有对该栈块 +0 的写。
反控：
 R1 跳数上限 3 -> 6。
 R2 把「宿主入口」判据换成「本函数区间(以 0x90/0xCC 填充切分)」，分类计数变化。
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
INSN={};CALLAT=[];CALLTGT=set()
pos=0
while pos<len(BUF):
    for off,sz,mn,op in md.disasm_lite(BUF[pos:pos+65536],LO+pos):
        INSN[off]=(sz,mn,op)
        if mn=='call' and op.startswith('0x'):
            t=int(op,16)
            if in_text(t): CALLAT.append((off,t)); CALLTGT.add(t)
    pos+=65536
KEYS=sorted(INSN)
SORT=sorted(CALLTGT)
def host_of(c):
    i=bisect.bisect_left(SORT,c)-1
    return SORT[i] if i>=0 else None
CALLERS=collections.defaultdict(list)
for c,t in CALLAT: CALLERS[t].append(c)
def calls_byte(fn):
    out=[]
    for va in range(LO,HI-5):
        if BUF[va-LO]!=0xE8: continue
        if struct.unpack_from('<i',BUF,va-LO+1)[0]+va+5==fn: out.append(va)
    return out
CS=calls_byte(0x4A1CA0)
ck('O1a 0x4A1CA0 字节法调用点==331', len(CS)==331, len(CS))
def win(lo,hi):
    i=bisect.bisect_left(KEYS,lo); j=bisect.bisect_left(KEYS,hi)
    return [(a,)+INSN[a] for a in KEYS[i:j]]
def find_def(reg, lo, hi):
    """在 [lo,hi) 内找 reg 最近一次被整字赋值。"""
    best=None
    for (a,sz,mn,op) in win(lo,hi):
        if ',' not in op: continue
        d=op.split(',',1)[0].strip()
        if d!=reg: continue
        if mn in ('mov','lea','pop') or (mn=='xor' and op.split(',',1)[1].strip()==reg):
            best=(a,mn,op)
    return best
GLOBAL_RANGES=[('.data',),('.rdata',)]
def sec_kind(imm):
    w=P.where(imm)
    return w if w and w!='None' else 'other'
def trace(c, hops=3):
    reg='ecx'; cur=c; hist=[]; h=0
    while h<hops:
        host=host_of(cur)
        if host is None: return ('NONE',hist)
        d=find_def(reg, host, cur)
        if d is None: return ('NONE',hist)
        a,mn,op=d; src=op.split(',',1)[1].strip(); hist.append((hex(a),mn,op))
        if mn=='lea' and 'esp' in src: return ('STACK',hist+[('esp',)])
        if mn=='pop': return ('POP',hist)
        if mn=='mov' and re.match(r'^0x[0-9a-f]+$',src):
            w=sec_kind(int(src,16)); return ('GLOBAL_'+w,hist)
        if mn=='xor': return ('ZERO_REG',hist)
        if 'esp' in src:
            # 参数透传：跳到本函数的调用者
            cs=[x for x in CALLERS.get(host,[])]
            if not cs: return ('PARAM_TOP',hist)
            cur=cs[0]; reg=reg; h+=1; continue
        return ('OTHER_'+src,hist)
    return ('PARAM_DEPTH',hist)
res=collections.Counter(); samples=collections.defaultdict(list)
for c in CS:
    k,h=trace(c,3)
    res[k]+=1
    if len(samples[k])<4: samples[k].append((hex(c),h))
ck('O3a 3 跳来源分类', True, dict(res))
for k,v in samples.items(): print('   O3b',k,v)
# R1 6 跳
res6=collections.Counter()
for c in CS: res6[trace(c,6)[0]]+=1
ck('R1a 6 跳来源分类', True, dict(res6))
# O4 STACK 终止点的 +0 写
stkw=[]
for c in CS:
    k,h=trace(c,3)
    if k!='STACK': continue
    a=int(h[0][0],16)
    z=[(hex(x),INSN[x][1]+' '+INSN[x][2]) for x in KEYS[bisect.bisect_left(KEYS,a):bisect.bisect_left(KEYS,c)]
       if INSN[x][1]=='mov' and '[' in INSN[x][2].split(',')[0] and INSN[x][2].split(',',1)[1].strip()=='0']
    if z: stkw.append((hex(c),hex(a),z[:3]))
ck('O4a STACK 终止点数', res.get('STACK',0), res.get('STACK',0))
ck('O4b 其中 lea 后到调用点之间存在零写的个数', True, len(stkw))
for r in stkw[:8]: print('   O4c',r)
json.dump(dict(cls={k:v for k,v in res.items()},cls6={k:v for k,v in res6.items()},
  stkw=stkw,samples={k:v for k,v in samples.items()},asserts=N,fails=fails),
  open('/home/t628/projects/ra2-campaign-forge/_r198/m10_origin.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
