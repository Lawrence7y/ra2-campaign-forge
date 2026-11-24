# Primary criterion: CFG reachability on recursive-descent instruction graph.
import struct, json, bisect, re, array as _ar, math
P='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r120/'
d=open(P,'rb').read()
e=struct.unpack_from('<I',d,0x3c)[0]
nsec=struct.unpack_from('<H',d,e+6)[0]; optsz=struct.unpack_from('<H',d,e+20)[0]
IB=struct.unpack_from('<I',d,e+24+28)[0]
sec=e+24+optsz; SEC={}
for i in range(nsec):
    nm=d[sec+40*i:sec+40*i+8].rstrip(b'\0').decode('latin1')
    vs,va,rs,ra=struct.unpack_from('<IIII',d,sec+40*i+8); SEC[nm]=dict(va=va,vs=vs,raw=ra,rawsz=rs)
tv=SEC['.text']; text=d[tv['raw']:tv['raw']+tv['vs']]; base=IB+tv['va']; tend=base+len(text)
def ld(n,t):
    a=_ar.array(t); a.frombytes(open(OUT+n+'.bin','rb').read()); return a
rdA=ld('rd2_addr','I'); rdZ=ld('rd2_size','B'); rdK=ld('rd2_kind','B')
rdT=ld('rd2_tgt','I'); rdF=ld('rd2_flow','B')
GRAPH={}
for a,z,k,t,f in zip(rdA,rdZ,rdK,rdT,rdF):
    GRAPH[int(a)]=(int(z),int(k),int(t),int(f))
print('rd graph insns',len(GRAPH))
starts=ld('a2_starts','I'); kinds=ld('a2_kinds','B'); sizes=ld('a2_sizes','B')
pushes=ld('a2_pushes','I'); pushv=ld('a2_pushv','I')
calls=ld('a2_calls','I'); callk=ld('a2_callk','B'); callt=ld('a2_callt','I')
pushset={a:v for a,v in zip(pushes,pushv)}; ns=len(starts)
startset=set(int(x) for x in starts)
B1=set(int(a) for a in starts if (int(a)-base)>0 and text[int(a)-base-1]==0xCC)
B2=set(int(starts[i]) for i in range(1,ns) if kinds[i-1] in (1,2))
B3=set(int(callt[i]) for i in range(len(calls)) if callk[i]==3 and base<=int(callt[i])<tend and int(callt[i]) in startset)
RDB=set(int(t) for t,k in zip(rdT,rdK) if k==3 and base<=int(t)<tend and int(t) in startset)
ALLSTARTS=sorted(B1|B2|B3|RDB)
def reach(fs,cap=200000):
    """CFG reachable insn set from fs over the RD graph; stop at other known function starts."""
    seen=set(); work=[fs]
    while work:
        a=work.pop()
        while True:
            if a in seen: break
            if a not in GRAPH: break
            if a!=fs and a in ALLSTARTS: break   # don't leak into neighbouring function
            seen.add(a)
            z,k,t,f=GRAPH[a]
            if k==1 or k==5 or k==7:   # ret / int3 / skipdata(unknown)
                break
            if k==2:                   # uncond jmp
                if t and base<=t<tend and t in GRAPH: work.append(t)
                break
            if k==6:                   # jcc
                if t and base<=t<tend and t in GRAPH: work.append(t)
            na=a+z
            if f==0: break
            a=na
            if len(seen)>cap: break
    return seen
def iid_in_insns(S):
    return sorted({pushset[a] for a in S if a in pushset and pushset[a] in iidset}) if S else []
# IID census
def guid_ok(b,drop_d2=False,d4=0x46000000,d3low=0x00C0):
    d1,d2,d3,d4_=struct.unpack('<4I',b)
    if d4_!=d4: return False
    if not drop_d2 and d2!=0: return False
    if d3low is not None and (d3&0xFFFF)!=d3low: return False
    return True
def scan(drop_d2=False,d4=0x46000000,d3low=0x00C0,sections=('.rdata','.data')):
    hits={}
    for nm in sections:
        s=SEC[nm]; blob=d[s['raw']:s['raw']+min(s['vs'],s['rawsz'])]
        for off in range(0,len(blob)-16,4):
            if guid_ok(blob[off:off+16],drop_d2,d4,d3low): hits[IB+s['va']+off]=nm
    return hits
iid=scan(); iidaddrs=sorted(iid); iidset=set(iidaddrs)
T1=0x7f7c80
raw1=[base+m.start() for m in re.finditer(re.escape(b'\x68'+T1.to_bytes(4,'little')),text)]
sites1=[a for a in raw1 if a in pushset and pushset[a]==T1]
# assign each 0x7f7c80 site to its innermost enclosing start that CFG-reaches it
def assign(a,cands):
    hits=[]
    for fs in sorted(cands,reverse=True):
        if fs>a: continue
        if a in reach(fs): hits.append(fs)
    return hits
print('computing reachability for sites...')
site_assign=[]
for a in sites1:
    cands=[fs for fs in ALLSTARTS if a-0x2000<=fs<=a]
    hits=assign(a,cands)
    site_assign.append(dict(site=hex(a),enclosing_starts=[hex(x) for x in hits]))
n_multi=sum(1 for r in site_assign if len(r['enclosing_starts'])>1)
n_one=sum(1 for r in site_assign if len(r['enclosing_starts'])==1)
n_zero=sum(1 for r in site_assign if len(r['enclosing_starts'])==0)
print('sites',len(sites1),'unique',n_one,'multi',n_multi,'none',n_zero)
RES=dict(n_sites=len(sites1),n_unique_enclosure=n_one,n_multiple=n_multi,n_none=n_zero,
   sites=site_assign)
json.dump(RES,open(OUT+'x120exec_cfg_assign.json','w'),indent=1)
