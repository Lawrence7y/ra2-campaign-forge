# -*- coding: utf-8 -*-
"""R218 m19：线性 sweep（遇非法字节仅前进 1 字节，不终止），统计真实指令数与 card C 六数。
正控：最后一条指令地址应接近 .text 末尾（>= 0x7df000）；反控：报出「非法字节跳过次数」。
"""
import sys,collections
sys.path.insert(0,'_r185'); import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
mdl=Cs(CS_ARCH_X86,CS_MODE_32)
t=P.B['.text']; lo=t['lo']; raw=P.RAW[t['rawptr']:t['rawptr']+t['rawsize']]
N=len(raw); pos=0; total=0; skips=0; lasta=0; cands=[]
while pos<N:
    got=False
    for a,sz,mn,ops in mdl.disasm_lite(raw[pos:pos+64], lo+pos):
        got=True; total+=1; lasta=a
        if mn in ('call','jmp'):
            s=ops.strip()
            if s.startswith('dword ptr ['):
                inner=s[s.index('[')+1:s.rindex(']')]
                if '*' not in inner:
                    parts=[x.strip() for x in inner.replace('-','+-').split('+')]
                    if parts and len(parts)<=2 and parts[0] in ('eax','ebx','ecx','edx','esi','edi','ebp','esp'):
                        disp=0; ok=True
                        if len(parts)==2:
                            try: disp=int(parts[1],0)
                            except: ok=False
                        if ok and parts[0]!='esp': cands.append((a,mn,inner,disp))
        pos+=sz
        break
    if not got:
        pos+=1; skips+=1
    if total>4_000_000: break
print('[指令数] %d  [非法跳字节] %d  [末指令地址] %08x (应 >= 0x7df000)'%(total,skips,lasta))
print('[候选] %d（card C 报 18,935）'%len(cands))
print('[disp==0x2c] %d（1114）  [disp==0] %d（824）'%(sum(1 for x in cands if x[3]==0x2c),sum(1 for x in cands if x[3]==0)))
hi=[x for x in cands if x[3]>=0x400]; ss=set(x[3]//4 for x in hi)
print('[s>=256] %d（931） 不同s=%d（91） 非4倍数=%d（0）'%(len(hi),len(ss),sum(1 for x in hi if x[3]%4)))
print('[0x41021a] %s   [负disp] %d   [s>344] %s'%(any(x[0]==0x41021a for x in cands),
      sum(1 for x in cands if x[3]<0),sorted(s for s in ss if s>344)))
print('[s 分布 top12]',collections.Counter(x[3]//4 for x in hi).most_common(12))
