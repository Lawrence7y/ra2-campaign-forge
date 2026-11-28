#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R204 m12（规则 D 复算）：亲跑复算审计员 #516 的 4 条加强结论。
A1 run 结构：708 run、run 内 mod24 恒定、run 基址 mod24 三态
A2 段长分布 / 单元素段占比 76.2%
A3 b-16 直方图判别力弱；替代证据 b-24 也对 294/294 + 孤立 708/708
A4 mdisp==0 <=> 自有 pTD（充要律）
"""
import sys, struct, collections, random, json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn];n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
T=P.B['.text'];LO=T['lo'];HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
VTI={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VTI[base+4*i]=P.dw(base+4*i-4)
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pchd']].append(c)
CHD=sorted(G)
BCD={a:[P.dw(P.dw(a+12)+4*j) for j in range(P.dw(a+8))] for a in CHD}
uniq=sorted(set(b for v in BCD.values() for b in v))
bcdset=set(uniq)

# ---- A1 run 结构 ----
runs=[]; cur=[uniq[0]]
for i in range(1,len(uniq)):
    if uniq[i]-uniq[i-1]==24: cur.append(uniq[i])
    else: runs.append(cur); cur=[uniq[i]]
runs.append(cur)
print('   A1 run 数 %d，run 长度分布 top8 %s' % (len(runs), collections.Counter(len(r) for r in runs).most_common(8)))
ck('A1a run 数 == 708', len(runs)==708, len(runs))
modok=sum(1 for r in runs if len(set(x%24 for x in r))==1)
ck('A1b run 内 mod24 恒定 708/708', modok==len(runs), (modok,len(runs)))
bm=collections.Counter(r[0]%24 for r in runs)
print('   A1 run 基址 mod24 分布 %s' % dict(bm))
ck('A1c run 基址 mod24 三态 == {0:235, 8:233, 16:240}', dict(bm)=={0:235,8:233,16:240}, dict(bm))
# 反控：把 run 切分判据改成 +16 后 run 数与 mod 恒定性如何
r16=[]; cur=[uniq[0]]
for i in range(1,len(uniq)):
    if uniq[i]-uniq[i-1]==16: cur.append(uniq[i])
    else: r16.append(cur); cur=[uniq[i]]
r16.append(cur)
print('   A1 反控：阈值改 16 后 run 数 %d' % len(r16))
ck('A1d 反控：阈值 16 给出不同 run 数（判据对阈值敏感）', len(r16)!=len(runs), (len(r16),len(runs)))

# ---- A2 BCA 段长分布 ----
segcnt=collections.Counter()
for a in CHD:
    v=BCD[a]; L=1
    for i in range(len(v)-1):
        if v[i+1]-v[i]==-24: L+=1
        else: segcnt[L]+=1; L=1
    segcnt[L]+=1
tot=sum(segcnt.values())
print('   A2 BCA 段数总计 %d，段长分布 %s' % (tot, sorted(segcnt.items())))
ck('A2a 段数总计 == 1642', tot==1642, tot)
ck('A2b 单元素段占比 76.2%（1252/1642）', segcnt[1]==1252, (segcnt[1], tot))
ck('A2c 段长 8 的异常聚集 == 79', segcnt[8]==79, segcnt[8])

# ---- A3 b-16 判别力 + 替代证据 ----
def h(vals): return sorted(collections.Counter(vals).items())
md_h=h(s32(P.dw(b+8)) for b in uniq)
b16_h=h(s32(P.dw(b-16)) for b in uniq)
same_keys=len(dict(md_h))==len(dict(b16_h))
ck('A3a hist(b-16)==hist(mdisp)（键数相等）', same_keys, (len(md_h), len(b16_h)))
per=sum(1 for b in uniq if s32(P.dw(b-16))==s32(P.dw(b+8)))
print('   A3 逐 BCD 相等 %d / %d' % (per, len(uniq)))
ck('A3b 逐 BCD 相等仅 975/1002（审计说的 27 处不等）', per==975, (per,len(uniq)))
# 偏移扫描 -64..+64 step 8
sweep=[]
for off in range(-64,65,8):
    hh=h(s32(P.dw(b+off)) for b in uniq)
    sweep.append((off,hh==md_h))
eqoffs=[o for o,e in sweep if e]
print('   A3 偏移扫描与 hist(mdisp) 相等的偏移 %s' % eqoffs)
ck('A3c 偏移扫描只有 {0, -16} 相等（唯一性）', set(eqoffs)=={0,-16}, eqoffs)
# 替代证据
both=[b for b in uniq if (b-24) in bcdset]
iso=[b for b in uniq if (b-24) not in bcdset]
ok1=sum(1 for b in both if P.dw(b-16)==P.dw(b-24+8))
ok2=sum(1 for b in iso if P.dw(b-16)==0)
print('   A3 b-24 也是 BCD 的 %d 个，dw(b-16)==mdisp(b-24) %d；孤立 %d 个，dw(b-16)==0 %d'%(len(both),ok1,len(iso),ok2))
ck('A3d 替代证据 1：链内 b-16 == mdisp(b-24) 全部成立', ok1==len(both), (ok1,len(both)))
ck('A3e 替代证据 2：孤立记录 b-16 == 0 全部成立', ok2==len(iso), (ok2,len(iso)))
ck('A3f 两类之和 == 1002', len(both)+len(iso)==1002, (len(both),len(iso)))
# 反控：随机 1002 个 .rdata 地址，b-16 直方图是否也大量 0
random.seed(2051)
rd=P.B['.rdata']
rnd=[rd['lo']+8*random.randrange(0,(rd['rawsize']-8)//8) for _ in range(1002)]
z=sum(1 for b in rnd if P.dw(b-16)==0)
print('   A3 反控：随机 1002 地址中 b-16==0 的 %d 个' % z)
ck('A3g 反控：随机地址 zero 率远低于 708/1002', z < 900, z)

# ---- A4 mdisp==0 <=> 自有 pTD（充要律） ----
own={}   # ptd -> set of chd that own it
for a in CHD:
    for c in G[a]: own.setdefault(COL[c]['ptd'],set()).add(a)
m0=0; m0own=0; mn=0; mnown=0; bad=[]
for a in CHD:
    owna=set(COL[c]['ptd'] for c in G[a])
    for b in BCD[a]:
        pt=P.dw(b); md=s32(P.dw(b+8))
        if md==0:
            m0+=1
            if pt in owna: m0own+=1
            else: bad.append((hex(a),hex(b),'mdisp0_notown'))
        else:
            mn+=1
            if pt in owna: mnown+=1; bad.append((hex(a),hex(b),'mdispNZ_own'))
print('   A4 BCA 元素 mdisp==0: %d（其中自有 pTD %d）；mdisp!=0: %d（其中自有 %d）'%(m0,m0own,mn,mnown))
ck('A4a mdisp==0 元素数 == 2228', m0==2228, m0)
ck('A4b mdisp!=0 元素数 == 387', mn==387, mn)
ck('A4c mdisp!=0 中自有 pTD == 0（反向零反例）', mnown==0, mnown)
ck('A4d mdisp==0 中自有 pTD == 954（每类恰 1 个主对象 BCD）', m0own==954, m0own)
ck('A4e 0+387 == 2615', m0+mn==2615, m0+mn)
# 反控：把 mdisp 换成 BCD+12（pdisp，恒 -1）后律必须塌
fake0=sum(1 for a in CHD for b in BCD[a] if s32(P.dw(b+12))==0)
ck('A4f 反控：把字段换成 +12(pdisp) 后无一为 0（律不成立）', fake0==0, fake0)

json.dump(dict(N=N,fails=fails,runs=len(runs),runlen=collections.Counter(len(r) for r in runs).most_common(10),
               runmod=dict(bm),segcnt=sorted(segcnt.items()),eqoffs=eqoffs,
               both=len(both),ok1=ok1,iso=len(iso),ok2=ok2,rand_zero=z,
               m0=m0,m0own=m0own,mn=mn,mnown=mnown),
          open('/home/t628/projects/ra2-campaign-forge/_r204/m12_audit.json','w'),ensure_ascii=False,indent=1)
print('\n== %d assertions, %d FAIL =='%(N,len(fails))); print('FAILS:',fails)
