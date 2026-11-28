#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m8：D1i 的 3 个反例逐条定位（组内 mdisp 非严格递减）+ 860/94 分解复核。"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
VTI={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VTI[base+4*i]=P.dw(base+4*i-4)
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pchd']].append(c)
CHD=sorted(G)
def parse(vt,maxk=4000):
    hn=COL[VTI[vt]]['name']; cur=VTI[vt]; views=[]; seps=[]; k=0
    while k<maxk:
        pos=vt+4*k; w=P.dw(pos)
        if w is None: break
        if in_text(w): k+=1; continue
        if w in COL and COL[w]['name']==hn: views.append(cur); seps.append(pos); cur=w; k+=1; continue
        break
    views.append(cur); return views,seps
HEADS=[]; skip=set(); VIE={}
for vt in sorted(VTI):
    if vt in skip: continue
    views,seps=parse(vt); HEADS.append(VTI[vt]); skip.add(vt); VIE[VTI[vt]]=views
    for p in seps:
        if p+4 in VTI: skip.add(p+4)
# D1i 反例
bad=[]
for h in HEADS:
    v=VIE[h]
    for i in range(len(v)-1):
        if COL[v[i]]['mdisp']<=COL[v[i+1]]['mdisp']:
            bad.append((hex(h),COL[h]['name'][:44],i,COL[v[i]]['mdisp'],COL[v[i+1]]['mdisp'],
                        [COL[x]['mdisp'] for x in v],[hex(x) for x in v]))
print('D1i 反例 %d 条:'%len(bad))
for b in bad: print('  组头 %s %s 位置%d %d->%d mdisp序列=%s\n     视图COL=%s'%b)
# 统计：非递增对的整体计数
tot=0; non=0
for h in HEADS:
    v=VIE[h]
    for i in range(len(v)-1):
        tot+=1
        if COL[v[i]]['mdisp']<=COL[v[i+1]]['mdisp']: non+=1
print('组内相邻对总数 %d，非严格递减 %d'%(tot,non))
print('反例组头是否在多视图类中:',[len(VIE[b[1]] if False else VIE[int(b[0],16)]) for b in bad])
# 这些类是否 MI
mi=[h for h in HEADS if len(VIE[h])>1]
print('多视图类 %d 个'%len(mi))
# 反例是否属于 ATL sink 家族
for b in bad:
    h=int(b[0],16)
    print('  %s 视图数=%d attributes=%d'%(COL[h]['name'][:50],len(VIE[h]),
          P.dw([a for a in CHD if a+16 in G[COL[h]['pchd']]][0]+4)))
json.dump(dict(bad=len(bad),tot=tot,non=non),[open('_r205/m8_d1i.json','w')][0] if False else None) if False else None
