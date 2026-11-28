# -*- coding: utf-8 -*-
"""R218 m14：为高槽块找「共同锚点」——即 6 张表 slot>=256 段的共同来源类。
方法：以 TechnoClass 0x7f4960（最小，309 槽）为基准，对每个 k>=256 取目标 T，
在全部 1214 张真虚表中找「同槽 k 也是 T」的表集合，统计集合大小；
若某 T 在 N 张表中同槽同值，说明它来自一个被 N 个类共同继承的祖先的槽 k。
正控：0x7e1f50 的 slot3（若有）应能在其派生类中复现。
反控：把 k 改成 k-256（低槽）时同槽同值的表数应明显不同。
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
TGT=[0x7f4960,0x7e3ebc,0x7e8c94,0x7e22a4,0x7eb058,0x7f5c70]
TS=set(TGT)
print('[锚点分析] 以 TechnoClass 0x7f4960 的 slot>=256 为主，找同槽同值的表数（排除 6 张目标表本身）')
print('%-5s %-9s %5s %-32s'%('k','target','n同值','表清单(前 4)'))
rows=[]
for k in range(256,len(S[0x7f4960])):
    T=S[0x7f4960][k]
    same=[v for v in VT if v not in TS and k<len(S[v]) and S[v][k]==T]
    rows.append((k,T,len(same)))
    names=[COL[VT[v]]['name'][4:-2][:22] for v in same[:4]]
    print('%-5d %08x %5d %s'%(k,T,len(same),names))
print('\n[统计] 同值表数分布:',dict(sorted(collections.Counter(n for _,_,n in rows).items())))
# 全 1214 表中，同槽同值的全局统计（不论 k）
print('\n[正控] 取 UnitClass 0x7f5c70 slot0（应为 0x410260 之类）在各表同槽同值表数')
t0=S[0x7f5c70][0]
print('  slot0=%08x 同值表数=%d'%(t0,sum(1 for v in VT if S[v] and S[v][0]==t0)))
print('\n[反控] 把 k 减去 256 后同槽同值表数（应不同）')
d=0
for k,T,n in rows:
    k2=k-256
    n2=sum(1 for v in VT if v not in TS and k2<len(S[v]) and S[v][k2]==T)
    if n2!=n: d+=1
print('  与高槽口径不同的槽数 = %d / %d'%(d,len(rows)))
