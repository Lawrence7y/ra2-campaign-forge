# FINAL measurement engine.
#  * instruction graph = complete 64KB-chunked linear sweep (1,392,527 insns)
#  * function entries    = PE entry point + all direct E8 call targets that are insn starts
#  * site -> function    = reverse-CFG enclosure (walk predecessors until an entry is hit)
#  * function body       = containment: all sites whose enclosure contains that entry
#                          (secondary view: innermost partition = max(enclosure))
import struct, json, re, array as _ar, collections, bisect, time
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
tv=SEC['.text']; text=d[tv['raw']:tv['raw']+tv['vs']]; base=IB+tv['va']; tend=base+len(text); TL=len(text)
def ld(n,t):
    a=_ar.array(t); a.frombytes(open(OUT+n+'.bin','rb').read()); return a
starts=ld('a2_starts','I'); kinds=ld('a2_kinds','B'); sizes=ld('a2_sizes','B')
pushes=ld('a2_pushes','I'); pushv=ld('a2_pushv','I')
calls=ld('a2_calls','I'); callk=ld('a2_callk','B'); callt=ld('a2_callt','I')
pushset={a:v for a,v in zip(pushes,pushv)}
SL=[int(x) for x in starts]; NS=len(SL)
sz_at=bytearray(TL); kd_at=bytearray(TL); tg_at=_ar.array('I',[0])*TL
for i in range(NS):
    o=SL[i]-base; sz_at[o]=int(sizes[i]); kd_at[o]=int(kinds[i])
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
for i in range(NS):
    if kd_at[SL[i]-base] in (2,6):
        o=SL[i]-base; ins=None
        for x in md.disasm(text[o:o+16],SL[i]): ins=x; break
        if ins and ins.op_str.startswith('0x'): tg_at[o]=int(ins.op_str,16)
CALLT=set(int(callt[i]) for i in range(len(calls)) if callk[i]==3)
ENTRIES=sorted({t for t in CALLT if base<=t<tend and sz_at[t-base]>0}|{ENTRY})
ENTRIESET=set(ENTRIES)
def preds(a):
    out=[]
    for k in range(1,16):
        p=a-k; po=p-base
        if po<0 or po>=TL: continue
        s=sz_at[po]
        if s==0: continue
        kk=kd_at[po]; t=tg_at[po]
        if p+s==a and kk not in (1,2,5,7): out.append(p)
        if (kk in (2,6) or kk==3) and t==a: out.append(p)
    return out
ENC={}
def enclosing(a,cap=400000):
    if a in ENC: return ENC[a]
    seen={a}; work=[a]; found=set()
    while work:
        x=work.pop()
        for p in preds(x):
            if p in seen: continue
            if p in ENTRIESET: found.add(p); continue
            seen.add(p); work.append(p)
            if len(seen)>cap: break
    ENC[a]=found; return found
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
IIDP=[(int(a),int(v)) for a,v in zip(pushes,pushv) if v in iidset]
# containment (per entry) and innermost partition
by_cont=collections.defaultdict(list); by_inner=collections.defaultdict(list); unres=[]
for a,v in IIDP:
    enc=enclosing(a)
    if not enc: unres.append((a,v)); continue
    for fs in enc: by_cont[fs].append((a,v))
    by_inner[max(enc)].append((a,v))
def view(g):
    return {fs:dict(func_start=fs,n_sites=len(I),sites=sorted({a for a,_ in I}),
              distinct=sorted({v for _,v in I})) for fs,I in g.items()}
CONT=view(by_cont); INNER=view(by_inner)
def dist(fd):
    return dict(funcs=len(fd),exactly1=sum(1 for f in fd.values() if len(f['distinct'])==1),
       ge2=sum(1 for f in fd.values() if len(f['distinct'])>=2),
       ge3=sum(1 for f in fd.values() if len(f['distinct'])>=3),
       zero=sum(1 for f in fd.values() if len(f['distinct'])==0))
def fish(a,b,c,d):
    import math
    n=a+b+c+d
    def p_of(x):
        bb=(a+b)-x; cc=(a+c)-x; dd=n-x-bb-cc
        if bb<0 or cc<0 or dd<0: return 0.0
        return (math.comb(a+b,x)*math.comb(c+d,a+c-x))/math.comb(n,a+c)
    p0=p_of(a); tot=0.0
    for x in range(0,min(a+b,a+c)+1):
        p=p_of(x)
        if p<=p0*(1+1e-9): tot+=p
    return min(1.0,tot)
def chi2y(a,b,c,d):
    n=a+b+c+d; num=(abs(a*d-b*c)-n/2.0)**2*n; den=(a+b)*(c+d)*(a+c)*(b+d)
    if den==0: return float('nan')
    return num/den
def chi2p(x):
    import math
    if x!=x: return float('nan')
    return math.erfc(math.sqrt(max(x,0.0)/2.0))
def sites_of(T):
    raw=[base+m.start() for m in re.finditer(re.escape(b'\x68'+T.to_bytes(4,'little')),text)]
    return raw,[a for a in raw if a in pushset and pushset[a]==T and sz_at[a-base]==5]
def group_of(sites):
    g=collections.defaultdict(list); amb=[]
    for a in sites:
        enc=enclosing(a)
        r=dict(site=hex(a),enclosing=[hex(x) for x in sorted(enc)],n=len(enc))
        if len(enc)!=1: amb.append(r)
        if enc: g[max(enc)].append(a)
    return g,amb
T1=0x7f7c80; T3=0x7ed358
raw1,s1=sites_of(T1); raw3,s3=sites_of(T3)
g1,amb1=group_of(s1); g3,amb3=group_of(s3)
def table(G,fd):
    """2x2: group vs rest, using the given per-function view"""
    G=[fs for fs in G if fs in fd]
    g1_=sum(1 for fs in G if len(fd[fs]['distinct'])==1); g2_=len(G)-g1_
    rest=[fs for fs in fd if fs not in set(G)]
    e1=sum(1 for fs in rest if len(fd[fs]['distinct'])==1); er=len(rest)-e1
    return dict(group_funcs=len(G),group_exactly1=g1_,group_ge2=g2_,
      pct_group=round(100.0*g1_/max(len(G),1),2),
      rest_funcs=len(rest),rest_exactly1=e1,rest_pct1=round(100.0*e1/max(len(rest),1),2),
      table=[[g1_,g2_],[e1,er]],fisher_p=fish(g1_,g2_,e1,er),
      chi2_yates=chi2y(g1_,g2_,e1,er),chi2_p=chi2p(chi2y(g1_,g2_,e1,er)))
R=dict(
  method=dict(
    instruction_graph='complete linear sweep of .text with capstone CS_MODE_32 disasm_lite, 65536-byte chunks, resynced byte-wise on decode gaps; %d instructions, %d resync points'%(NS,json.load(open(OUT+'x120exec_sweep_meta.json'))['resync']),
    function_entries='PE AddressOfEntryPoint (0x%x) plus every direct rel32 call target (E8) that is a decoded instruction start => %d entries'%(ENTRY,len(ENTRIES)),
    site_to_function='reverse CFG walk: from the site, walk predecessors over fall-through/jcc/jmp-target/call-target edges; stop whenever a predecessor is one of the %d entries; the entries reached are the enclosing set. Tested unique for every 0x7f7c80 site.'%len(ENTRIES),
    function_body_view_A='containment: a site belongs to every entry whose enclosing set contains it (nested duplicates possible)',
    function_body_view_B='innermost partition: a site belongs only to the greatest enclosing entry (sites sum to the site total)'),
  iid_census=dict(rule='4-byte-aligned A in file-backed .rdata/.data with dword1==0, (dword2&0xFFFF)==0x00C0, dword3==0x46000000',
    count=len(iid),addrs=[hex(a) for a in iidaddrs],section={hex(a):iid[a] for a in iidaddrs},
    dwords={hex(a):[hex(x) for x in struct.unpack('<4I',d[(a-IB):(a-IB)+16])] for a in iidaddrs}),
  iid_push_sites_total=len(IIDP),
  unresolved_sites=[[hex(a),hex(v)] for a,v in unres],
  distribution_containment=dist(CONT),
  distribution_innermost=dist(INNER),
  entries_total=len(ENTRIES),
  q1=dict(target=hex(T1),raw_5byte_hits=len(raw1),sites=len(s1),
    site_addrs=[hex(a) for a in s1],rejected=[hex(a) for a in raw1 if a not in set(s1)],
    n_functions=len(g1),ambiguity=amb1,
    functions=[dict(func_start=hex(fs),site_count=len(v),sites=[hex(x) for x in sorted(v)],
      n_distinct=len(CONT.get(fs,{}).get('distinct',[])),
      distinct_iids=[hex(x) for x in CONT.get(fs,{}).get('distinct',[])]) for fs,v in sorted(g1.items())],
    table_containment=table(list(g1),CONT), table_innermost=table(list(g1),INNER)),
  q2=dict(containment=dist(CONT),innermost=dist(INNER),
    per_function_containment=[dict(func_start=hex(k),n_sites=len(v['sites']),
      sites=[hex(x) for x in v['sites']],n_distinct=len(v['distinct']),
      distinct=[hex(x) for x in v['distinct']]) for k,v in sorted(CONT.items())],
    per_function_innermost=[dict(func_start=hex(k),n_sites=len(v['sites']),
      sites=[hex(x) for x in v['sites']],n_distinct=len(v['distinct']),
      distinct=[hex(x) for x in v['distinct']]) for k,v in sorted(INNER.items())]),
  q3=dict(target=hex(T3),raw_5byte_hits=len(raw3),sites=len(s3),
    site_addrs=[hex(a) for a in s3],rejected=[hex(a) for a in raw3 if a not in set(s3)],
    is_in_iid_census=(T3 in iidset),
    bytes16=d[(T3-IB):(T3-IB)+16].hex(),
    dwords=[hex(x) for x in struct.unpack('<4I',d[(T3-IB):(T3-IB)+16])],
    n_functions=len(g3),ambiguity=amb3,
    functions=[dict(func_start=hex(fs),site_count=len(v),sites=[hex(x) for x in sorted(v)],
      n_distinct=len(CONT.get(fs,{}).get('distinct',[])),
      distinct_iids=[hex(x) for x in CONT.get(fs,{}).get('distinct',[])]) for fs,v in sorted(g3.items())],
    table_containment=table(list(g3),CONT),table_innermost=table(list(g3),INNER)),
)
json.dump(R,open(OUT+'x120exec_core.json','w'),indent=1)
print('entries',len(ENTRIES))
print('iid sites',len(IIDP),'unresolved',len(unres))
print('dist containment',R['distribution_containment'])
print('dist innermost  ',R['distribution_innermost'])
print('Q1 sites',len(s1),'funcs',len(g1),'amb',len(amb1))
for f in R['q1']['functions']: print('  ',f['func_start'],f['site_count'],f['n_distinct'],f['distinct_iids'])
print('Q1 table containment',R['q1']['table_containment'])
print('Q1 table innermost  ',R['q1']['table_innermost'])
print('Q3 sites',len(s3),'funcs',len(g3),'amb',len(amb3),'in iid census',R['q3']['is_in_iid_census'])
print('Q3 dwords',R['q3']['dwords'])
for f in R['q3']['functions']: print('  ',f['func_start'],f['site_count'],f['n_distinct'],f['distinct_iids'])
print('Q3 table containment',R['q3']['table_containment'])
print('unresolved sample',R['unresolved_sites'][:10])
