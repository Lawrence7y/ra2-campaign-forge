# Three attribution views + Q3 detail + Q4 controls, all from the same complete graph.
import struct, json, re, array as _ar, collections, bisect, math
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
iatref=ld('a2_iatref','I'); iatslot=ld('a2_iatslot','I')
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
# ---- View C: address-range to next entry
EARR=ENTRIES
def next_entry(a):
    i=bisect.bisect_right(EARR,a); return EARR[i] if i<len(EARR) else tend
# ---- build views
VA=collections.defaultdict(list); VB=collections.defaultdict(list); VC=collections.defaultdict(list)
unres=[]
for a,v in IIDP:
    enc=enclosing(a)
    if enc:
        for fs in enc: VA[fs].append((a,v))
        VB[max(enc)].append((a,v))
    else: unres.append((a,v))
    if a in ENTRIESET: VC[a].append((a,v))
    else:
        i=bisect.bisect_right(EARR,a)-1
        if i>=0: VC[EARR[i]].append((a,v))
def view(g):
    return {fs:dict(func_start=fs,n_sites=len(I),sites=sorted({a for a,_ in I}),
        distinct=sorted({v for _,v in I})) for fs,I in g.items()}
VIEWS={'A_containment':view(VA),'B_innermost':view(VB),'C_addr_range_to_next_entry':view(VC)}
def dist(fd):
    return dict(funcs=len(fd),exactly1=sum(1 for f in fd.values() if len(f['distinct'])==1),
      ge2=sum(1 for f in fd.values() if len(f['distinct'])>=2),
      ge3=sum(1 for f in fd.values() if len(f['distinct'])>=3),
      zero=sum(1 for f in fd.values() if len(f['distinct'])==0))
def fish(a,b,c,d):
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
    return float('nan') if den==0 else num/den
def chi2p(x): return float('nan') if x!=x else math.erfc(math.sqrt(max(x,0.0)/2.0))
def table(Gset,fd):
    G=[fs for fs in Gset if fs in fd]
    a_=sum(1 for fs in G if len(fd[fs]['distinct'])==1); b_=len(G)-a_
    rest=[fs for fs in fd if fs not in set(G)]
    c_=sum(1 for fs in rest if len(fd[fs]['distinct'])==1); d_=len(rest)-c_
    return dict(group_funcs=len(G),group_exactly1=a_,group_ge2=b_,
      pct_group=round(100.0*a_/max(len(G),1),2),
      rest_funcs=len(rest),rest_exactly1=c_,rest_pct1=round(100.0*c_/max(len(rest),1),2),
      table=[[a_,b_],[c_,d_]],fisher_p=fish(a_,b_,c_,d_),
      chi2_yates=chi2y(a_,b_,c_,d_),chi2_p=chi2p(chi2y(a_,b_,c_,d_)))
def sites_of(T):
    raw=[base+m.start() for m in re.finditer(re.escape(b'\x68'+T.to_bytes(4,'little')),text)]
    return raw,[a for a in raw if a in pushset and pushset[a]==T and sz_at[a-base]==5]
T1=0x7f7c80; T3=0x7ed358
raw1,s1=sites_of(T1); raw3,s3=sites_of(T3)
# ---- Q3 function-level detail: OleLoadFromStream presence per candidate enclosing entry
def fn_iats(fs,cap=6000):
    """walk forward from fs over the graph until first return-path exhaustion; collect IAT slot refs"""
    seen=set(); work=[fs]; slots=set(); n=0
    while work:
        a=work.pop()
        while True:
            if a in seen or sz_at[a-base]==0: break
            seen.add(a); n+=1
            kk=kd_at[a-base]; t=tg_at[a-base]
            if kk in (1,5,7): break
            if kk==2:
                if base<=t<tend: work.append(t)
                break
            if kk in (6,3) and base<=t<tend: work.append(t)
            if a-base+sz_at[a-base]>=TL: break
            a=a+sz_at[a-base]
            if n>cap: break
    for ref,slot in zip(iatref,iatslot):
        if int(ref) in seen: slots.add(int(slot))
    return slots,n
IATNAME={0x7e15f8:'OleLoadFromStream',0x7e15f4:'OleSaveToStream',0x7e15e4:'StgOpenStorage',
         0x7e15c8:'StgCreateDocfile',0x7e15fc:'CoCreateInstance',0x7e1600:'OleRun'}
Q3rows=[]
for a in s3:
    enc=sorted(enclosing(a))
    cand=[]
    for fs in enc:
        slots,n=fn_iats(fs)
        fv=VIEWS['A_containment'].get(fs,{})
        cand.append(dict(func_start=hex(fs),reachable_insns=n,
           ole_slots=[IATNAME.get(x,hex(x)) for x in sorted(slots)],
           has_OleLoadFromStream=(0x7e15f8 in slots),
           n_distinct_iids_in_view_A=len(fv.get('distinct',[])),
           distinct_iids=[hex(x) for x in fv.get('distinct',[])]))
    Q3rows.append(dict(site=hex(a),n_enclosing=len(enc),candidates=cand))
# ---- Q4 controls
Q4={}
Q4['a_d4_46000001']=dict(rule='dword3==0x46000001',count=len(scan(d4=0x46000001)),
  addrs=[hex(x) for x in sorted(scan(d4=0x46000001))])
cb=scan(drop_d2=True)
Q4['b_drop_d2_zero']=dict(rule='drop dword1==0',count=len(cb),baseline=len(iid),
  strictly_greater=len(cb)>len(iid),remark='not strictly greater on this file: no aligned 16-byte window has (d2&0xFFFF)==0x00C0 and d3==0x46000000 with dword1!=0')
cb2=scan(drop_d2=True,d3low=None)
Q4['b2_drop_d2_and_d3']=dict(rule='drop dword1==0 AND drop (dword2&0xFFFF)==0x00C0',
  count=len(cb2),baseline=len(iid),strictly_greater=len(cb2)>len(iid),
  addrs=[hex(x) for x in sorted(cb2)])
cb3=scan(drop_d2=False,d3low=None)
Q4['b3_drop_d3_only']=dict(rule='drop (dword2&0xFFFF)==0x00C0 only',count=len(cb3),
  strictly_greater=len(cb3)>len(iid))
# anti-control 1
for tgt,label in ((0x7f7c94,'card_says_+4'),(0x7f7c84,'true_+4'),(0x7f7c90,'+0x10_of_7c80')):
    r=[base+m.start() for m in re.finditer(re.escape(b'\x68'+tgt.to_bytes(4,'little')),text)]
    s=[a for a in r if a in pushset and pushset[a]==tgt]
    Q4['c_anti_%s_%x'%(label,tgt)]=dict(target=hex(tgt),is_iid_start=(tgt in iidset),
      raw68_hits=len(r),push_imm_sites=len(s),
      imm32_occurrences_anywhere=len([x for x in re.finditer(re.escape(tgt.to_bytes(4,'little')),text)]))
# anti-control 2: fake boundary = site-0x200 over 0x200 bytes
def fake(site,delta=0x200):
    fs=site-delta; vals=set()
    for (aa,sz,m,op) in md.disasm_lite(text[fs-base:fs-base+delta],fs):
        if m=='push' and re.fullmatch(r'0x[0-9a-f]+',op):
            v=int(op,16)
            if v in iidset: vals.add(v)
    return fs,len(vals)
fk=[fake(a) for a in s1]
Q4['d_anti_fake_boundary']=dict(rule='function start := site-0x200; extent := exactly 0x200 bytes',
  funcs=len({f for f,_ in fk}),exactly1=sum(1 for _,n in fk if n==1),
  ge2=sum(1 for _,n in fk if n>=2),zero=sum(1 for _,n in fk if n==0),
  real_A=dist_b3 if False else None)
Q4['d_anti_fake_boundary']['real_view_A_Q1_summary']=dist({k:v for k,v in VIEWS['A_containment'].items() if k in set(enc_max for enc_max in [0])}) if False else None
realq1={fs for a in s1 for fs in [max(enclosing(a))] if enclosing(a)}
Q4['d_anti_fake_boundary']['real_Q1_A_subset']=dict(
  funcs=len(realq1),exactly1=sum(1 for fs in realq1 if len(VIEWS['A_containment'].get(fs,{}).get('distinct',[]))==1),
  ge2=sum(1 for fs in realq1 if len(VIEWS['A_containment'].get(fs,{}).get('distinct',[]))>=2))
# anti-control 3: call-after-push dimension vs OleSaveToStream-in-function
def first_call(site,window=64):
    for k in range(1,window):
        a=site+k; o=a-base
        if o<TL and sz_at[o]>0 and kd_at[o] in (3,4):
            return a,kd_at[o],tg_at[o]
    return None,None,None
rows=[]
for a in s1:
    ca,ck,ct=first_call(a)
    fs=max(enclosing(a)) if enclosing(a) else None
    slots,_=fn_iats(fs) if fs else (set(),0)
    rows.append(dict(site=hex(a),first_call=(hex(ca) if ca else None),
       first_call_kind=('direct' if ck==3 else ('indirect' if ck==4 else None)),
       first_call_iat_slot=(hex(ct) if ck==4 and ct in IATNAME else None),
       first_call_is_OleSaveToStream=(ck==4 and ct==0x7e15f4),
       fn=hex(fs) if fs else None, fn_has_OleSaveToStream=(0x7e15f4 in slots)))
Q4['e_anti_call_vs_save']=dict(n_sites=len(rows),
  sites_with_first_call_directly_OleSaveToStream=sum(1 for r in rows if r['first_call_is_OleSaveToStream']),
  sites_with_OleSaveToStream_somewhere_in_their_function=sum(1 for r in rows if r['fn_has_OleSaveToStream']),
  first_call_kind_hist=dict(collections.Counter(r['first_call_kind'] for r in rows)),
  identical=(sum(1 for r in rows if r['first_call_is_OleSaveToStream'])==
             sum(1 for r in rows if r['fn_has_OleSaveToStream'])),
  per_site=rows)
RES=dict(views={k:dist(v) for k,v in VIEWS.items()},
   views_per_function={k:[dict(func_start=hex(fs),n_sites=len(f['sites']),
      sites=[hex(x) for x in f['sites']],n_distinct=len(f['distinct']),
      distinct=[hex(x) for x in f['distinct']]) for fs,f in sorted(v.items())]
      for k,v in VIEWS.items()},
   q1={},q3=dict(rows=Q3rows,sites=[hex(a) for a in s3],raw_hits=len(raw3)),
   q4=Q4, entries=len(ENTRIES), unresolved=[[hex(a),hex(v)] for a,v in unres],
   iid_census=dict(count=len(iid),addrs=[hex(x) for x in iidaddrs]))
for k,v in VIEWS.items():
    G={max(enclosing(a)) for a in s1}
    RES['q1'][k]=dict(n_functions=len([fs for fs in G if fs in v]),
      table=table(G,v),
      functions=[dict(func_start=hex(fs),site_count=len([1 for a in s1 if max(enclosing(a))==fs]),
         n_distinct=len(v.get(fs,{}).get('distinct',[])),
         distinct=[hex(x) for x in v.get(fs,{}).get('distinct',[])])
         for fs in sorted(G) if fs in v])
json.dump(RES,open(OUT+'x120exec_views.json','w'),indent=1)
for k in VIEWS: print(k,RES['views'][k])
for k in VIEWS:
    t=RES['q1'][k]['table']
    print('Q1',k,'fns',t['group_funcs'],'e1',t['group_exactly1'],'rest',t['rest_funcs'],
          t['rest_exactly1'],'fisher',t['fisher_p'])
print('Q3 rows',len(Q3rows))
for r in Q3rows: print(' ',r['site'],r['n_enclosing'],[ (c['func_start'],c['has_OleLoadFromStream'],c['n_distinct_iids_in_view_A']) for c in r['candidates']])
print('Q4',json.dumps({k:v for k,v in Q4.items() if k!='e_anti_call_vs_save'},indent=1)[:2500])
print('Q4 e',{k:v for k,v in Q4['e_anti_call_vs_save'].items() if k!='per_site'})
print('unresolved',len(unres))
