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
grp=collections.defaultdict(list)
for vt in sorted(VT): grp[COL[VT[vt]]['name']].append(vt)
VF=0x7F9594
TD={}
for sn in ('.data','.rdata'):
    base,w,n=wv(sn)
    for i in range(n-2):
        if w[i]!=VF: continue
        va=base+4*i; nm=P.cstr(va+8,160)
        if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'): TD[va]=nm.decode('latin1')
def layer_name(colva):
    c=COL[colva]
    cand=[P.dw(P.dw(c['pchd']+12)+4*j) for j in range(P.dw(c['pchd']+8))]
    cand=[b for b in cand if b is not None and P.dw(b+8)==c['mdisp']]
    return TD.get(P.dw(cand[0]),'?') if cand else '?', (cand[0] if cand else None)
def is_adj(va):
    o=P.r2o(va)
    if o is None: return False
    r=P.RAW[o:o+4]
    return (r[0:3]==b'\x83\x6c\x24' or r[0:3]==b'\x81\x6c\x24') and r[3]==0x04
direct=[]
for vt in sorted(VT):
    if COL[VT[vt]]['mdisp']==0: continue
    for k in range(NS[vt]):
        v=P.dw(vt+4*k)
        if not is_adj(v): direct.append((vt,k,v))
same_layer=0; diff_layer=0; det=collections.Counter(); ex=[]
for vt,k,v in direct:
    nm=COL[VT[vt]]['name']
    sibs=[t for t in grp[nm] if t!=vt and k<NS[t]]
    if not sibs: continue
    t=sorted(sibs)[0]; w=P.dw(t+4*k)
    ln1,b1=layer_name(VT[vt]); ln2,b2=layer_name(VT[t])
    if ln1==ln2: same_layer+=1
    else:
        diff_layer+=1
        det[(ln1,ln2)]+=1
        if len(ex)<5: ex.append((nm,k,ln1,COL[VT[vt]]['mdisp'],hex(v),ln2,COL[VT[t]]['mdisp'],hex(w)))
print('535 = same_layer %d + diff_layer %d'%(same_layer,diff_layer))
print('top layer pairs:')
for kk,c in det.most_common(10): print('   ',kk,c)
for e in ex: print('   ex',e)
