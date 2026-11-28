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
def layername(colva):
    c=COL[colva]
    m=[b for b in bcds(c) if b is not None and P.dw(b+8)==c['mdisp']]
    b=max(m,key=lambda x:P.dw(x+4)) if m else None
    return TD.get(P.dw(b),'?') if b else '?'
def is_adj(va):
    o=P.r2o(va)
    if o is None: return False
    r=P.RAW[o:o+4]
    return (r[0:3]==b'\x83\x6c\x24' or r[0:3]==b'\x81\x6c\x24') and r[3]==0x04
# image-wide key: (layer base name, mdisp, slot)
key=collections.defaultdict(list)
for vt,colva in VT.items():
    ln=layername(colva); m=COL[colva]['mdisp']
    for k in range(NS[vt]):
        key[(ln,m,k)].append((vt,P.dw(vt+4*k)))
print('distinct (layer,mdisp,slot) keys',len(key))
multi={k:v for k,v in key.items() if len(v)>1}
print('keys with >=2 hosts',len(multi),'slot instances covered',sum(len(v) for v in multi.values()))
cons=0; inc=0; incx=[]
for k,hosts in multi.items():
    vals=collections.Counter(v for _,v in hosts)
    if len(vals)==1: cons+=1
    else:
        inc+=1
        if len(incx)<10: incx.append((k,len(hosts),len(vals),[(hex(x),c) for x,c in vals.most_common(4)]))
print('image-wide slot keys: consistent %d / inconsistent %d  rate %.4f'%(cons,inc,cons/(cons+inc)))
mod=sum(collections.Counter(v for _,v in h).most_common(1)[0][1] for h in multi.values())
print('modal coverage %.4f (%d/%d)'%(mod/sum(len(h) for h in multi.values()),mod,sum(len(h) for h in multi.values())))
for e in incx: print('   INC',e)
