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
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
def nslot(vt):
    k=0
    while in_text(P.dw(vt+4*k)): k+=1
    return k
NS={vt:nslot(vt) for vt in VT}
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
# rule R-ncb: among BCDs with mdisp == COL.mdisp, take max ncb (outermost = most derived)
uniq=0; tie=0; ties=collections.Counter()
LAY={}
for va,c in COL.items():
    m=[b for b in bcds(c) if b is not None and P.dw(b+8)==c['mdisp']]
    if len(m)==1: uniq+=1; LAY[va]=m[0]; continue
    best=max(m,key=lambda b:P.dw(b+4)); top=[b for b in m if P.dw(b+4)==P.dw(best+4)]
    if len(top)==1: LAY[va]=best
    else:
        tie+=1; ties[(TD.get(P.dw(best),'?'),P.dw(best+4))]+=1
        LAY[va]=None
print('ncb-max rule: unique-single %d, max-unique %d, tie %d'%(uniq,sum(1 for c in LAY.values() if c)-uniq,tie))
for k,c in ties.most_common(5): print('   TIE',k,c)
# interface families by (layer name, mdisp)
fam=collections.defaultdict(list)
nom=0
for vt,colva in VT.items():
    b=LAY[colva]
    if b is None: nom+=1; continue
    fam[(TD.get(P.dw(b),'?'),COL[colva]['mdisp'])].append(vt)
print('families',len(fam),'tables placed',sum(len(v) for v in fam.values()),'unplaced',nom)
sz=collections.Counter(len(v) for v in fam.values()); print('size dist',dict(sorted(sz.items())))
multi={k:v for k,v in fam.items() if len(v)>1}
print('multi families',len(multi),'tables',sum(len(v) for v in multi.values()))
cons=0; inc=0; incex=[]
for k,hosts in multi.items():
    mn=min(NS[t] for t in hosts)
    for s in range(mn):
        vals={P.dw(t+4*s) for t in hosts}
        if len(vals)==1: cons+=1
        else:
            inc+=1
            if len(incex)<8: incex.append((k,s,len(vals),len(hosts),[hex(x) for x in sorted(vals)][:4]))
print('slot-inst %d consistent %d (%.4f) inconsistent %d'%(cons+inc,cons,cons/(cons+inc),inc))
for e in incex: print('   INC',e)
