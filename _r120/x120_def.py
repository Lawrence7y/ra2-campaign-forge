# DEFINITIVE ANALYSIS: function entries = PE entry point + direct (E8) call targets that are instruction
# starts in the chunked linear sweep. Site -> innermost enclosing entry by reverse CFG walk.
import struct, json, re, array as _ar, collections, math, time
P='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r120/'
d=open(P,'rb').read()
e=struct.unpack_from('<I',d,0x3c)[0]
nsec=struct.unpack_from('<H',d,e+6)[0]; optsz=struct.unpack_from('<H',d,e+20)[0]
IB=struct.unpack_from('<I',d,e+24+28)[0]; SOI=struct.unpack_from('<I',d,e+24+56)[0]
ENTRY=IB+struct.unpack_from('<I',d,e+24+16)[0]
DIRS={i:struct.unpack_from('<II',d,e+24+96+8*i) for i in range(16)}
sec=e+24+optsz; SEC={}
for i in range(nsec):
    nm=d[sec+40*i:sec+40*i+8].rstrip(b'\0').decode('latin1')
    vs,va,rs,ra=struct.unpack_from('<IIII',d,sec+40*i+8); SEC[nm]=dict(va=va,vs=vs,raw=ra,rawsz=rs)
tv=SEC['.text']; text=d[tv['raw']:tv['raw']+tv['vs']]; base=IB+tv['va']; tend=base+len(text)
def ld(n,t):
    a=_ar.array(t); a.frombytes(open(OUT+n+'.bin','rb').read()); return a
rdA=ld('rd2_addr','I'); rdZ=ld('rd2_size','B'); rdK=ld('rd2_kind','B')
rdT=ld('rd2_tgt','I'); rdF=ld('rd2_flow','B')
starts=ld('a2_starts','I'); sizes=ld('a2_sizes','B')
pushes=ld('a2_pushes','I'); pushv=ld('a2_pushv','I')
calls=ld('a2_calls','I'); callk=ld('a2_callk','B'); callt=ld('a2_callt','I')
pushset={a:v for a,v in zip(pushes,pushv)}
startset=set(int(x) for x in starts); ns=len(starts)
NODE={}
for a,z,k,t,f in zip(rdA,rdZ,rdK,rdT,rdF): NODE[int(a)]=(int(z),int(k),int(t),int(f))
NODES=set(NODE)
rdZ_map={int(a):int(z) for a,z in zip(rdA,rdZ)}
# ---------- entries ----------
CALLT = sorted({int(callt[i]) for i in range(len(calls))
    if callk[i]==3 and base<=int(callt[i])<tend and int(callt[i]) in startset})
ENTRIES = sorted(set(CALLT)|{ENTRY})
ENTRIESET=set(ENTRIES)
print('direct-call-target entries',len(CALLT),'with entry point',len(ENTRIES),'entry',hex(ENTRY))
# ---------- reverse walk ----------
def preds(a):
    out=[]
    for k in range(1,16):
        p=a-k
        nd=NODE.get(p)
        if nd is None: continue
        z,kk,t,f=nd
        if f==1 and p+z==a: out.append(p)
        if kk in (2,6) and t==a: out.append(p)
        if kk==3 and t==a: out.append(p)
    return out
def enclosing(a,cap=200000):
    seen={a}; work=[a]; found=set()
    while work:
        x=work.pop()
        for p in preds(x):
            if p in seen: continue
            if p in ENTRIESET:
                found.add(p); continue      # stop: entry is a boundary
            seen.add(p); work.append(p)
            if len(seen)>cap: break
    return found
# ---------- IID census ----------
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
iid=scan(); iidset=set(iid); iidaddrs=sorted(iid)
# ---------- assign IID push sites to innermost entry ----------
IIDP=[(int(a),int(v)) for a,v in zip(pushes,pushv) if v in iidset]
t0=time.time(); assign={}; unresolved=[]
for a,v in IIDP:
    enc=enclosing(a)
    if not enc: unresolved.append((a,v)); continue
    # innermost = greatest address among enclosing entries (prefers the tightest nested routine)
    pick=max(enc)
    assign.setdefault(pick,[]).append((a,v))
print('IID push sites',len(IIDP),'unresolved',len(unresolved),'assigned funcs',len(assign),'%.1fs'%(time.time()-t0))
FND={fs:dict(func_start=fs,sites=sorted({a for a,_ in I}),distinct=sorted({v for _,v in I}))
     for fs,I in assign.items()}
def dist(fdict):
    return dict(funcs=len(fdict),
      exactly1=sum(1 for f in fdict.values() if len(f['distinct'])==1),
      ge2=sum(1 for f in fdict.values() if len(f['distinct'])>=2),
      ge3=sum(1 for f in fdict.values() if len(f['distinct'])>=3),
      zero=sum(1 for f in fdict.values() if len(f['distinct'])==0))
# ---------- targets ----------
def sites_of(T):
    raw=[base+m.start() for m in re.finditer(re.escape(b'\x68'+T.to_bytes(4,'little')),text)]
    ok=[a for a in raw if a in pushset and pushset[a]==T and sizes[bisect_idx(a)]==5]
    return raw,ok
import bisect
def bisect_idx(a):
    i=bisect.bisect_left(starts,a); return i if i<ns and starts[i]==a else 0
T1=0x7f7c80; T3=0x7ed358
def report(T):
    raw,ok=sites_of(T)
    rows=[]; amb=[]
    for a in ok:
        enc=enclosing(a)
        rows.append(dict(site=hex(a),enclosing=[hex(x) for x in sorted(enc)],n=len(enc)))
        if len(enc)!=1: amb.append(rows[-1])
    grp=collections.defaultdict(list)
    for a in ok: grp[max(enclosing(a))].append(a)
    return dict(target=hex(T),raw_5byte_hits=len(raw),sites=len(ok),
      site_addrs=[hex(a) for a in ok],
      rejected=[hex(a) for a in raw if a not in set(ok)],
      n_functions=len(grp),ambiguity=amb,site_enclosure=rows,
      functions=[dict(func_start=hex(fs),site_count=len(v),sites=[hex(x) for x in sorted(v)],
         n_distinct=len(FND.get(fs,{}).get('distinct',[])),
         distinct_iids=[hex(x) for x in FND.get(fs,{}).get('distinct',[])]) for fs,v in sorted(grp.items())])
r1=report(T1); r3=report(T3)
print('T1 sites',r1['sites'],'funcs',r1['n_functions'],'amb',len(r1['ambiguity']))
print('T3 sites',r3['sites'],'funcs',r3['n_functions'],'amb',len(r3['ambiguity']))
D_ALL=dist(FND); print('full-text IID distribution',D_ALL)
json.dump(dict(entries=len(ENTRIES),call_targets=len(CALLT),entry_point=hex(ENTRY),
   iid_site_assign=dict(assigned_funcs=len(FND),distribution=D_ALL,
      functions=[dict(func_start=hex(k),n_sites=len(v['sites']),
        sites=[hex(x) for x in v['sites']],distinct=[hex(x) for x in v['distinct']])
        for k,v in sorted(FND.items())]),
   unresolved=[[hex(a),hex(v)] for a,v in unresolved],
   q1=r1,q3=r3, iid_census=dict(count=len(iid),addrs=[hex(a) for a in iidaddrs])),
   open(OUT+'x120exec_def.json','w'),indent=1)
