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
    return [P.dw(arr+4*j) for j in range(nb)]
# layer base = self BCD (mdisp == COL.mdisp, pTD == COL.ptd)
amb=0; multi=collections.Counter(); LAY={}
for va,c in COL.items():
    cand=[b for b in bcds(c) if b is not None and P.dw(b)==c['ptd'] and P.dw(b+8)==c['mdisp']]
    if len(cand)!=1: amb+=1; multi[len(cand)]+=1; continue
    LAY[va]=cand[0]
print('self BCD unique',len(LAY),'amb',amb,dict(multi))
# interface groups: (ptd of layer base) -> hosts
iface=collections.defaultdict(list)
for va,b in LAY.items(): iface[b].append(va)
print('iface groups',len(iface))
sizes=collections.Counter(len(v) for v in iface.values())
print('hosts per iface',dict(sorted(sizes.items())))
multi_iface={b:v for b,v in iface.items() if len(v)>1}
print('multi-host ifaces',len(multi_iface),'covered tables',sum(len(v) for v in multi_iface.values()))
# slot consistency
cons=0; incons=0; deets=[]
for b,hosts in multi_iface.items():
    mn=min(NS[t] for t in hosts)
    for k in range(mn):
        vals={P.dw(t+4*k) for t in hosts}
        if len(vals)==1: cons+=1
        else:
            incons+=1
            if len(deets)<10: deets.append((TD.get(P.dw(b),'?'),hex(b),k,len(vals),[hex(x) for x in sorted(vals)][:4]))
print('slot instances checked',cons+incons,'consistent',cons,'inconsistent',incons, 'rate %.4f'%(cons/(cons+incons)))
for d in deets: print('  ',d)
