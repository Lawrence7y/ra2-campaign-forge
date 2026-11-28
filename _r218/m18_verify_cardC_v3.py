# -*- coding: utf-8 -*-
"""R218 m18：m16/m17 切块推进均有缺陷（m16 固定 64KB 截断指令、m17 遇非法字节提前推进不足）。
改用 capstone 生成器对全段一次性 disasm_lite（规则允许：lite 全段流式；严禁 detail=True 全段）。
复算 card C（#567）六个数。
"""
import sys,collections
sys.path.insert(0,'_r185'); import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
mdl=Cs(CS_ARCH_X86,CS_MODE_32)
t=P.B['.text']; lo=t['lo']; raw=P.RAW[t['rawptr']:t['rawptr']+t['rawsize']]
total=0; cands=[]
for a,sz,mn,ops in mdl.disasm_lite(raw,lo):
    total+=1
    if mn not in ('call','jmp'): continue
    s=ops.strip()
    if not s.startswith('dword ptr ['): continue
    inner=s[s.index('[')+1:s.rindex(']')]
    if '*' in inner: continue
    parts=[x.strip() for x in inner.replace('-','+-').split('+')]
    if not parts or len(parts)>2: continue
    if parts[0] not in ('eax','ebx','ecx','edx','esi','edi','ebp','esp'): continue
    disp=0
    if len(parts)==2:
        try: disp=int(parts[1],0)
        except: continue
    if parts[0]=='esp': continue
    cands.append((a,mn,inner,disp))
print('[指令数] %d（card C 报 1,394,300）'%total)
print('[候选] %d（card C 报 18,935）'%len(cands))
print('[disp==0x2c] %d（1114）  [disp==0] %d（824）'%(sum(1 for x in cands if x[3]==0x2c),sum(1 for x in cands if x[3]==0)))
hi=[x for x in cands if x[3]>=0x400]
ss=set(x[3]//4 for x in hi)
print('[s>=256] %d（931）  不同 s=%d（91）  非4倍数=%d（0）'%(len(hi),len(ss),sum(1 for x in hi if x[3]%4)))
print('[0x41021a] %s ; 0x410210 函数体命中 %s'%(any(x[0]==0x41021a for x in cands),
      [(hex(a),n) for a,_,n,_ in cands if 0x410210<=a<0x410230]))
print('[负 disp] %d ; [s>344] %s'%(sum(1 for x in cands if x[3]<0),sorted(s for s in ss if s>344)))
print('[s 分布 top12]',collections.Counter(x[3]//4 for x in hi).most_common(12))
