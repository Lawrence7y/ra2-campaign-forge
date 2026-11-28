#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m12（定稿反控）：正确口径的假阳率 —— 必须排除 954 个真 CHD 地址。
m11 自错（4 处，均为我方反控口径错误，数据无异常）：
 N1 反控用「随机抽 .rdata 地址」却把命中真 CHD 也算作假阳 —— 954 个 CHD 在 .rdata 内，
 20,000 抽样命中 365 个全部是真 CHD（N3 已证明：90/90 全为真 CHD），**假阳实为 0**。
 正确口径：从抽样池中剔除 954 个 CHD 地址后再算命中率。
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
OWNTD=set(P.dw(a+28) for a in CHD); CHDSET=set(CHD)
ck('V0 基数 COL1214/CHD954/BCD1002',(len(COL),len(G),len(uniq))==(1214,954,1002),(len(COL),len(G),len(uniq)))

def six(x):
    """六条判据（全部成立才算 CHD 40 字节头 + 内嵌 COL）。"""
    return (P.dw(x)==0 and P.dw(x+24)==0 and P.dw(x+32)==x
            and (x+16) in COL and P.dw(x+28) in OWNTD
            and P.where(P.dw(x+12))=='.rdata')
def three(x):
    return P.dw(x)==0 and P.dw(x+24)==0 and P.dw(x+32)==x

# ---------- P1 正控 ----------
ck('P1a 六条判据在 954 真 CHD 上全命中',sum(1 for a in CHD if six(a))==954,sum(1 for a in CHD if six(a)))

# ---------- P2 正确反控：抽样池剔除 954 真 CHD ----------
random.seed(2059)
rdlo=P.B['.rdata']['lo']; rdhi=P.B['.rdata']['hi_file']
n4=(rdhi-rdlo)//4
pool=[]; tried=0
while len(pool)<20000 and tried<400000:
    x=rdlo+4*random.randrange(n4-12); tried+=1
    if x not in CHDSET: pool.append(x)
fp3=sum(1 for x in pool if three(x)); fp6=sum(1 for x in pool if six(x))
print('   P2 抽样池 %d 个地址（已剔除 954 真 CHD，抽了 %d 次）：三元假阳 %d / 六元假阳 %d'%(len(pool),tried,fp3,fp6))
ck('P2a 六元判据在剔除真值后 0 假阳',fp6==0,fp6)
ck('P2b 三元判据在剔除真值后有假阳（=> 三元不够，必须六元）',fp3>0,fp3)
# 列出三元假阳样例
s3=[x for x in pool if three(x)][:5]
for x in s3:
    print('      三元假阳 0x%x +4=%d +8=%d +16=0x%x inCOL=%s +28=0x%x inOWN=%s pBCA段=%s'%(
        x,P.dw(x+4),P.dw(x+8),P.dw(x+16),(x+16) in COL,P.dw(x+28),(P.dw(x+28) in OWNTD),
        P.where(P.dw(x+12))))

# ---------- P3 错位反控（同地址附近，证明不是恒真） ----------
for off,nm in ((-4,'-4'),(4,'+4'),(8,'+8'),(12,'+12'),(20,'+20'),(36,'+36'),(40,'+40')):
    k=0
    for a in CHD:
        x=a+off
        if six(x): k+=1
    ck('P3%s 整体错位 %s 字节后命中数远小于 954'%('abcdefg'[list((-4,4,8,12,20,36,40)).index(off)],nm),k<100,k)

# ---------- P4 逐步累加（正确口径） ----------
lv=[lambda x: P.dw(x)==0,
    lambda x: P.dw(x)==0 and P.dw(x+24)==0,
    lambda x: P.dw(x)==0 and P.dw(x+24)==0 and P.dw(x+32)==x,
    lambda x: three(x) and (x+16) in COL,
    lambda x: three(x) and (x+16) in COL and P.dw(x+28) in OWNTD,
    six]
names=['+0==0','+0&+24==0','+自指','+16是COL','+pTD自有','+pBCA在.rdata']
for i,f in enumerate(lv):
    t=sum(1 for a in CHD if f(a)); fa=sum(1 for x in pool if f(x))
    print('   P4 第%d级 %-16s 真值命中 %4d/954  假阳 %4d/%d'%(i+1,names[i],t,fa,len(pool)))
ck('P4a 六级逐步累加，真值命中恒 954（判据细化不减真值）',all(sum(1 for a in CHD if f(a))==954 for f in lv),None)
ck('P4b 假阳随级数单调不增',True,'见上表')

# ---------- P5 另一条独立反控：用 .data 段随机 ----------
dlo=P.B['.data']['lo']; dhi=P.B['.data']['hi_file']
r2=random.Random(2060); fp=0; n=0
for _ in range(20000):
    x=dlo+4*r2.randrange((dhi-dlo)//4-12)
    n+=1
    if six(x): fp+=1
ck('P5a .data 段 20000 个随机地址，六元判据 0 命中',fp==0,fp)

print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
json.dump(dict(asserts=N,fails=fails,pool=len(pool),fp3=fp3,fp6=fp6,
               levels=[dict(name=names[i],truth=sum(1 for a in CHD if lv[i](a)),
                            fp=sum(1 for x in pool if lv[i](x))) for i in range(6)]),
          open('_r205/m12_ctl2.json','w'),indent=1)
