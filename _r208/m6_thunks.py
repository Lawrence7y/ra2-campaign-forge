# -*- coding: utf-8 -*-
"""R208 m6：vftable 槽 0 的「同址折叠」现象字节实证（R181/R182 待办⑧：虚表字节级取证）。
正控：1214 张 vftable 的 slot0 分布；两个热点 thunk 的完整反汇编；使用它们的类名
反控：slot0 的随机基线（把 slot0 换成 slot1 统计）；两 thunk 的字节是否完全相同（ICF 判据）
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
refidx=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i,x in enumerate(w):
        if x in COL: refidx[x].append(base+4*i)
vt={}
for c in COL:
    q=[x for x in refidx.get(c,[]) if P.where(P.dw(x+4))=='.text']
    if len(q)==1: vt[c]=q[0]+4
def vlen(s,cap=4096):
    k=0
    while k<cap and P.where(P.dw(s+4*k))=='.text': k+=1
    return k
S={c:[P.dw(vt[c]+4*k) for k in range(vlen(vt[c]))] for c in vt}
print('vftable %d 槽 %d' % (len(S),sum(len(v) for v in S.values())))
s0=collections.Counter(v[0] for v in S.values())
print('== A slot0 分布 top10 ==')
for a,n in s0.most_common(10):
    print('   0x%x  被 %d 张 vftable 用作 slot0' % (a,n))
print('   slot0 不同地址 %d / 1214 张' % len(s0))
s1=collections.Counter(v[1] for v in S.values() if len(v)>1)
print('== 反控 slot1 分布 top5 ==',[(hex(k),v) for k,v in s1.most_common(5)],' 不同 %d'%len(s1))
print('== B 热点 thunk 字节与反汇编 ==')
md=Cs(CS_ARCH_X86,CS_MODE_32)
for a in [x for x,_ in s0.most_common(4)]:
    raw=P.RAW[P.r2o(a):P.r2o(a)+24]
    ins=list(md.disasm(raw,a))
    txt='; '.join('%s %s'%(i.mnemonic,i.op_str) for i in ins[:6])
    print('   0x%x 字节 %s' % (a,raw[:14].hex()))
    print('        %s' % txt)
    # 规范化字节串（去 nop 填充）
    norm=raw.split(b'\x90')[0]
    print('        nop 前规范字节 %s (len %d)' % (norm.hex(),len(norm)))
print('== C ICF 判据：各热点 thunk 的规范化字节是否相同 ==')
norm={}
for a,_ in s0.most_common(8):
    raw=P.RAW[P.r2o(a):P.r2o(a)+24]
    norm[a]=raw.split(b'\x90')[0]
g=collections.defaultdict(list)
for a,b in norm.items(): g[b].append(a)
print('   不同规范字节组数 %d / 8' % len(g))
for b,al in g.items():
    print('   字节 %s -> %s' % (b.hex(),[hex(x) for x in sorted(al)]))
print('== D 使用 0x410590 / 0x410580 的类 ==')
for tgt in (0x410590,0x410580,0x410310 if 0x410310 in s0 else None):
    if tgt is None: continue
    cls=[COL[c]['name'] for c in S if S[c][0]==tgt]
    print('   0x%x: %d 类，前 8 名 %s' % (tgt,len(cls),sorted(cls)[:8]))
print('== E slot1 为 0x410590 的类（析构槽在 slot1 的类）==')
c2=[COL[c]['name'] for c in S if len(S[c])>1 and S[c][1]==0x410590]
print('   %d 类，前 6 %s' % (len(c2),sorted(c2)[:6]))
json.dump(dict(slot0=[[hex(k),v] for k,v in s0.most_common(20)],distinct0=len(s0),
               slot1=[[hex(k),v] for k,v in s1.most_common(10)],distinct1=len(s1),
               icfGroups=[[b.hex(),[hex(x) for x in sorted(al)]] for b,al in g.items()]),
          open('_r208/m6_thunks.json','w'),ensure_ascii=False,indent=1)
