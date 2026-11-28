# -*- coding: utf-8 -*-
"""R218 m16：主会话独立复算 card C（#567）关键数字（§2.12 规则 D）。
复算项：有效位点 18935 / disp==0x2c 1114 / s>=256 931 / 不同 s 数 91 / 0x41021a 命中 / 非4倍数 0。
只用 disasm_lite 分块，禁 detail 常驻。
"""
import sys,struct,collections
sys.path.insert(0,'_r185'); import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86 import X86_OP_MEM,X86_OP_REG
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
# detail 只对本条指令开（capstone python: md.disasm with detail on single chunk must avoid whole段）。
# 折中：全段 disasm_lite 收集候选地址，再对候选单独 detail。
t=P.B['.text']; lo=t['lo']; raw=P.RAW[t['rawptr']:t['rawptr']+t['rawsize']]
GPR={8,16,24,32,40,48,56,64,72,80,88,96,104,112}  # eax..edi
mdl=Cs(CS_ARCH_X86,CS_MODE_32)
CH=0x10000
cands=[]; total=0
pos=0
while pos<len(raw):
    chunk=raw[pos:pos+CH]
    base=lo+pos
    for ins in mdl.disasm_lite(chunk,base):
        total+=1
        a,sz,mn,ops=ins
        if mn not in ('call','jmp'): continue
        s=ops.strip()
        if not s.startswith('dword ptr ['): continue
        inner=s[s.index('[')+1:s.rindex(']')]
        # 仅 [reg] 或 [reg+0xNN] 或 [reg-0xNN]
        if '*' in inner or '[' in inner or '+' in inner.strip('+-')[1:] if False else False: pass
        parts=[x.strip() for x in inner.replace('-','+-').split('+')]
        if len(parts)<1 or len(parts)>2: continue
        if parts[0] not in ('eax','ebx','ecx','edx','esi','edi','ebp','esp'): continue
        if len(parts)==2:
            try: disp=int(parts[1],0)
            except: continue
        else:
            disp=0
        if parts[0]=='esp': continue
        cands.append((a,sz,mn,inner,disp))
    pos+=CH
    if pos>=len(raw): break
print('[总数] disasm_lite 解码指令 %d 条（card C 报 1,394,300）'%total)
print('[候选] 接受位点 %d（card C 报 18,935）'%len(cands))
c2=collections.Counter(inner for _,_,_,inner,_ in cands)
print('[disp==0x2c] %d 处（card C 报 1114）'%sum(1 for x in cands if x[4]==0x2c))
print('[disp==0] %d 处（card C 报 824）'%sum(1 for x in cands if x[4]==0))
hi=[x for x in cands if x[4]>=0x400]
print('[s>=256] %d 处（card C 报 931）'%len(hi))
ss=set(x[4]//4 for x in hi)
print('[不同 s] %d 个（card C 报 91）'%len(ss))
print('[非4倍数] %d 处（card C 报 0）'%sum(1 for x in hi if x[4]%4))
print('[0x41021a 命中] %s'%any(x[0]==0x41021a for x in cands))
print('[0x410210 函数体内] %s'%[(hex(a),n) for a,_,_,n,_ in cands if 0x410210<=a<0x410230])
print('[s 分布 top12]',[(s,sum(1 for x in hi if x[4]//4==s)) for s,_ in collections.Counter(x[4]//4 for x in hi).most_common(12)])
print('[超过 344 的 s]',sorted(s for s in ss if s>344))
neg=[x for x in cands if x[4]<0]
print('[负 disp] %d 处 %s'%(len(neg),[(hex(a),n) for a,_,_,n,_ in neg]))
