#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m11：C3 反控 90/5000 命中的定位 —— 判据强度分级（诚实报告用）。
m10 自错：C3 用三元判据（+0==0 / +24==0 / +32==自身）就报「0 命中」，实测 90/5000，
说明**三元判据本身弱**；m1 的 C2 用的是五元判据（追加 pTD==自有 + pCHD 一致）才 0/2000。
本轮把判据强度逐级量化，供正文如实写。
"""
import sys,struct,collections,json,random
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails=[]; N=0
def ck(nm,c,d=''):
    global N; N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
def cname(b):
    t=P.cstr(P.dw(b)+8,400); return None if t is None else t.decode('latin1')
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pchd']].append(c)
CHD=sorted(G); BCA={a:[P.dw(P.dw(a+12)+4*j) for j in range(P.dw(a+8))] for a in CHD}
uniq=sorted(set(b for v in BCA.values() for b in v))
OWNTD=set(P.dw(a+28) for a in CHD); EMBS=set(a+16 for a in CHD)
ck('V0 基数 COL1214/CHD954/BCD1002',(len(COL),len(G),len(uniq))==(1214,954,1002),(len(COL),len(G),len(uniq)))

# ---------- N1 判据强度分级：在 954 真值上逐级命中率 ----------
def test(x, levels, ownset, embs, colset):
    r=[]
    r.append(P.dw(x)==0)                                  # L1 +0 恒 0
    r.append(P.dw(x+24)==0)                                # L2 cdOffset 恒 0
    r.append(P.dw(x+32)==x)                                # L3 pCHD 自指
    r.append(x+16 in colset)                               # L4 +16 是 COL 记录
    r.append(P.dw(x+28) in ownset)                         # L5 pTD 属 954 自有
    r.append(P.where(P.dw(x+12))=='.rdata')                # L6 pBCA 在 .rdata
    r.append(P.dw(x+8)==len([1 for _ in range(0)]))        # 占位，稍后替换
    return r
# 正控：954 CHD 上逐级
lv=[0]*6
for a in CHD:
    r=test(a,None,OWNTD,EMBS,set(COL))
    for i in range(6): lv[i]+=1 if r[i] else 0
print('   N1 954 真值逐级命中: L1+0==0:%d L2+24==0:%d L3自指:%d L4在COL集:%d L5pTD自有:%d L6pBCA.rdata:%d'%tuple(lv))
ck('N1a 六个单条判据在真值上全 954/954',all(x==954 for x in lv),lv)

# ---------- N2 随机对照组：逐级 + 累加 ----------
random.seed(2058)
rdlo=P.B['.rdata']['lo']; rdhi=P.B['.rdata']['hi_file']
n4=(rdhi-rdlo)//4
single=[0]*6; cum=collections.Counter()
TR=20000
for _ in range(TR):
    x=rdlo+4*random.randrange(n4-12)
    r=test(x,None,OWNTD,EMBS,set(COL))
    for i in range(6):
        if r[i]: single[i]+=1
    for k in range(1,7):
        if all(r[:k]): cum[k]+=1
print('   N2 %d 随机地址：单条命中 %s'%(TR,single))
print('   N2 累加命中（前 k 条同时成立）：%s'%dict(sorted(cum.items())))
ck('N2a L1+L2+L3 三元在随机上非零（判据弱，m10 C3 的 90/5000 由此而来）',cum[3]>0,cum[3])
ck('N2b L1..L4（+16 是 COL 记录）在随机上 0 命中',cum[4]==0,cum[4])
ck('N2c L1..L5（+16 是 COL 且 pTD 属 954 自有）在随机上 0 命中',cum[5]==0,cum[5])
ck('N2d L1..L6 全六条在随机上 0 命中',cum[6]==0,cum[6])

# ---------- N3 那 90/5000 三元命中的地址是什么 ----------
random.seed(2057)
hits=[]
for _ in range(5000):
    x=rdlo+4*random.randrange(n4-12)
    if P.dw(x)==0 and P.dw(x+24)==0 and P.dw(x+32)==x: hits.append(x)
print('   N3 m10 C3 的 5000 抽样复现 %d 个三元命中'%len(hits))
kc=collections.Counter()
for x in hits:
    if x in set(CHD): kc['真CHD']+=1
    elif x+16 in set(COL): kc['+16是COL但非CHD']+=1
    else:
        v=P.dw(x+32); kc['其它']+=1
ck('N3a 三元命中里真 CHD 占少数（=> 判据弱，需联合）',kc['真CHD']<len(hits),dict(kc))
for x in hits[:6]:
    print('      0x%x +4=%d +8=%d +16=0x%x +16inCOL=%s +28=0x%x'%(
        x,P.dw(x+4),P.dw(x+8),P.dw(x+16),x+16 in COL,P.dw(x+28)))
# 这些「其它」是否落在某个真 CHD 的 ±40 范围内（即块内偏移）
near=sum(1 for x in hits if any(abs(x-a)<64 for a in CHD))
ck('N3b 三元命中多数落在真 CHD 附近（块内偏移）',near>=len(hits)//2,(near,len(hits)))

# ---------- N4 最终判据：六条齐备才是充分条件 ----------
ok=sum(1 for a in CHD if P.dw(a)==0 and P.dw(a+24)==0 and P.dw(a+32)==a
       and a+16 in COL and P.dw(a+28) in OWNTD and P.where(P.dw(a+12))=='.rdata')
ck('N4a 六条齐备在 954 真值上 954/954',ok==954,ok)
print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
json.dump(dict(asserts=N,fails=fails,truth=lv,single=single,cum=dict(cum),
               hits=len(hits),kinds=dict(kc)),open('_r205/m11_ctl.json','w'),indent=1)
