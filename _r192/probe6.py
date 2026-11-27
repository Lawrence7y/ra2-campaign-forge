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
# family: (base class name X, mdisp m) from BCD entries with pmd.mdisp != 0
fam=collections.defaultdict(list)   # (X,m) -> [vt]
nofam=0
for vt,colva in VT.items():
    c=COL[colva]
    nb=P.dw(c['pchd']+8); arr=P.dw(c['pchd']+12)
    seen=set()
    for j in range(nb):
        b=P.dw(arr+4*j)
        if b is None: continue
        m=P.dw(b+8)
        if m==0: continue
        X=TD.get(P.dw(b))
        if X is None: continue
        if (X,m) in seen: continue
        seen.add((X,m))
        # only if this table's own layer is at that offset
        if c['mdisp']==m: fam[(X,m)].append(vt)
sz=collections.Counter(len(v) for v in fam.values())
print('families',len(fam),'tables in fam',sum(len(v) for v in fam.values()),'size dist',dict(sorted(sz.items())))
multi={k:v for k,v in fam.items() if len(v)>=2}
print('multi families',len(multi),'tables',sum(len(v) for v in multi.values()))
def is_adj(va):
    o=P.r2o(va)
    if o is None: return None
    r=P.RAW[o:o+4]
    if (r[0:3]==b'\x83\x6c\x24' or r[0:3]==b'\x81\x6c\x24') and r[3]==0x04: return 'adj_imm8' if r[0]==0x83 else 'adj_imm32'
    return None
def jump_tgt(va):
    o=P.r2o(va)
    if o is None: return None
    r=P.RAW[o:o+6]
    if r[0]==0xE9: return va+5+struct.unpack_from('<i',r,1)[0]
    if r[0]==0xEB: return va+2+struct.unpack_from('<b',r,1)[0]
    if r[0]==0xFF and r[1]==0x25: return P.dw(struct.unpack_from('<I',r,2)[0])
    return None
def canon(va,maxhop=8):
    cur=va
    for _ in range(maxhop):
        t=jump_tgt(cur)
        if t is None or not in_text(t): break
        cur=t
    return cur
cons=0; inc=0; inc_pairs=[]
for k,hosts in multi.items():
    mn=min(NS[t] for t in hosts)
    for s in range(mn):
        vals={P.dw(t+4*s) for t in hosts}
        if len(vals)==1: cons+=1
        else:
            inc+=1
            inc_pairs.append((k,s,sorted(vals),hosts))
print('slot inst',cons+inc,'consistent',cons,'inconsistent',inc, 'rate %.4f'%(cons/(cons+inc)))
# breakdown of distinct values within inconsistent (canon collapse)
collapse=0; distinct=0
for k,s,vals,hosts in inc_pairs:
    cvals={canon(v) for v in vals}
    if len(cvals)==1: collapse+=1
    else: distinct+=1
print('inconsistent: canon-collapse',collapse,'still-distinct',distinct)
for k,s,vals,hosts in inc_pairs[:6]:
    print('  FAM',k[0],k[1],'slot',s,'vals',[hex(v) for v in vals],'hosts',len(hosts))
    for t in hosts[:4]: print('      ',COL[VT[t]]['name'],hex(t),hex(P.dw(t+4*s)))

print('=== modal coverage per (family,slot) ===')
tot=0; modal_sum=0; full=0; hist=collections.Counter()
for k,hosts in multi.items():
    mn=min(NS[t] for t in hosts)
    for s in range(mn):
        vs=[P.dw(t+4*s) for t in hosts]
        c2=collections.Counter(vs)
        mv,mc=c2.most_common(1)[0]
        tot+=1; modal_sum+=mc
        if mc==len(hosts): full+=1
        hist[(len(hosts),len(c2))]+=1
print('family-slot groups',tot,'modal coverage %.4f'%(modal_sum/sum(len(h) for k,h in multi.items() for _ in range(min(NS[t] for t in h)))))
print('fully-unanimous groups',full)
for (nh,nv),c in sorted(hist.items())[:20]: print('  hosts',nh,'distinct',nv,'groups',c)
