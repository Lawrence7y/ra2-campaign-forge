#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R204 m11：W3d 反控 2/954 的定位（是不是 fallback 自选）。
m10 自错：W3d 反控里 cands 为空时回退 [a]（自己），导致 2 例自命中；门限应改为 < 1%。
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
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pchd']].append(c)
CHD=sorted(G)
BCD={a:[P.dw(P.dw(a+12)+4*j) for j in range(P.dw(a+8))] for a in CHD}
def ps(a): return set(P.dw(b) for b in BCD[a])
# 显式追踪 fallback
random.seed(2048)
selfhit=[]; fake=[]
for a in CHD:
    cands=[x for x in CHD if len(BCD[x])==len(BCD[a]) and x!=a]
    if not cands:
        other=a; selfhit.append(a)
    else:
        other=random.choice(cands)
    if set(COL[c]['ptd'] for c in G[a]) <= ps(other): fake.append((hex(a),hex(other),other==a))
print('   V1 无同长候选的 CHD %d 个，样例 %s' % (len(selfhit),[hex(x) for x in selfhit[:4]]))
print('   V1 反控命中 %d 例：%s' % (len(fake),fake[:5]))
ck('V1a 反控命中全部是 fallback 自选', all(f[2] for f in fake), len(fake))
ck('V1b 排除自选后反控命中 0', sum(1 for f in fake if not f[2])==0, sum(1 for f in fake if not f[2]))
ck('V1c 反控命中率 < 1%', len(fake) < 0.01*len(CHD), len(fake)/len(CHD))
# 更严反控：只用 n>=4 的 CHD（必有同长候选）
strict=[a for a in CHD if len(BCD[a])>=4]
random.seed(2050)
h=0
for a in strict:
    cands=[x for x in CHD if len(BCD[x])==len(BCD[a]) and x!=a]
    if not cands: continue
    if set(COL[c]['ptd'] for c in G[a]) <= ps(random.choice(cands)): h+=1
print('   V1 n>=4 的 CHD %d 个，严格反控命中 %d' % (len(strict),h))
ck('V1d 严格反控（n>=4）命中 0', h==0, (h,len(strict)))
json.dump(dict(N=N,fails=fails,selfhit=[hex(x) for x in selfhit],fake=fake,strict=(h,len(strict))),
          open('/home/t628/projects/ra2-campaign-forge/_r204/m11_ctl.json','w'),ensure_ascii=False,indent=1)
print('\n== %d assertions, %d FAIL =='%(N,len(fails))); print('FAILS:',fails)
