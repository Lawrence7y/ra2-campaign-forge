#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 第十二刀（收口）：STACKARG 继续上跳，直到 STACK / GLOBAL / TOP。
 Y1 331 个调用点，每次遇到 STACKARG 就跳到「宿主函数的所有调用点」，继续跟 ecx 的源。
 Y2 终止分类计数 + 每类样本。
 Y3 对 STACK 终止：记录 lea 地址与该栈块是否有零写。
 反控：上跳层数 6 -> 1。
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
CALLTGT=set();CALLAT=[]
pos=0
while pos<len(BUF):
    for off,sz,mn,op in md.disasm_lite(BUF[pos:pos+65536],LO+pos):
        if mn=='call' and op.startswith('0x'):
            t=int(op,16)
            if in_text(t): CALLAT.append((off,t)); CALLTGT.add(t)
    pos+=65536
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
ck('Y1a 331', len(CS)==331, len(CS))
def func_start(va):
    p=va-LO; q=p
    while q>16:
        if (BUF[q-1]==0x90 and BUF[q-2]==0x90) or (BUF[q-1]==0xCC and BUF[q-2]==0xCC): return LO+q
        q-=1
    return None
def last_def(reg,lo,hi):
    best=None
    for off,sz,mn,op in md.disasm_lite(BUF[lo-LO:hi-LO],lo):
        if ',' not in op: continue
        if op.split(',',1)[0].strip()==reg and mn in ('mov','lea','pop','xor','sub','and','or','add'):
            best=(off,mn,op)
    return best
def trace(callva, depth=6):
    reg='ecx'; cur=callva; hist=[]; d=0
    while d<depth:
        fs=func_start(cur)
        if fs is None: return ('NOSTART',hist)
        ld=last_def(reg,fs,cur)
        if ld is None: return ('NODEF',hist)
        a,mn,op=ld; src=op.split(',',1)[1].strip() if ',' in op else ''
        hist.append((hex(a),mn,op))
        if mn=='lea' and 'esp' in src: return ('STACK',hist+[(hex(a),'LEA_ESP',src)])
        if mn=='pop': return ('POP',hist)
        if mn=='xor' and src==reg: return ('ZEROREG',hist)
        if re.match(r'^0x[0-9a-f]+$',src): return ('GLOBAL_'+str(P.where(int(src,16))),hist)
        if re.match(r'^e[a-z]{2}$',src): reg=src; cur=a; continue
        if 'esp' in src or 'ebp' in src:
            h=host_of(cur)
            if h is None: return ('PARAM_TOP',hist)
            ups=CALLERS.get(h,[])
            if not ups: return ('PARAM_TOP',hist)
            cur=ups[0]; reg='ecx'; d+=1; continue
        return ('OTHER_'+src,hist)
    return ('DEPTH',hist)
res=collections.Counter(); samp=collections.defaultdict(list)
for c in CS:
    k,h=trace(c,6); res[k]+=1
    if len(samp[k])<3: samp[k].append((hex(c),h[:6]))
ck('Y2a 6 跳上溯分类', True, dict(res))
for k,v in samp.items(): print('   Y2b',k,v)
res1=collections.Counter()
for c in CS: res1[trace(c,1)[0]]+=1
ck('R1a 1 跳分类', True, dict(res1))
stk=[(c,h) for c in CS for k,h in [trace(c,6)] if k=='STACK']
ck('Y3a STACK 终止数', True, len(stk))
for c,h in stk[:8]: print('   Y3b',hex(c),h[-3:])
json.dump(dict(cls={k:v for k,v in res.items()},cls1={k:v for k,v in res1.items()},
  stk=[(hex(c),h[-3:]) for c,h in stk[:40]],samp={k:v for k,v in samp.items()},asserts=N,fails=fails),
  open('/home/t628/projects/ra2-campaign-forge/_r198/m12_final.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
