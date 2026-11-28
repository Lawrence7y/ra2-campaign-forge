# -*- coding: utf-8 -*-
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(addr=base+4*i,sig=w[i],mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G)
NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
own={}
for a in CHD:
    for c in G[a]:
        if c==a+16: own[a]=COL[c]
TDOWN=set(v['pTD'] for v in own.values())
V={a:set(COL[c]['mdisp'] for c in G[a])-{0} for a in CHD}
NM={a:own[a]['name'] for a in CHD}
def rec(b):
    f=[P.dw(b+4*z) for z in range(6)]
    return dict(pTD=f[0],nc=s32(f[1]),mdisp=s32(f[2]),pdisp=s32(f[3]),vdisp=s32(f[4]),attr=f[5])
def tdn(td):
    nm=P.cstr(td+8,300); return nm.decode('latin1') if nm else ''
A4b={a for a in CHD if any(rec(b)['mdisp']==4 for b in BCA[a])}
A4v={a for a in CHD if 4 in V[a]}
print('4∈B 类 %d ; 4∈V 类 %d'%(len(A4b),len(A4v)))
print('\nB 有 4 但 V 无 4（%d 类）：'%len(A4b-A4v))
for a in sorted(A4b-A4v):
    rs=[rec(b) for b in BCA[a] if rec(b)['mdisp']==4]
    print('  %-52s V=%-14s 4记录 pTD=%s'%(NM[a],sorted(V[a]),[tdn(r['pTD']) for r in rs]))
print('\nV 有 4 但 B 无 4（%d 类）：'%len(A4v-A4b))
for a in sorted(A4v-A4b): print('  %-52s V=%s'%(NM[a],sorted(V[a])))
