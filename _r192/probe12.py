import sys,struct,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=w[i+1],ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
VF=0x7F9594
TD={}
for sn in ('.data','.rdata'):
    base,w,n=wv(sn)
    for i in range(n-2):
        if w[i]!=VF: continue
        va=base+4*i; nm=P.cstr(va+8,160)
        if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'): TD[va]=nm.decode('latin1')
def bcds(c):
    return [P.dw(P.dw(c['pchd']+12)+4*j) for j in range(P.dw(c['pchd']+8))]
amblist=[]
for va,c in COL.items():
    if c['mdisp']==0: continue
    m=[b for b in bcds(c) if b is not None and P.dw(b+8)==c['mdisp']]
    if len(m)>1: amblist.append((va,c,m))
print('ambiguous count',len(amblist))
for va,c,m in amblist[:3]:
    print('COL',hex(va),c['name'],'mdisp',c['mdisp'],'pchd',hex(c['pchd']))
    for b in m: print('   cand',hex(b),'ptd',hex(P.dw(b)),TD.get(P.dw(b),'?'),'pmd',(P.dw(b+8),P.dw(b+12),P.dw(b+16)),'attr',P.dw(b+20))
    # all bcds for context
    for b in bcds(c): print('      all',hex(b),TD.get(P.dw(b),'?'),'mdisp',P.dw(b+8),'ncb',P.dw(b+4))
