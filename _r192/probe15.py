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
dup=0
for nm,l in grp.items():
    ms=[COL[VT[t]]['mdisp'] for t in l]
    if len(ms)!=len(set(ms)): dup+=1
print('name groups with duplicate mdisp:',dup)
VF=0x7F9594
TD={}
for sn in ('.data','.rdata'):
    base,w,n=wv(sn)
    for i in range(n-2):
        if w[i]!=VF: continue
        va=base+4*i; nm=P.cstr(va+8,160)
        if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'): TD[va]=nm.decode('latin1')
def bcds(c): return [P.dw(P.dw(c['pchd']+12)+4*j) for j in range(P.dw(c['pchd']+8))]
def lname(colva):
    c=COL[colva]; m=[b for b in bcds(c) if b is not None and P.dw(b+8)==c['mdisp']]
    if not m: return '?'
    return TD.get(P.dw(max(m,key=lambda b:P.dw(b+4))),'?')
sub=[vt for vt in VT if COL[VT[vt]]['mdisp']!=0]
key=collections.defaultdict(list)
for vt in sub:
    for k in range(NS[vt]): key[(lname(VT[vt]),COL[VT[vt]]['mdisp'],k)].append(vt)
multi={k:v for k,v in key.items() if len(v)>1}
tot=0; adj=0
def is_adj(va):
    o=P.r2o(va)
    if o is None: return False
    r=P.RAW[o:o+4]
    return (r[0:3]==b'\x83\x6c\x24' or r[0:3]==b'\x81\x6c\x24') and r[3]==0x04
for k,hosts in multi.items():
    for t in hosts:
        v=P.dw(t+4*k[2]); tot+=1
        if is_adj(v): adj+=1
print('multi-key instances',tot,'adjusters',adj,'direct',tot-adj)
print('--- top keys with overriders ---')
for k,hosts in sorted(multi.items(), key=lambda x:-len(x[1]))[:6]:
    vals=collections.Counter(P.dw(t+4*k[2]) for t in hosts)
    print('KEY',k[0],'mdisp',k[1],'slot',k[2],'hosts',len(hosts),'distinct',len(vals))
    maj,cn=vals.most_common(1)[0]
    out=[(hex(P.dw(t+4*k[2])),COL[VT[t]]['name']) for t in hosts if P.dw(t+4*k[2])!=maj]
    print('   majority',hex(maj),cn,'overriders',out[:8])
