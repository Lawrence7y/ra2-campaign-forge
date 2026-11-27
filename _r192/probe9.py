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
def layer_name(colva):
    c=COL[colva]
    cand=[P.dw(P.dw(c['pchd']+12)+4*j) for j in range(P.dw(c['pchd']+8))]
    cand=[b for b in cand if b is not None and P.dw(b+8)==c['mdisp']]
    return TD.get(P.dw(cand[0]),'?') if cand else '?'
for tgt in (0x410450,0x410580,0x410590,0x4C9150,0x410220,0x410230,0x410210):
    slots=collections.Counter(); lays=collections.Counter(); md=collections.Counter(); names=collections.Counter()
    for vt,colva in VT.items():
        for k in range(NS[vt]):
            if P.dw(vt+4*k)!=tgt: continue
            slots[k]+=1; md[COL[colva]['mdisp']]+=1; lays[layer_name(colva)]+=1; names[COL[colva]['name']]+=1
    print('== %08x total %d'%(tgt,sum(slots.values())))
    print('   slots',dict(sorted(slots.items())))
    print('   layer names',dict(lays.most_common(6)))
    print('   mdisp',dict(sorted(md.items())))
    print('   host classes',len(names),dict(names.most_common(4)))
