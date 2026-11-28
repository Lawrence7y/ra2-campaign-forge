# -*- coding: utf-8 -*-
"""R209 v7：审计 #536 判据漏斗中段数字（23707/10932/1229）与我方（23711/10936/1225）差异追因。
三个中段各差 4/-4/-4，且末段一致 ⇒ 必是「段顺序」或「where() 边界含/不含」一类的口径差。
枚举变体定位（不猜）。
"""
import sys, struct, collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P

def funnel(segs, upto=4, skip_top=0):
    f=[0]*5
    for sn in segs:
        s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
        w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
        for k in range(len(w)-upto-skip_top):
            if w[k] in (0,1,2): f[0]+=1
            else: continue
            f[1]+= (w[k+2]==0)
            if w[k+2]!=0: continue
            f[2]+= (P.where(w[k+3])=='.data')
            if P.where(w[k+3])!='.data': continue
            f[3]+= (P.where(w[k+4])=='.rdata')
            if P.where(w[k+4])!='.rdata': continue
            nm=P.cstr(w[k+3]+8,400)
            if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'): f[4]+=1
    return f
print('base (.rdata,.data)      ->', funnel(('.rdata','.data')))
print('swap (.data,.rdata)      ->', funnel(('.data','.rdata')))
print('rdata only               ->', funnel(('.rdata',)))
print('data only                ->', funnel(('.data',)))
# 若审计把 w[k] in {0,1,2} 写成 w[k]!=0？不——先看真值是哪个
# 差异定位：找出「w[k] in {0,1,2} 但 w[k+2]!=0」的 4 条，看它们在哪
extra=[]
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k in range(len(w)-4):
        if w[k] in (0,1,2) and w[k+2]!=0: extra.append((sn,base+4*k,w[k],w[k+2]))
print('sig 但 w2!=0 的记录数 =', len(extra))
# 差异第二段：w2==0 且 pTD 落 .data 的计数，按 w[k] 值分
cnt=collections.Counter()
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k in range(len(w)-4):
        if w[k] in (0,1,2) and w[k+2]==0 and P.where(w[k+3])=='.data': cnt[w[k]]+=1
print('w2==0 且 pTD@.data 按 sig 值 =', dict(cnt), '合计', sum(cnt.values()))
# 第三段差 4 的追因：这 4 条 pTD@.data 但 pCHD 不在 .rdata 的
miss=[]
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for k in range(len(w)-4):
        if w[k] in (0,1,2) and w[k+2]==0 and P.where(w[k+3])=='.data':
            if P.where(w[k+4])!='.rdata':
                miss.append((sn,hex(base+4*k),w[k],hex(w[k+3]),hex(w[k+4]),P.where(w[k+4])))
print('pTD@.data 但 pCHD 非 .rdata =', len(miss))
for m in miss: print('   ',m)
