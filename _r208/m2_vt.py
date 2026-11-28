# -*- coding: utf-8 -*-
"""R208 m2：vftable 槽目标分布 + 0x7f9594 归属核验（分段小窗反汇编，绝不整段 detail）。
正控：全 1214 张 vftable 槽目标统计、最热地址、1 槽 vftable 的槽是否全同址
反控：把槽目标换成「每张 vftable 起点自身」作为对照分布
"""
import sys, struct, collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
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
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G)
# vftable 定位：vftable[-1] == COL 地址 且 vftable 在 .text
VFT={}
allrefs=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i,x in enumerate(w):
        if x in COL: allrefs[x].append(base+4*i)
for c in COL:
    cand=[a for a in allrefs[c] if P.where(a+4)=='.text']
    if len(cand)==1: VFT[c]=cand[0]+4
print('COL',len(COL),'vftable 定位',len(VFT))
def slots(v):
    out=[];a=v
    while P.where(a)=='.text':
        out.append(P.dw(a));a+=4
        if len(out)>4000: break
    return out
S={c:slots(v) for c,v in VFT.items()}
tot=sum(len(x) for x in S.values())
tgt=collections.Counter(x for x in S.values() for x in x)
print('总槽',tot,'不同目标',len(tgt))
print('最热 8 目标',[(hex(k),v) for k,v in tgt.most_common(8)])
one=[c for c in S if len(S[c])==1]
print('1 槽 vftable 数',len(one),'其槽值分布',collections.Counter(S[c][0] for c in one).most_common(5))
# 全部槽同址的 vftable
same=[c for c in S if len(S[c])>1 and len(set(S[c]))==1]
print('全部槽同址 vftable 数',len(same),'尺寸分布',collections.Counter(len(S[c]) for c in same).most_common(8),
      '目标分布',collections.Counter(S[c][0] for c in same).most_common(5))
# 反控：以 vftable 起点自身做对照（应几乎不复用）
selfc=collections.Counter(c for c in S)
print('反控 起点自身唯一数',len(selfc),'（= vftable 数 %d）'%len(S))
# 0x7f9594 归属
V=0x7f9594
print('V 是否某张 vftable 的起点?',V in set(VFT.values()),' 是否某槽目标?',V in tgt)
print('V 的前一 dword 0x7f9590 值=0x%x'%P.dw(0x7f9590),' where=',P.where(P.dw(0x7f9590)))
# HEAD 名
for H in (0x80ee30,0x80eea0):
    print('HEAD 0x%x +28 -> %s ; +0=0x%x +4=0x%x +8=%d' %
          (H, P.cstr(P.dw(H+28),200), P.dw(H), P.dw(H+4), P.dw(H+8)))
