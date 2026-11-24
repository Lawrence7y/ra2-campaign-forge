import struct,json,bisect,re,array as _ar,math
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
startset=set(starts)
R={}
def is_start(a): return a in startset

# boundary sets
def padset(minrun):
    out=[]
    for i,a in enumerate(starts):
        o=a-base
        if o==0: continue
        p=o-1; n=0
        while p>=0 and text[p]==0xCC: n+=1; p-=1
        if n>=minrun: out.append(a)
    return sorted(out)
C2=sorted({int(starts[i]) for i in range(1,len(starts)) if kinds[i-1] in (1,2)})
C3=sorted({int(o,16) for a,k,o in calls if k==3 and base<=int(o,16)<tend and is_start(int(o,16))})
Cunion=sorted(set(C2)|set(C3))
C1_2=padset(2); C1_3=padset(3)
BS=dict(C2_afterterm=C2, C3_calltarget=C3, Cunion_C2_or_C3=Cunion,
        C1_int3pad_ge2=C1_2, C1_int3pad_ge3=C1_3)
R['boundary_sets']={k:len(v) for k,v in BS.items()}

def extent(arr,fs):
    i=bisect.bisect_right(arr,fs)
    return arr[i] if i<len(arr) else tend
def fns_by(arr):
    """map iid-push instruction -> nearest prior boundary; also function ranges touched."""
    return arr, extent

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
        s=S[nm]; blob=d[s['raw']:s['raw']+s['vs']]
        for off in range(0,len(blob)-16,4):
            if guid_ok(blob[off:off+16],drop_d2,d4,d3low): hits[IB+s['va']+off]=nm
    return hits
iid=scan()

# per-function analysis under a boundary set
def analyze(arr):
    fns={}
    for a,v in pushset.items():
        if v not in iid: continue
        i=bisect.bisect_right(arr,a)-1
        fs=arr[i] if i>=0 else base
        fns.setdefault(fs,[]).append((a,v))
    out={}
    for fs,items in fns.items():
        out[fs]=dict(func_start=fs,func_end=extent(arr,fs),
                     sites=sorted({a for a,_ in items}),
                     distinct=sorted({v for _,v in items}))
    return out
def dist(fns):
    c={0:0,1:0,2:0}
    for f in fns.values():
        n=len(f['distinct'])
        c[0 if n==0 else (1 if n==1 else 2)]+=1
    return dict(total=len(fns),zero=c[0],exactly1=c[1],ge2=c[2],
                ge3=sum(1 for f in fns.values() if len(f['distinct'])>=3))
Q2={}
FNS={}
for k,arr in BS.items():
    fns=analyze(arr); FNS[k]=fns
    Q2[k]=dist(fns)
R['q2_full_text_distribution']=Q2

TARGET=0x7f7c80
site7f=[a for a in sorted(pushset) if pushset[a]==TARGET]
# group membership of those sites under each criterion
grp={}
for k,arr in BS.items():
    g={}
    for a in site7f:
        i=bisect.bisect_right(arr,a)-1
        fs=arr[i] if i>=0 else base
        g.setdefault(fs,[]).append(a)
    grp[k]={fs:dict(sites=sorted(ss),distinct=sorted({pushset[x] for x in ss}),
                    all_distinct_in_fn=sorted(FNS[k][fs]['distinct']) if fs in FNS[k] else []) for fs,ss in g.items()}
R['q2_group_sizes']={k:len(v) for k,v in grp.items()}

# Fisher exact
def logfact(n): return math.lgamma(n+1.0)
def hyper_lp(a,b,c,d):
    n=a+b+c+d
    return (logfact(a+b)+logfact(c+d)+logfact(a+c)+logfact(b+d)-logfact(n)-logfact(a)-logfact(b)-logfact(c)-logfact(d))
def fisher_two_sided(a,b,c,d):
    base_lp=hyper_lp(a,b,c,d); p=0.0
    ra=range(0,min(a+b,a+c)+1)
    for x in ra:
        bb=a+b-x; cc=a+c-x; dd=c+d-(a+c-x)
        if bb<0 or cc<0 or dd<0: continue
        lp=hyper_lp(x,bb,cc,dd)
        if lp<=base_lp+1e-9: p+=math.exp(lp)
    return min(1.0,p)
def chi2_yates(a,b,c,d):
    n=a+b+c+d
    num=(abs(a*d-b*c)-n/2.0)**2*n
    den=(a+b)*(c+d)*(a+c)*(b+d)
    return num/den if den else float('nan')
def chi2_sf(x):
    # df=1 survival = erfc(sqrt(x/2))
    return math.erfc(math.sqrt(max(x,0.0)/2.0))
TEST={}
for k,fns in FNS.items():
    G=set(grp[k].keys())
    g1=sum(1 for fs in G if len(fns.get(fs,{}).get('distinct',[]))==1)
    g2=len(G)-g1
    # full set including group
    allf=[(fs,len(f['distinct'])) for fs,f in fns.items()]
    all1=sum(1 for _,n in allf if n==1); allrest=len(allf)-all1
    # full set excluding group
    ex=[(fs,n) for fs,n in allf if fs not in G]
    ex1=sum(1 for _,n in ex if n==1); exrest=len(ex)-ex1
    a_,b_,c_,d_=g1,g2,all1-g1,allrest-g2
    a2,b2,c2,d2=g1,g2,ex1,exrest
    ch=chi2_yates(a2,b2,c2,d2)
    TEST[k]=dict(group_funcs=len(G),group_exactly1=g1,group_ge2=g2,
        full_incl=dict(total=len(allf),exactly1=all1,ge2=allrest,
            pct1=round(100.0*all1/max(len(allf),1),2)),
        full_excl=(dict(total=len(ex),exactly1=ex1,ge2=exrest,
            pct1=round(100.0*ex1/max(len(ex),1),2)) if ex else None),
        pct1_group=round(100.0*g1/max(len(G),1),2),
        table_incl=[[g1,g2],[all1-g1,allrest-g2]],
        table_excl=[[g1,g2],[ex1,exrest]],
        fisher_p_incl=fisher_two_sided(a_,b_,c_,d_),
        fisher_p_excl=fisher_two_sided(a2,b2,c2,d2),
        chi2_yates_excl=ch, chi2_p_excl=chi2_sf(ch))
R['q2_test']=TEST

# ---------------- Q3 ----------------
T3=0x7ed358
raw3=[base+m.start() for m in re.finditer(re.escape(b'\x68'+T3.to_bytes(4,'little')),text)]
sites3=[a for a in raw3 if a in pushset and pushset[a]==T3]
rej3=[a for a in raw3 if a not in sites3]
IAT_LOAD=0x7e15f8; IAT_SAVE=0x7e15f4; IAT_STGOPEN=0x7e15e4; IAT_STGCREATE=0x7e15c8
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
def fn_refs(fs,fe):
    o1=fs-base; o2=min(fe,tend)-base
    blob=text[o1:o2]
    refs={}
    for i in md.disasm_lite(blob,fs):
        a,sz,m,op=i
        for tag,addr in (('OleLoadFromStream',IAT_LOAD),('OleSaveToStream',IAT_SAVE),
                         ('StgOpenStorage',IAT_STGOPEN),('StgCreateDocfile',IAT_STGCREATE)):
            if '0x%x'%addr in op:
                refs.setdefault(tag,[]).append((hex(a),m,op))
    return refs
Q3={}
for k,arr in BS.items():
    per=[]
    for a in sites3:
        i=bisect.bisect_right(arr,a)-1
        fs=arr[i] if i>=0 else base
        fe=extent(arr,fs)
        f=FNS[k].get(fs)
        refs=fn_refs(fs,fe)
        per.append(dict(site=hex(a),func_start=hex(fs),func_end=hex(fe),
                        n_distinct_iids=(len(f['distinct']) if f else 0),
                        iid_list=([hex(x) for x in f['distinct']] if f else []),
                        ole_load_calls=refs.get('OleLoadFromStream',[]),
                        ole_save_calls=refs.get('OleSaveToStream',[])))
    Q3[k]=per
R['q3']=dict(target=hex(T3),raw_push_hits=len(raw3),valid_sites=len(sites3),
    sites=[hex(a) for a in sites3],rejected=[hex(a) for a in rej3],
    per_criterion=Q3)
# Q3 2x2 vs full
Q3T={}
for k in BS:
    fns=FNS[k]; G={int(p['func_start'],16) for p in Q3[k]}
    g1=sum(1 for fs in G if len(fns.get(fs,{}).get('distinct',[]))==1); g2=len(G)-g1
    ex=[(fs,f) for fs,f in fns.items() if fs not in G]
    ex1=sum(1 for fs,f in ex if len(f['distinct'])==1); exr=len(ex)-ex1
    ch=chi2_yates(g1,g2,ex1,exr)
    Q3T[k]=dict(group_funcs=len(G),exactly1=g1,ge2=g2,pct1_group=round(100.0*g1/max(len(G),1),2),
        full_excl=dict(total=len(ex),exactly1=ex1,pct1=round(100.0*ex1/max(len(ex),1),2)),
        table=[[g1,g2],[ex1,exr]],fisher_p=fisher_two_sided(g1,g2,ex1,exr),
        chi2_yates=ch,chi2_p=chi2_sf(ch))
R['q3_test']=Q3T
json.dump(R,open(OUT+'x120exec_q23.json','w'),indent=1)
print('boundary sets',R['boundary_sets'])
print('Q2 dist',json.dumps(Q2,indent=1))
print('Q2 group sizes',R['q2_group_sizes'])
for k,v in TEST.items():
    print(k,'grp',v['group_funcs'],'e1',v['group_exactly1'],'pct',v['pct1_group'],
          '| full(excl)',v['full_excl'],'| p_excl',v['fisher_p_excl'])
print('Q3 sites',len(sites3),[hex(a) for a in sites3])
for k in BS:
    for p in Q3[k]:
        print(k,p['site'],p['func_start'],'nIID',p['n_distinct_iids'],'iids',p['iid_list'],
              'load',len(p['ole_load_calls']),'save',len(p['ole_save_calls']))
