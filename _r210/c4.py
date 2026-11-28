# -*- coding: utf-8 -*-
"""R210 c4: 律 U 的残余 {4} 从哪来 —— 全 .text 找所有「lea reg,[this+4] 后 mov [out],reg」的 QI 返回点，
取该点之前最近的 mov edi, IID，把 (IID -> 返回 +4) 列表出来。流式 disasm_lite 分块，防 OOM。
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
TE=P.B['.text']; lo,hi=TE['lo'],TE['lo']+TE['rawsize']
hits=[]   # (addr, imm, iid, iid_addr)
CH=0x8000
buf=P.RAW
ins_cache=[]
cur_iid=None
for base in range(lo,hi,CH):
    end=min(base+CH,hi)
    o=P.r2o(base)
    prev=[]
    for ins in md.disasm_lite(buf[o:o+(end-base)],base):
        a,mn,op=ins[0],ins[2],ins[3]
        if mn=='mov' and op.startswith('edi, 0x'):
            cur_iid=int(op.split(', ')[1],16)
        if mn=='mov' and op.startswith('ecx, 0x') is False: pass
        if mn=='lea' and op.endswith('+ 4]'):
            reg=op.split(',')[0]
            prev.append((a,reg,cur_iid))
        if mn=='mov' and op.startswith('dword ptr [') and prev:
            rhs=op.split(', ')[1]
            a2,reg,iid=prev[-1]
            if rhs==reg and a-a2<=8:
                hits.append((a,4,iid,a2,reg))
        if len(prev)>8: prev=prev[-8:]
print('# 全 .text 「lea reg,[x+4]; mov [out],reg」候选点 =',len(hits))
iids=collections.Counter(h[2] for h in hits)
print('# 其中带 IID 上下文的 =',sum(1 for h in hits if h[2]))
for iid,n in iids.most_common(12):
    print('   IID %s -> %d 处'%(hex(iid) if iid else None,n))
for h in hits[:20]:
    print('   site %08x iid=%s lea@%08x reg=%s'%(h[0],hex(h[2]) if h[2] else None,h[3],h[4]))
json.dump([[hex(h[0]),h[2] and hex(h[2]),hex(h[3]),h[4]] for h in hits],
          open('/home/t628/projects/ra2-campaign-forge/_r210/c4.json','w'),indent=0)
print('FAILS',fails)
