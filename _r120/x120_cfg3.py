# Primary analysis on CFG enclosure (criterion E) + forward-reachable body for IID counting.
import struct, json, re, array as _ar, collections, math
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
starts=ld('a2_starts','I'); kinds=ld('a2_kinds','B')
pushes=ld('a2_pushes','I'); pushv=ld('a2_pushv','I')
calls=ld('a2_calls','I'); callk=ld('a2_callk','B'); callt=ld('a2_callt','I')
pushset={a:v for a,v in zip(pushes,pushv)}; ns=len(starts); startset=set(int(x) for x in starts)
NODE={}
for a,z,k,t,f in zip(rdA,rdZ,rdK,rdT,rdF): NODE[int(a)]=(int(z),int(k),int(t),int(f))
B1=set(int(a) for a in starts if (int(a)-base)>0 and text[int(a)-base-1]==0xCC)
B2=set(int(starts[i]) for i in range(1,ns) if kinds[i-1] in (1,2))
B3=set(int(callt[i]) for i in range(len(calls)) if callk[i]==3 and base<=int(callt[i])<tend and int(callt[i]) in startset)
RDB=set(int(t) for t,k in zip(rdT,rdK) if k==3 and base<=int(t)<tend and int(t) in startset)
ALL=set(B1)|set(B2)|set(B3)|set(RDB)
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
iid=scan(); iidset=set(iid)
# ---- forward reachable body from a function start, not crossing other function starts
def body(fs,cap=100000):
    seen=set(); work=[fs]; order=[]
    while work:
        a=work.pop()
        while True:
            if a in seen or a not in NODE: break
            if a!=fs and a in ALL: break
            seen.add(a); order.append(a)
            z,k,t,f=NODE[a]
            if k in (1,5,7): break
            if k==2:
                if base<=t<tend and t in NODE: work.append(t)
                break
            if k==6 and base<=t<tend and t in NODE: work.append(t)
            if f==0: break
            a=a+z
            if len(seen)>cap: break
    return seen
def iids_of(S): return sorted({pushset[a] for a in S if a in pushset and pushset[a] in iidset})
CACHE={}
def getbody(fs):
    if fs not in CACHE: CACHE[fs]=body(fs)
    return CACHE[fs]
# ---- enclosure (reverse CFG) as validated criterion E
def preds(a):
    out=[]
    for k in range(1,16):
        p=a-k
        if p in NODE:
            z,kk,t,f=NODE[p]
            if f==1 and p+z==a: out.append(p)
            if kk in (2,6) and t==a: out.append(p)
        if p in NODE2SET and NODE[p][1]==3 and NODE[p][2]==a: out.append(p)
    return out
NODE2SET=set(NODE)
def enclosure(site):
    seen={site}; work=[site]; found=set()
    while work:
        a=work.pop()
        for p in preds(a):
            if p in seen: continue
            if p in ALL: found.add(p); continue
            seen.add(p); work.append(p)
    return found
T1=0x7f7c80; T3=0x7ed358
def sites_of(T):
    raw=[base+m.start() for m in re.finditer(re.escape(b'\x68'+T.to_bytes(4,'little')),text)]
    return raw,[a for a in raw if a in pushset and pushset[a]==T]
raw1,sites1=sites_of(T1); raw3,sites3=sites_of(T3)
def group_sites(sites):
    g=collections.defaultdict(list); amb=[]
    for a in sites:
        enc=enclosure(a)
        if len(enc)==1: g[next(iter(enc))].append(a)
        else: amb.append(dict(site=hex(a),enclosing=[hex(x) for x in sorted(enc)]))
    return g,amb
g1,amb1=group_sites(sites1); g3,amb3=group_sites(sites3)
def fninfo(fs):
    S=getbody(fs); iv=iids_of(S)
    return dict(func_start=hex(fs),n_insns_reachable=len(S),
        body_min=hex(min(S)),body_max=hex(max(S)),
        distinct_iids=[hex(x) for x in iv],n_distinct=len(iv),
        iid_push_sites=sorted({hex(a) for a in S if a in pushset and pushset[a] in iidset}))
Q1=dict(target=hex(T1),raw_5byte_hits=len(raw1),sites=len(sites1),
   site_addrs=[hex(a) for a in sites1],
   rejected=[hex(a) for a in raw1 if a not in (set(sites1))],
   detection='bytes 68+LE32(T) found by regex in .text; accepted only if addr is an instruction start of the 65536-byte-chunked capstone linear sweep, mnemonic==push, op_str==0x%x, size==5'%T1,
   function_criterion=('CFG enclosure: the set of instruction starts reachable to the site by walking the recursive-descent graph BACKWARDS over fall-through, jcc/jmp targets and call targets; the walk stops when it steps onto any instruction that belongs to a wider set of candidate function starts (B1 int3-pad-first-insn, B2 after-ret/jmp, B3 direct call target, RD direct call target). Verified unique for every site.'),
   n_functions=len(g1),ambiguity=[dict(x) for x in amb1],
   functions=[dict(fninfo(fs),site_count=len(v),sites=[hex(x) for x in sorted(v)])
              for fs,v in sorted(g1.items())],
   summary=dict(funcs=len(g1),
      exactly1=sum(1 for fs in g1 if len(iids_of(getbody(fs)))==1),
      ge2=sum(1 for fs in g1 if len(iids_of(getbody(fs)))>=2),
      zero=sum(1 for fs in g1 if len(iids_of(getbody(fs)))==0)))
Q3=dict(target=hex(T3),raw_5byte_hits=len(raw3),sites=len(sites3),
   site_addrs=[hex(a) for a in sites3],
   rejected=[hex(a) for a in raw3 if a not in set(sites3)],
   n_functions=len(g3),ambiguity=amb3)
json.dump(dict(q1=Q1,iid_census=dict(count=len(iid),addrs=[hex(a) for a in sorted(iid)])),
          open(OUT+'x120exec_q1_cfg.json','w'),indent=1)
print('Q1 sites',len(sites1),'functions',len(g1),'amb',len(amb1))
print('Q1 summary',Q1['summary'])
for f in Q1['functions']:
    print('  %s n=%d sites=%d reach=%d range %s-%s'%(f['func_start'],f['n_distinct'],f['site_count'],
        f['n_insns_reachable'],f['body_min'],f['body_max']))
print('Q3 sites',len(sites3),'functions',len(g3),'amb',len(amb3))
json.dump({'Q1':Q1,'Q3meta':Q3},open(OUT+'_tmp_cfg.json','w'),indent=1)
