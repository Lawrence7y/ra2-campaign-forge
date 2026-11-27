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
amb=collections.Counter(); mdist=collections.Counter()
for va,c in COL.items():
    if c['mdisp']==0: continue
    m=[b for b in bcds(c) if b is not None and P.dw(b+8)==c['mdisp']]
    amb[len(m)]+=1; mdist[c['mdisp']]+=1
print('non-zero-mdisp COLs',sum(amb.values()),'mdisp-match count dist',dict(amb))
print('mdisp value dist',dict(sorted(mdist.items())))
# for mdisp==0: self BCD is first? check pTD names
n0=0; selfok=0
for va,c in COL.items():
    if c['mdisp']!=0: continue
    n0+=1
    b=bcds(c)[0]
    if b is not None and P.dw(b)==c['ptd'] and P.dw(b+8)==0: selfok+=1
print('mdisp==0 COLs',n0,'first BCD == self (ptd,mdisp 0)',selfok)
