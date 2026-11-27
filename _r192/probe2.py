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
# TD name map
VF=0x7F9594
TD={}
for sn in ('.data','.rdata'):
    base,w,n=wv(sn)
    for i in range(n-2):
        if w[i]!=VF: continue
        va=base+4*i; nm=P.cstr(va+8,160)
        if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'): TD[va]=nm.decode('latin1')
print('TD',len(TD))
# layer base class: BCD with mdisp == COL.mdisp
def layer_bc(c):
    nb=P.dw(c['pchd']+8); arr=P.dw(c['pchd']+12)
    out=[]
    for j in range(nb):
        b=P.dw(arr+4*j)
        if b is None: continue
        if P.dw(b+8)==c['mdisp']: out.append((TD.get(P.dw(b),'?'),P.dw(b)))
    return out
cnt=collections.Counter()
none=0
for va,c in COL.items():
    lb=layer_bc(c)
    if not lb: none+=1
    cnt[len(lb)]+=1
print('layer BCD count dist',dict(cnt),'none',none)
# group by (layername, slot) across all tables
lay=collections.defaultdict(list)
for va,c in COL.items():
    for nm,_ in layer_bc(c):
        lay[(nm,c['mdisp'])].append(va); break
print('layer keys',len(lay))
