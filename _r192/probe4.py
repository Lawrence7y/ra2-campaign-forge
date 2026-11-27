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
    nb=P.dw(c['pchd']+8); arr=P.dw(c['pchd']+12)
    return [(P.dw(arr+4*j)) for j in range(nb)]
AMB=collections.Counter(); LAY={}
for va,c in COL.items():
    cand=[b for b in bcds(c) if b is not None and P.dw(b+8)==c['mdisp']]
    AMB[len(cand)]+=1
    if len(cand)>=1: LAY[va]=cand[0]
print('mdisp-match BCD count dist',dict(AMB))
print('resolved',len(LAY))
# names of layer class
LN={va:TD.get(P.dw(b),'TD_MISS@%x'%P.dw(b)) for va,b in LAY.items()}
mm=collections.Counter(1 if LN[va]==COL[va]['name'] else 0 for va in LAY)
print('layer name == COL name:',dict(mm))
key=collections.defaultdict(list)
for va in LAY: key[(LN[va],COL[va]['mdisp'])].append(va)
print('layer keys',len(key))
sz=collections.Counter(len(v) for v in key.values())
print('tables per key',dict(sorted(sz.items())))
multi={k:v for k,v in key.items() if len(v)>1}
print('multi keys',len(multi),'tables',sum(len(v) for v in multi.values()))
cons=0; inc=0; incd=[]
for k,hosts in multi.items():
    mn=min(NS[t] for t in hosts)
    for s in range(mn):
        vals={P.dw(t+4*s) for t in hosts}
        if len(vals)==1: cons+=1
        else:
            inc+=1
            if len(incd)<12: incd.append((k[0],k[1],s,len(vals),[hex(x) for x in sorted(vals)][:5],len(hosts)))
print('slot instances',cons+inc,'consistent',cons,'inconsistent',inc,'rate %.4f'%(cons/(cons+inc) if cons+inc else -1))
for d in incd: print('  INC',d)
