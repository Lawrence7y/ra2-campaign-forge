# -*- coding: utf-8 -*-
"""R218 m15：决定性检验——高槽段是否为「另一张虚表的拼接」（即 V+n 起其实是另一个类的 vftable 主体）。
做法：对每张 >256 表 T 与每张已知表 U，找最大 L 使 T[shift .. shift+L-1] == U[0 .. L-1]，
      shift 取 256 附近各值；若 L 很大（>=16）且 U 的类名与 T 的祖先相关，则为拼接证据。
正控：T=0x7e1f50 与自己 shift=0 应得 L=24。
反控：随机表对的最大公共前缀应很小（报 max）。
"""
import sys,struct,collections
sys.path.insert(0,'_r185'); import pe185 as P
def words(sn):
    s=P.B[sn]; return struct.unpack_from('<%dI'%(s['rawsize']//4),P.RAW,s['rawptr']),s['lo']
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
COL={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-5):
        if w[k]>2 or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,512)
        if not nm or nm[:3]!=b'.?A' or nm[-2:]!=b'@@': continue
        COL[base+4*k]=dict(md_=s32(w[k+1]),pCHD=w[k+4],name=nm.decode('latin1'))
CS=set(COL); VT={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k,v in enumerate(w):
        if v in CS: VT[base+4*k+4]=v
VT={v:c for v,c in VT.items() if P.where(P.dw(v))=='.text'}
def slots(vt,cap=65536):
    out=[]
    while len(out)<cap and P.where(P.dw(vt+4*len(out)))=='.text': out.append(P.dw(vt+4*len(out)))
    return out
S={v:slots(v) for v in VT}
def lcp(a,b):
    n=0
    while n<len(a) and n<len(b) and a[n]==b[n]: n+=1
    return n
print('[正控] 0x7e1f50 自比 L=%d (应 24)'%lcp(S[0x7e1f50],S[0x7e1f50]))
TGT=[0x7f5c70,0x7eb058,0x7e22a4,0x7e8c94,0x7e3ebc,0x7f4960]
best_all=[]
for vt in TGT:
    T=S[vt]
    cands=[]
    for shift in range(0,len(T)):
        for u,su in S.items():
            if u==vt: continue
            L=lcp(T[shift:],su)
            if L>=12: cands.append((L,shift,u))
    cands.sort(reverse=True)
    print('='*96)
    print('%08x %-24s slots=%d  候选拼接(>=12) %d 条'%(vt,COL[VT[vt]]['name'],len(T),len(cands)))
    for L,shift,u in cands[:6]:
        print('   L=%3d shift=%3d 源表=%08x %-32s'%(L,shift,u,COL[VT[u]]['name'][:32]))
    best_all+=cands[:3]
print('\n[反控] 随机取 20 对无关表的最大公共前缀:')
import random
random.seed(7)
ks=random.sample(list(VT),20); mx=0
for i in range(10):
    a,b=ks[2*i],ks[2*i+1]
    L=lcp(S[a],S[b]); mx=max(mx,L)
    print('   %08x vs %08x L=%d'%(a,b,L))
print('   最大 = %d'%mx)
