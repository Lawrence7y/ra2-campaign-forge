#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m21：审计 X1 的 953/954 —— 组头不是组内最小地址视图的唯一例外定位。"""
import sys,struct,collections,json
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
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),pchd=w[i+4],name=nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if P.B['.text']['lo']<=w[i]<P.B['.text']['hi_file'] and P.dw(base+4*i-4) in COL:
            VT[base+4*i]=P.dw(base+4*i-4)
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pchd']].append(c)
CHD=sorted(G)
def in_text(x): return x is not None and P.B['.text']['lo']<=x<P.B['.text']['hi_file']
def parse(vt,maxk=4000):
    hn=COL[VT[vt]]['name']; cur=VT[vt]; views=[]; seps=[]; k=0
    while k<maxk:
        pos=vt+4*k; w=P.dw(pos)
        if w is None: break
        if in_text(w): k+=1; continue
        if w in COL and COL[w]['name']==hn: views.append(cur); seps.append(pos); cur=w; k+=1; continue
        break
    views.append(cur); return views,seps
HEADS=[]; skip=set(); VIE={}
for vt in sorted(VT):
    if vt in skip: continue
    views,seps=parse(vt); HEADS.append(VT[vt]); skip.add(vt); VIE[VT[vt]]=views
    for p in seps:
        if p+4 in VT: skip.add(p+4)
ck('V0 组头 954',len(HEADS)==954,len(HEADS))
bad=[h for h in HEADS if h!=min(VIE[h])]
ck('W1 组头 != 组内最小地址视图 的组数 == 1',len(bad)==1,len(bad))
for h in bad:
    print('   例外组头 0x%x %s'%(h,COL[h]['name']))
    print('   组内视图（地址, mdisp, vt, 是否组头）:')
    for c in sorted(VIE[h]):
        vt=[k for k,x in VT.items() if x==c]
        print('       COL 0x%x mdisp=%2d vt=%s 组头=%s 最小地址=%s'%(
            c,COL[c]['mdisp'],hex(vt[0]) if vt else 'NONE',c==h,c==min(VIE[h])))
    ck('W2 例外组是多视图组',len(VIE[h])>1,len(VIE[h]))
    ck('W3 例外组的组头 mdisp 是组内最大',
       COL[h]['mdisp']==max(COL[x]['mdisp'] for x in VIE[h]),COL[h]['mdisp'])
    ck('W4 例外组的最小地址视图 mdisp != 最大（=> 地址序被打破）',
       COL[min(VIE[h])]['mdisp']!=max(COL[x]['mdisp'] for x in VIE[h]),COL[min(VIE[h])]['mdisp'])
    low=min(VIE[h])
    print('   最小地址视图 0x%x 的 vt = %s（若 NONE 说明它没有 vt-4 指向的 vftable）'%(
        low,hex([k for k,x in VT.items() if x==low][0]) if any(x==low for x in VT.values()) else 'NONE'))
# 全局复核：地址升序序是否仍严格递减
ck('W5 例外组在地址升序下仍严格递减',
   all(COL[sorted(VIE[h])[i]]['mdisp']>COL[sorted(VIE[h])[i+1]]['mdisp']
       for i in range(len(VIE[h])-1)),None)
print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
json.dump(dict(asserts=N,fails=fails,bad=1,
               name=COL[bad[0]]['name'] if bad else None,
               head=hex(bad[0]) if bad else None,
               low=hex(min(VIE[bad[0]])) if bad else None),
          open('_r205/m21_x1.json','w'),indent=1)
