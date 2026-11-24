# R120 exhaustive measurement (Q1..Q4). Self-written PE parse, streaming disasm facts.
import struct, json, bisect, re, array as _ar, math
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
def ld(nm,ty):
    a=_ar.array(ty); a.frombytes(open(OUT+nm+'.bin','rb').read()); return a
starts=ld('a2_starts','I'); kinds=ld('a2_kinds','B'); sizes=ld('a2_sizes','B')
pushes=ld('a2_pushes','I'); pushv=ld('a2_pushv','I')
calls=ld('a2_calls','I'); callk=ld('a2_callk','B'); callt=ld('a2_callt','I')
sm=json.load(open(OUT+'x120exec_sweep_meta.json'))
pushset={a:v for a,v in zip(pushes,pushv)}; startset=set(starts); ns=len(starts)
def sidx(a):
    i=bisect.bisect_left(starts,a)
    return i if i<ns and starts[i]==a else None
callset={a:(callk[i],callt[i]) for i,a in enumerate(calls)}
IAT_LOAD=0x7e15f8; IAT_SAVE=0x7e15f4
def rva2off(rva):
    for nm,s in SEC.items():
        if s['va']<=rva<s['va']+min(s['vs'],s['rawsz']): return s['raw']+(rva-s['va'])
    return None
impname={}
o=rva2off(DIRS[1][0]); i=0
while True:
    ilt,ts,fc,nr,iat=struct.unpack_from('<IIIII',d,o+20*i)
    if nr==0 and iat==0: break
    dll=d[rva2off(nr):rva2off(nr)+32].split(b'\0')[0].decode('latin1'); j=0
    while True:
        v=struct.unpack_from('<I',d,rva2off(iat)+4*j)[0]
        if v==0: break
        nm=None
        if not (v&0x80000000): nm=d[rva2off(v)+2:rva2off(v)+66].split(b'\0')[0].decode('latin1')
        impname[IB+iat+4*j]=(dll,nm); j+=1
    i+=1
# ---- boundary sets
B1=[a for a in starts if (a-base)>0 and text[a-base-1]==0xCC]
B2=sorted({int(starts[i]) for i in range(1,ns) if kinds[i-1] in (1,2)})
B3=sorted({int(callt[i]) for i in range(len(calls)) if callk[i]==3 and base<=int(callt[i])<tend and int(callt[i]) in startset})
rd_addr=ld('rd2_addr','I'); rd_tgt=ld('rd2_tgt','I'); rd_kind=ld('rd2_kind','B')
RDB=sorted({int(t) for t,k in zip(rd_tgt,rd_kind) if k==3 and base<=int(t)<tend and int(t) in startset})
CRIT=[('B1_after_int3_padding',B1),('B2_after_ret_or_uncond_jmp',B2),
      ('B3_direct_call_target',B3),('RD_direct_call_target',RDB)]
def nearest(arr,a):
    i=bisect.bisect_right(arr,a)-1
    return arr[i] if i>=0 else None
def nextb(arr,fs):
    i=bisect.bisect_right(arr,fs); return arr[i] if i<len(arr) else tend
# ---- IID census
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
iid=scan(); iidaddrs=sorted(iid)
# ---- function grouping helpers
def funcs_for(arr,items):
    g={}
    for a,v in items: g.setdefault(nearest(arr,a),[]).append((a,v))
    out=[]
    for fs,I in sorted(g.items()):
        if fs is None: continue
        fe=nextb(arr,fs); ii=sidx(fs) or bisect.bisect_left(starts,fs)
        j=bisect.bisect_left(starts,fe)
        vals=[pushset[int(starts[k])] for k in range(ii,j) if int(starts[k]) in pushset]
        dv=sorted({v for v in vals if v in iid})
        out.append(dict(fs=fs,fe=fe,n_sites=len(I),sites=sorted({a for a,_ in I}),distinct=dv))
    return out
def summarize(fl):
    return dict(funcs=len(fl),exactly1=sum(1 for f in fl if len(f['distinct'])==1),
                ge2=sum(1 for f in fl if len(f['distinct'])>=2),
                ge3=sum(1 for f in fl if len(f['distinct'])>=3),
                zero=sum(1 for f in fl if len(f['distinct'])==0))
def fisher(a,b,c,d):
    lf=math.lgamma; n=a+b+c+d
    def lp(x):
        bb=a+b-x; cc=a+c-x; dd=d-(a+c-x)
        if bb<0 or cc<0 or dd<0: return None
        return (lf(a+b+1)+lf(c+d+1)+lf(a+c+1)+lf(b+d+1)-lf(n+1)-lf(x+1)
                -lf(a+b-x+1)-lf(a+c-x+1)-lf(n-a-c+x+1))
    base_lp=lp(a); p=0.0
    for x in range(0,min(a+b,a+c)+1):
        v=lp(x)
        if v is not None and v<=base_lp+1e-12: p+=math.exp(v)
    return min(1.0,p)
def chi2y(a,b,c,d):
    n=a+b+c+d; num=(abs(a*d-b*c)-n/2.0)**2*n; den=(a+b)*(c+d)*(a+c)*(b+d)
    return (num/den) if den else float('nan')
def chi2p(x): return math.erfc(math.sqrt(max(x,0.0)/2.0))
IIDP=[(a,v) for a,v in zip(pushes,pushv) if v in iid]
HEAD=dict(target=P,file_len=hex(len(d)),e_lfanew=hex(e),ImageBase=hex(IB),SizeOfImage=hex(SOI),
  entry_va=hex(ENTRY),
  sections={k:dict(va=hex(IB+v['va']),vsize=hex(v['vs']),raw=hex(v['raw']),rawsize=hex(v['rawsz']),
     file_backed_va=hex(IB+v['va'])+'-'+hex(IB+v['va']+min(v['vs'],v['rawsz']))) for k,v in SEC.items()},
  data_dirs={str(i):[hex(x) for x in DIRS[i]] for i in (1,2,5)},
  sweep=dict(mode='capstone CS_MODE_32, disasm_lite, 64KB chunks, detail=False',
     insn_decoded=sm['n_insn'],resync_points=sm['resync'],push_imm_insns=sm['n_push_imm'],
     call_insns=sm['n_calls']),
  rd=json.load(open(OUT+'rd2_meta.json')),
  ole_imports={hex(k):v for k,v in impname.items() if v[1] in
     ('OleLoadFromStream','OleSaveToStream','StgOpenStorage','StgCreateDocfile','CoCreateInstance','OleRun','StringFromGUID2')})
R={'header':HEAD}

# ================= Q2 =================
Q2=dict(criterion_distributions=[],group_stats=[])
for cname,arr in CRIT:
    fl=funcs_for(arr,IIDP)
    Q2['criterion_distributions'].append(dict(criterion=cname,candidates=len(arr),
        total_funcs_pushing_ge1_iid=len(fl),summary=summarize(fl),
        detail=[dict(func_start=hex(f['fs']),func_end=hex(f['fe']),n_sites=f['n_sites'],
                     n_distinct=len(f['distinct']),distinct=[hex(x) for x in f['distinct']]) for f in fl]))
T1=0x7f7c80
raw1=[base+m.start() for m in re.finditer(re.escape(b'\x68'+T1.to_bytes(4,'little')),text)]
sites1=[a for a in raw1 if a in pushset and pushset[a]==T1 and sizes[sidx(a)]==5]
for cname,arr in CRIT:
    fl=funcs_for(arr,IIDP); fdict={f['fs']:f for f in fl}
    G=sorted({nearest(arr,a) for a in sites1})
    g1=sum(1 for fs in G if fs in fdict and len(fdict[fs]['distinct'])==1)
    g2=len(G)-g1
    ex=[f for f in fl if f['fs'] not in G]
    e1=sum(1 for f in ex if len(f['distinct'])==1); er=len(ex)-e1
    ch=chi2y(g1,g2,e1,er)
    Q2['group_stats'].append(dict(criterion=cname,
        group_funcs=len(G),group_exactly1=g1,group_ge2=g2,
        group_pct1=round(100.0*g1/max(len(G),1),2),
        group_func_list=[hex(x) for x in G],
        rest_funcs=len(ex),rest_exactly1=e1,rest_ge2=er,
        rest_pct1=round(100.0*e1/max(len(ex),1),2),
        full_incl=dict(funcs=len(fl),exactly1=sum(1 for f in fl if len(f['distinct'])==1),
                       pct1=round(100.0*sum(1 for f in fl if len(f['distinct'])==1)/max(len(fl),1),2)),
        table_group_vs_rest=[[g1,g2],[e1,er]],
        fisher_p_two_sided=fisher(g1,g2,e1,er),
        chi2_yates=ch,chi2_p_df1=chi2p(ch)))
Q2['iid_push_site_counts']={hex(v):sum(1 for a,x in IIDP if x==v) for v in iidaddrs}
R['q2']=Q2

# ================= Q1 =================
Q1=dict(target=hex(T1),raw_5byte_hits=len(raw1),sites=len(sites1),
   site_addrs=[hex(a) for a in sites1],
   rejected=[hex(a) for a in raw1 if a not in sites1],
   method='find bytes 68+LE32(0x7f7c80) in .text; accept only if (1) the address is an instruction start of the chunked capstone linear sweep, (2) that instruction is push, (3) op_str is exactly 0x7f7c80, (4) insn size==5 so bytes[1:5] are the imm32 operand (not incidental data)',
   per_criterion=[])
for cname,arr in CRIT:
    fl=funcs_for(arr,[(a,pushset[a]) for a in sites1])
    Q1['per_criterion'].append(dict(criterion=cname,candidates=len(arr),n_functions=len(fl),
        summary=summarize(fl),
        functions=[dict(func_start=hex(f['fs']),func_end=hex(f['fe']),site_count=f['n_sites'],
            sites=[hex(x) for x in f['sites']],distinct_iids=[hex(x) for x in f['distinct']],
            n_distinct=len(f['distinct'])) for f in fl]))
amb=[]
for a in sites1:
    amb.append(dict(site=hex(a),candidates={c:hex(nearest(arr,a)) for c,arr in CRIT}))
Q1['per_site_candidates']=amb
Q1['distinct_candidate_vectors']=[json.loads(x) for x in sorted({json.dumps(p['candidates'],sort_keys=True) for p in amb})]
Q1['boundary_uniqueness']='%d distinct candidate-start vectors over %d sites; see distinct_candidate_vectors'%(
   len(Q1['distinct_candidate_vectors']),len(sites1))
R['q1']=Q1

# ================= Q3 =================
T3=0x7ed358
raw3=[base+m.start() for m in re.finditer(re.escape(b'\x68'+T3.to_bytes(4,'little')),text)]
sites3=[a for a in raw3 if a in pushset and pushset[a]==T3 and sizes[sidx(a)]==5]
mdC=Cs=None
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
def refs_in(fs,fe,targets):
    out={}
    ob=text[fs-base:min(fe,tend)-base]
    for (a,sz,m,op) in md.disasm_lite(ob,fs):
        for slot,nm in targets.items():
            if '0x%x'%slot in op: out.setdefault(nm,[]).append(dict(at=hex(a),insn=m+' '+op))
    return out
TGT={IAT_LOAD:'OleLoadFromStream',IAT_SAVE:'OleSaveToStream',0x7e15e4:'StgOpenStorage',0x7e15c8:'StgCreateDocfile'}
Q3=dict(target=hex(T3),raw_5byte_hits=len(raw3),sites=len(sites3),
   site_addrs=[hex(a) for a in sites3],per_criterion=[])
for cname,arr in CRIT:
    fl=funcs_for(arr,IIDP); fdict={f['fs']:f for f in fl}
    rows=[]
    for a in sites3:
        fs=nearest(arr,a); fe=nextb(arr,fs)
        r=refs_in(fs,fe,TGT)
        f=fdict.get(fs)
        rows.append(dict(site=hex(a),func_start=hex(fs),func_end=hex(fe),
            n_distinct_iids=(len(f['distinct']) if f else 0),
            distinct_iids=([hex(x) for x in f['distinct']] if f else []),
            has_OleLoadFromStream=('OleLoadFromStream' in r),
            calls=r))
    G=sorted({nearest(arr,a) for a in sites3})
    g1=sum(1 for fs in G if fs in fdict and len(fdict[fs]['distinct'])==1); g2=len(G)-g1
    ex=[f for f in fl if f['fs'] not in G]
    e1=sum(1 for f in ex if len(f['distinct'])==1); er=len(ex)-e1
    ch=chi2y(g1,g2,e1,er)
    Q3['per_criterion'].append(dict(criterion=cname,rows=rows,
        group_funcs=len(G),group_exactly1=g1,group_ge2=g2,
        group_pct1=round(100.0*g1/max(len(G),1),2),
        rest_funcs=len(ex),rest_exactly1=e1,rest_pct1=round(100.0*e1/max(len(ex),1),2),
        table=[[g1,g2],[e1,er]],fisher_p_two_sided=fisher(g1,g2,e1,er),
        chi2_yates=ch,chi2_p_df1=chi2p(ch)))
R['q3']=Q3

# ================= Q4 =================
Q4={}
ca=scan(d4=0x46000001)
Q4['ctrl_a_d4_46000001']=dict(rule='d4==0x46000001 (rest identical)',count=len(ca),
   addrs=[hex(x) for x in sorted(ca)],expected='0',pass_=(len(ca)==0))
cb=scan(drop_d2=True)
Q4['ctrl_b_drop_d2_zero_check']=dict(rule='drop d2==0, keep (d3&0xFFFF)==0x00C0 and d4==0x46000000',
   count=len(cb),baseline=len(iid),strictly_greater=len(cb)>len(iid),
   addrs=[hex(x) for x in sorted(cb)],
   remark='as specified this control does NOT come out strictly greater: every d3low==0x00C0 & d4==0x46000000 hit already has d2==0, so the d2 clause adds no selectivity on this file')
cb2=scan(drop_d2=True,d3low=None)
Q4['ctrl_b2_drop_d2_and_d3']=dict(rule='drop d2==0 AND drop (d3&0xFFFF)==0x00C0, keep d4==0x46000000',
   count=len(cb2),baseline=len(iid),strictly_greater=len(cb2)>len(iid),
   addrs=[hex(x) for x in sorted(cb2)])
cb3=scan(drop_d2=False,d3low=None)
Q4['ctrl_b3_drop_d3_only']=dict(rule='keep d2==0, drop d3low, keep d4',count=len(cb3),
   addrs=[hex(x) for x in sorted(cb3)],strictly_greater=len(cb3)>len(iid))
# anti-control 1: 0x7f7c94
T4=0x7f7c94
raw4=[base+m.start() for m in re.finditer(re.escape(b'\x68'+T4.to_bytes(4,'little')),text)]
sites4=[a for a in raw4 if a in pushset and pushset[a]==T4]
any4=[base+m.start() for m in re.finditer(re.escape(T4.to_bytes(4,'little')),text)]
sites4b=[a for a,v in zip(pushes,pushv) if v==T4]
Q4['ctrl_c_anti_0x7f7c94']=dict(target=hex(T4),push_imm_sites=len(sites4),
   raw68_hits=len(raw4),imm32_occurrences_anywhere_in_text=len(any4),
   imm32_occurrence_addrs=[hex(x) for x in any4],
   decoded_push_of_this_imm_anywhere=len(sites4b),
   note='0x7f7c94 is 0x7f7c80+0x14, i.e. the third dword (d3) of the 0x7f7c80 GUID; it is not a GUID start')
# anti-control 2: fake boundary = site-0x200
fake=[]
for a in sites1:
    fs=a-0x200
    ob=text[fs-base:fs-base+0x200]
    vals=[]
    for (aa,sz,m,op) in md.disasm_lite(ob,fs):
        if m=='push' and re.fullmatch(r'0x[0-9a-f]+',op):
            v=int(op,16)
            if v in iid: vals.append(v)
    fake.append(dict(func_start=hex(fs),n_distinct=len(set(vals)),distinct=[hex(x) for x in sorted(set(vals))]))
Q4['ctrl_d_anti_fake_boundary_0x200']=dict(
   rule='function start := site_address-0x200, extent := exactly the following 0x200 bytes',
   n_functions=len({f['func_start'] for f in fake}),
   exactly1=sum(1 for f in fake if f['n_distinct']==1),
   ge2=sum(1 for f in fake if f['n_distinct']>=2),
   zero=sum(1 for f in fake if f['n_distinct']==0),
   per_site=fake,
   differs_from_real=None)
R['q4']=Q4

# anti-control 3: "first call after push" vs "OleSaveToStream in same function"
def first_call_after(a, window=64):
    for k in range(1,window):
        if a+k in callset: return a+k,callset[a+k]
    return None,None
def func_has(fs,fe,slot):
    ob=text[fs-base:min(fe,tend)-base]
    return any('0x%x'%slot in op for (aa,sz,m,op) in md.disasm_lite(ob,fs))
rows=[]
for a in sites1:
    cn,(ck,ct)=first_call_after(a)
    fsB3=nearest(B3,a); feB3=nextb(B3,fsB3)
    fsRD=nearest(RDB,a); feRD=nextb(RDB,fsRD)
    rows.append(dict(site=hex(a),first_call_addr=(hex(cn) if cn else None),
       first_call_kind=('direct' if ck==3 else ('indirect' if ck==4 else None)),
       first_call_target=(hex(ct) if ct else None),
       first_call_is_OleSaveToStream_IAT=(ct==IAT_SAVE) if ck==4 else False,
       B3_fn=hex(fsB3),B3_has_OleSaveToStream=func_has(fsB3,feB3,IAT_SAVE),
       RD_fn=hex(fsRD),RD_has_OleSaveToStream=func_has(fsRD,feRD,IAT_SAVE)))
R['q4']['ctrl_e_anti_save_vs_call']=dict(
  per_site=rows,
  n_sites=len(rows),
  call_next_direct_to_OleSaveToStream=sum(1 for r in rows if r['first_call_is_OleSaveToStream_IAT']),
  first_call_within_64_bytes=sum(1 for r in rows if r['first_call_addr']),
  B3_fn_with_OleSaveToStream=sum(1 for r in rows if r['B3_has_OleSaveToStream']),
  RD_fn_with_OleSaveToStream=sum(1 for r in rows if r['RD_has_OleSaveToStream']))
json.dump(R,open(OUT+'x120exec_ALL.json','w'),indent=1)

# split to per-question files
json.dump({'header':HEAD,'q1':R['q1'],'iid_census':dict(count=len(iid),
   addrs=[hex(a) for a in iidaddrs],section={hex(a):iid[a] for a in iidaddrs},
   rule='dword[1]==0, (dword[2]&0xFFFF)==0x00C0, dword[3]==0x46000000, 4-byte aligned, .rdata/.data file-backed bytes')},
   open(OUT+'x120exec_q1.json','w'),indent=1)
json.dump({'header':HEAD,'q2':R['q2'],'iid_census_count':len(iid),
   'iid_census_addrs':[hex(a) for a in iidaddrs]},open(OUT+'x120exec_q2.json','w'),indent=1)
json.dump({'header':HEAD,'q3':R['q3']},open(OUT+'x120exec_q3.json','w'),indent=1)
json.dump({'header':HEAD,'q4':R['q4']},open(OUT+'x120exec_q4.json','w'),indent=1)
print('=== Q1 ===')
for p in Q1['per_criterion']: print(' ',p['criterion'],'fns',p['n_functions'],p['summary'])
print('candidate vectors',len(Q1['distinct_candidate_vectors']))
print('=== Q2 ===')
for g in Q2['group_stats']: print(' ',g['criterion'],'grp',g['group_funcs'],'e1',g['group_exactly1'],
    'pct',g['group_pct1'],'| rest',g['rest_funcs'],g['rest_exactly1'],'pct',g['rest_pct1'],
    '| fisher',round(g['fisher_p_two_sided'],6),'chi2p',round(g['chi2_p_df1'],6))
for d_ in Q2['criterion_distributions']: print('  dist',d_['criterion'],d_['total_funcs_pushing_ge1_iid'],d_['summary'])
print('IID push site counts',Q2['iid_push_site_counts'])
print('=== Q3 ===')
for p in Q3['per_criterion']:
    print(' ',p['criterion'],'sites',len(p['rows']),'e1',p['group_exactly1'],'pct',p['group_pct1'],
          'fisher',round(p['fisher_p_two_sided'],6))
    for r in p['rows']: print('    ',r['site'],r['func_start'],r['n_distinct_iids'],r['has_OleLoadFromStream'])
print('=== Q4 ===')
for k,v in Q4.items():
    if k=='ctrl_e_anti_save_vs_call':
        print(' ',k,{kk:vv for kk,vv in v.items() if kk!='per_site'})
    else:
        print(' ',k,{kk:vv for kk,vv in v.items() if kk not in ('addrs','per_site','imm32_occurrence_addrs')})
