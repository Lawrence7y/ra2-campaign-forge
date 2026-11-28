#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第十九刀：把所有已取得/未取得的数打成一份可复算汇总（供台账与看板引用）。
只做汇总与一致性自检，不引入新判据。
"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
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
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
TL=P.B['.text']; TLO=TL['lo']; THI=TL['hi_file']
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        v=w[i]
        if TLO<=v<THI and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
CHD={}
for c,cc in COL.items():
    v=cc['pchd']
    if v not in CHD: CHD[v]=dict(n=P.dw(v+8),arr=P.dw(v+12),attr=P.dw(v+4))
for v,d in CHD.items():
    d['bcds']=[P.dw(d['arr']+4*j) for j in range(d['n'])]
    d['ncb']=[P.dw(b+4) for b in d['bcds']]
    d['d']=[s32(P.dw(b+8)) for b in d['bcds']]
MAIN=[v for v in VT if COL[VT[v]]['mdisp']==0]; SUB=[v for v in VT if COL[VT[v]]['mdisp']!=0]
tot=sum(d['n'] for d in CHD.values())
uniq=len({b for v,d in CHD.items() for b in d['bcds']})
def build(ncb,n):
    par={}
    for i in range(n):
        if ncb[i]<0 or i+ncb[i]>=n: return None
    for i in range(n):
        end=i+ncb[i];k=i+1
        while k<=end:
            par[k]=i;k=k+ncb[k]+1
            if k==0 or k>n: return None
        if k!=end+1: return None
    return par
t2=0;branch=0;dep=[]
for v,d in CHD.items():
    par=build(d['ncb'],d['n'])
    if par is None: continue
    kids={i:[] for i in range(d['n'])}
    for c,p in par.items(): kids[p].append(c)
    sz=[1]*d['n']
    def szof(i):
        return 1+sum(szof(c) for c in kids[i])
    for i in range(d['n']):
        if d['ncb'][i]==szof(i)-1: t2+=1
    branch+=sum(1 for i in range(d['n']) if len(kids[i])>=2)
S={
 'vt':len(VT),'col':len(COL),'chd':len(CHD),'main':len(MAIN),'sub':len(SUB),
 'bcd_elements':tot,'bcd_uniq':uniq,
 'ncb_subtree_ok':t2,'branch_points':branch,
 'color_mdisp':dict(collections.Counter(c['mdisp'] for c in COL.values())),
 'chd_attr':dict(collections.Counter(d['attr'] for d in CHD.values())),
 'chd_n':dict(sorted(collections.Counter(d['n'] for d in CHD.values()).items())),
 'ncb_value':dict(sorted(collections.Counter(P.dw(b+4) for v,d in CHD.items() for b in d['bcds']).items())),
 'd_value':dict(sorted(collections.Counter(s32(P.dw(b+8)) for v,d in CHD.items() for b in d['bcds']).items())),
 'attrs':dict(collections.Counter(P.dw(b+20) for v,d in CHD.items() for b in d['bcds'])),
 'pdisp':dict(collections.Counter(s32(P.dw(b+12)) for v,d in CHD.items() for b in d['bcds'])),
 'vdisp':dict(collections.Counter(s32(P.dw(b+16)) for v,d in CHD.items() for b in d['bcds'])),
}
print(json.dumps(S,ensure_ascii=False,indent=1))
json.dump(S,open('_r196/m19_summary.json','w'),ensure_ascii=False,indent=1)
# 自检
assert S['vt']==1214 and S['col']==1214 and S['chd']==954 and S['main']==954 and S['sub']==260
assert S['bcd_elements']==2615 and S['ncb_subtree_ok']==2615
print('SELF-CHECK OK')
