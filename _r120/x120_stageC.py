# Q1..Q4 measurements with multiple boundary criteria. Self-written PE parse; reuses stageA sweep.
import struct, json, bisect, re, array as _ar, math
P='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r120/'
d=open(P,'rb').read()
e=struct.unpack_from('<I',d,0x3c)[0]
nsec=struct.unpack_from('<H',d,e+6)[0]; optsz=struct.unpack_from('<H',d,e+20)[0]
IB=struct.unpack_from('<I',d,e+24+28)[0]; sec=e+24+optsz
S={}
for i in range(nsec):
    nm=d[sec+40*i:sec+40*i+8].rstrip(b'\0').decode()
    vs,va,rs,ra=struct.unpack_from('<IIII',d,sec+40*i+8); S[nm]=dict(va=va,vs=vs,raw=ra,rawsz=rs)
tv=S['.text']; text=d[tv['raw']:tv['raw']+tv['vs']]; base=IB+tv['va']; tend=base+len(text)
starts=_ar.array('I'); starts.frombytes(open(OUT+'x120_starts.bin','rb').read())
kinds=_ar.array('B'); kinds.frombytes(open(OUT+'x120_kinds.bin','rb').read())
A=json.load(open(OUT+'x120_stageA.json'))
pushset={a:v for a,v in A['pushes']}
calls=[(a,k,o) for a,k,o in A['calls']]
def is_start(a):
    i=bisect.bisect_left(starts,a); return i<len(starts) and starts[i]==a
R={}

# ---------------- boundary criterion candidate sets ----------------
C1=[]
for i,a in enumerate(starts):
    o=a-base
    if o==0: continue
    p=o-1; n=0
    while p>=0 and text[p]==0xCC: n+=1; p-=1
    if n>=1: C1.append(a)
C1.sort()
C2=[int(starts[i]) for i in range(1,len(starts)) if kinds[i-1] in (1,2)]
C2=sorted(set(C2))
C3=sorted({int(o,16) for a,k,o in calls
           if k==3 and base<=int(o,16)<tend and is_start(int(o,16))})
C1s=C1; C2s=C2; C3s=C3
def mk(arr): return arr, len(arr)
def nearest(arr,addr):
    i=bisect.bisect_right(arr,addr)-1
    return arr[i] if i>=0 else None
def nextof(arr,fs):
    i=bisect.bisect_right(arr,fs)
    return arr[i] if i<len(arr) else tend
def inter(a,b):
    sa=sb=None
    bs=set(b); return sorted(x for x in a if x in bs)
Cstrict=sorted(set(C2s)&set(C3s))
Cpad_call=sorted(set(C1s)&set(C3s))
R['boundary_candidate_counts']=dict(C1_int3_pad=len(C1s),C2_after_terminator=len(C2s),
    C3_direct_call_target=len(C3s),Cstrict_C2_and_C3=len(Cstrict),
    C1pad_and_C3=len(Cpad_call))

# ---------------- IID scans ----------------
def guid_ok(b,drop_d2=False,d4=0x46000000,d3low=0x00C0):
    d1,d2,d3,d4_=struct.unpack('<4I',b)
    if d4_!=d4: return False
    if not drop_d2 and d2!=0: return False
    if d3low is not None and (d3 & 0xFFFF)!=d3low: return False
    return True
def scan(drop_d2=False,d4=0x46000000,d3low=0x00C0,sections=('.rdata','.data')):
    hits={}
    for nm in sections:
        s=S[nm]; blob=d[s['raw']:s['raw']+s['vs']]
        for off in range(0,len(blob)-16,4):
            if guid_ok(blob[off:off+16],drop_d2,d4,d3low):
                hits[IB+s['va']+off]=nm
    return hits
iid=scan()
R['iid_census']=dict(count=len(iid),addrs=[hex(a) for a in sorted(iid)],
   addr_section={hex(a):iid[a] for a in sorted(iid)})
R['ctrl_a_d4_46000001']=dict(rule='d4==0x46000001',count=len(scan(d4=0x46000001)),
    addrs=[hex(x) for x in sorted(scan(d4=0x46000001))])
cb=scan(drop_d2=True)
R['ctrl_b_drop_d2']=dict(rule='drop d2==0, keep d3low==0x00C0 and d4==0x46000000',
    count=len(cb),addrs=[hex(x) for x in sorted(cb)],baseline=len(iid),
    strictly_greater=len(cb)>len(iid))
cb2=scan(drop_d2=True,d3low=None)
R['ctrl_b2_drop_d2_and_d3']=dict(rule='drop d2==0 and drop d3low, keep d4==0x46000000',
    count=len(cb2),addrs=[hex(x) for x in sorted(cb2)])
cb3=scan(drop_d2=False,d3low=None)
R['ctrl_b3_d3_dropped_only']=dict(rule='keep d2==0, drop d3low',count=len(cb3),
    addrs=[hex(x) for x in sorted(cb3)])
cb4=scan(drop_d2=False,d4=0x46000001,d3low=None)
R['controls_summary']=dict(primary=len(iid),a=len(scan(d4=0x46000001)),
    b_drop_d2=len(cb),b2_drop_d2_d3=len(cb2),b3_drop_d3=len(cb3),b4=len(cb4))

# ---------------- Q1 ----------------
TARGET=0x7f7c80
raw=[base+m.start() for m in re.finditer(re.escape(b'\x68'+TARGET.to_bytes(4,'little')),text)]
sites=[a for a in raw if a in pushset and pushset[a]==TARGET]
per=[]
groups={}
for critname,carr in (('C1_int3pad',C1s),('C2_afterterm',C2s),('C3_calltarget',C3s),
                      ('Cstrict_C2andC3',Cstrict),('Cpad_and_call',Cpad_call)):
    g={}
    for a in sites:
        fs=nearest(carr,a)
        g.setdefault(fs,[]).append(a)
    groups[critname]=g
    per.append(dict(criterion=critname,n_distinct_function_starts=len(g),
                    starts=[hex(k) for k in sorted(g) if k is not None]))
# fake boundary control: addr-0x200
gfake={}
for a in sites:
    fs=a-0x200
    gfake.setdefault(fs,[]).append(a)
groups['FAKE_addr_minus_0x200']=gfake
per.append(dict(criterion='FAKE_addr_minus_0x200',n_distinct_function_starts=len(gfake),
                starts=[hex(k) for k in sorted(gfake)]))

# ambiguity per site: list all candidate starts from all criteria (excluding fake)
def cands(a):
    out={}
    for nm,arr in (('C1_int3pad',C1s),('C2_afterterm',C2s),('C3_calltarget',C3s),('Cstrict',Cstrict)):
        v=nearest(arr,a)
        if v is not None: out[nm]=hex(v)
    return out
per_site=[dict(site=hex(a),candidates=cands(a)) for a in sites]
uniq_cand=set()
for p in per_site:
    uniq_cand.add(tuple(sorted(p['candidates'].values())))
R['q1']=dict(target=hex(TARGET),raw_pushopcode_hits=len(raw),valid_sites=len(sites),
    sites=[hex(a) for a in sites],
    push_detection_method='scan .text for the 5-byte sequence 0x68 + little-endian(0x7f7c80); accept only if the 0x68 address is a decoded instruction start from a chunked (64KB) capstone linear sweep AND capstone decodes it as push with immediate equal to 0x7f7c80',
    boundary_summary=per,
    distinct_candidate_start_vectors=sorted(list(uniq_cand)),
    per_site_candidates=per_site)

# function extents & IID push counting, for each criterion set
def analyze(carr, g):
    out=[]
    for fs,ss in sorted(g.items()):
        if fs is None: fs=base
        fe=nextof(carr,fs) if carr else tend
        i=bisect.bisect_left(starts,fs); j=bisect.bisect_left(starts,fe)
        vals=[pushset[int(starts[k])] for k in range(i,j) if int(starts[k]) in pushset]
        iidv=sorted({v for v in vals if v in iid})
        out.append(dict(func_start=hex(fs),func_end_exclusive=hex(fe),
                        site_count=len(ss),sites=[hex(x) for x in sorted(ss)],
                        distinct_iids=[hex(v) for v in iidv],n_distinct=len(iidv)))
    return out
R['q1_groups']={k:analyze(dict((nm,arr) for nm,arr in
              (('C1_int3pad',C1s),('C2_afterterm',C2s),('C3_calltarget',C3s),
               ('Cstrict_C2andC3',Cstrict),('Cpad_and_call',Cpad_call)))[k], v)
              for k,v in groups.items() if k!='FAKE_addr_minus_0x200'}
def summ(gs):
    return dict(funcs=len(gs),exactly1=sum(1 for x in gs if x['n_distinct']==1),
                ge2=sum(1 for x in gs if x['n_distinct']>=2),
                zero=sum(1 for x in gs if x['n_distinct']==0))
R['q1_summary']={k:summ(v) for k,v in R['q1_groups'].items()}
json.dump(R,open(OUT+'x120exec_q1_partial.json','w'),indent=1)
print('IID',len(iid),'ctrlA',len(scan(d4=0x46000001)),'ctrlB',len(cb),'ctrlB2',len(cb2),'ctrlB3',len(cb3))
print('boundary counts',R['boundary_candidate_counts'])
print('sites',len(sites),'raw',len(raw))
print('q1_summary',json.dumps(R['q1_summary'],indent=1))
for k,v in R['q1_groups'].items():
    print(k)
    for f in v: print('   %s n=%d sites=%d iid=%s'%(f['func_start'],f['n_distinct'],f['site_count'],f['distinct_iids']))
