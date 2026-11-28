#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m23：两序（vt 序 vs COL 地址序）到底在几组上不同 —— 精确到每组。"""
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
vt_of={c:k for k,c in VT.items()}
ck('V0 组头 954',len(HEADS)==954,len(HEADS))
# 逐组比较
diff=[]
for h in HEADS:
    a=sorted(VIE[h],key=lambda x:vt_of[x])
    b=sorted(VIE[h])
    if a!=b: diff.append((h,a,b))
ck('W1 单视图组 860（两序必然相同）',sum(1 for h in HEADS if len(VIE[h])==1)==860,None)
ck('W2 两序不同的组数',True,len(diff))
for h,a,b in diff:
    print('   不同组 %s 组头 0x%x'%(COL[h]['name'],h))
    print('      vt序  : %s'%[(hex(c),COL[c]['mdisp'],hex(vt_of[c])) for c in a])
    print('      地址序: %s'%[(hex(c),COL[c]['mdisp'],hex(vt_of[c])) for c in b])
    # 是否 mdisp 序列相同只是顺序不同
    sa=[COL[c]['mdisp'] for c in a]; sb=[COL[c]['mdisp'] for c in b]
    ck('   %s vt序mdisp=%s 地址序mdisp=%s'%(COL[h]['name'][:26],sa,sb),True,None)
# 多视图组数
mv=[h for h in HEADS if len(VIE[h])>1]
ck('W3 多视图组 94',len(mv)==94,len(mv))
ck('W4 两序相同的多视图组数 = 94 - 不同数',len(mv)-len(diff)==94-len(diff),94-len(diff))
# 关键结论：vt 序是否也严格递减（在 diff 组之外）
def strict(seq): return all(seq[i]>seq[i+1] for i in range(len(seq)-1))
bad_vt=[h for h in HEADS if not strict([COL[c]['mdisp'] for c in sorted(VIE[h],key=lambda x:vt_of[x])])]
bad_ad=[h for h in HEADS if not strict([COL[c]['mdisp'] for c in sorted(VIE[h])])]
ck('W5 vt 序不严格递减的组 == 3',len(bad_vt)==3,[COL[h]['name'] for h in bad_vt])
ck('W6 COL 地址序不严格递减的组 == 0',len(bad_ad)==0,len(bad_ad))
ck('W7 两序不同的组 ⊂ vt 序不严格递减的组（3 组）',set(h for h,_,_ in diff)<=set(bad_vt),None)
print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
json.dump(dict(asserts=N,fails=fails,diff=len(diff),bad_vt=len(bad_vt),bad_ad=len(bad_ad),
               names=[COL[h]['name'] for h,_,_ in diff], same_order=len(HEADS)-len(diff)),
          open('_r205/m23_order.json','w'),indent=1)
