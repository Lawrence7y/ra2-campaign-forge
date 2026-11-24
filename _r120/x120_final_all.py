# ============ R120 FINAL CONSOLIDATED MEASUREMENT ============
# All numbers below are recomputed here from bytes of gamemd.exe; nothing is imported from the repo.
import struct, json, re, array as _ar, collections, bisect, math, time
P='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r120/'
d=open(P,'rb').read()
e=struct.unpack_from('<I',d,0x3c)[0]
assert d[:2]==b'MZ' and d[e:e+4]==b'PE\0\0'
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
CALLT=sorted({int(callt[i]) for i in range(len(calls)) if callk[i]==3})
ENTRIES=sorted({t for t in CALLT if base<=t<tend and sz_at[t-base]>0}|{ENTRY})
ENTRIESET=set(ENTRIES)
B2=[int(starts[i]) for i in range(1,NS) if kinds[i-1] in (1,2)]
B2=[a for a in B2 if sz_at[a-base]>0]
B2SET=set(B2)
# reachability from ENTRY-level tier1 (to detect indirect-only code)
reach=bytearray(TL); work=list(ENTRIES)
for a in ENTRIES: reach[a-base]=1
while work:
    a=work.pop(); o=a-base; kk=kd_at[o]; nxt=[]
    if kk in (2,6,3) and tg_at[o]: nxt.append(tg_at[o])
    if kk not in (1,2,5,7): nxt.append(a+sz_at[o])
    for b in nxt:
        if base<=b<tend:
            ob=b-base
            if sz_at[ob]>0 and not reach[ob]: reach[ob]=1; work.append(b)
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
def nearest_B2(a):
    i=bisect.bisect_right(B2,a)-1
    return B2[i] if i>=0 else None
def next_entry(a):
    i=bisect.bisect_right(ENTRIES,a); return ENTRIES[i] if i<len(ENTRIES) else tend
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
iid=scan(); iidset=set(iid); iidaddrs=sorted(iid)
IIDP=[(int(a),int(v)) for a,v in zip(pushes,pushv) if v in iidset]
# ---- attribution views
def build(mode):
    g=collections.defaultdict(list); unres=[]
    for a,v in IIDP:
        if mode=='A_containment':
            enc=enclosing(a)
            if not enc: unres.append((a,v)); continue
            for fs in enc: g[fs].append((a,v))
        elif mode=='B_innermost':
            enc=enclosing(a)
            if not enc: unres.append((a,v)); continue
            g[max(enc)].append((a,v))
        elif mode=='C_addr_range_to_next_entry':
            g[next_entry(a)].append((a,v))
        elif mode=='D_enclosure_else_nearest_B2':
            enc=enclosing(a)
            if enc: g[max(enc)].append((a,v))
            else:
                nb=nearest_B2(a)
                if nb is None: unres.append((a,v))
                else: g[nb].append((a,v))
        elif mode=='E_nearest_B2_always':
            nb=nearest_B2(a); g[nb].append((a,v))
    return {fs:dict(func_start=fs,n_sites=len(I),sites=sorted({x for x,_ in I}),
            distinct=sorted({v for _,v in I})) for fs,I in g.items()}, unres
VIEWS={}; UNRES={}
for m in ('A_containment','B_innermost','C_addr_range_to_next_entry',
          'D_enclosure_else_nearest_B2','E_nearest_B2_always'):
    try:
        VIEWS[m],UNRES[m]=build(m)
    except Exception as ex:
        print('mode fail',m,ex)
def dist(fd):
    return dict(funcs=len(fd),sites=sum(f['n_sites'] for f in fd.values()),
      exactly1=sum(1 for f in fd.values() if len(f['distinct'])==1),
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
    ch=chi2y(a_,b_,c_,d_)
    return dict(group_funcs=len(G),group_exactly1=a_,group_ge2=b_,
      pct_group=round(100.0*a_/max(len(G),1),2),
      rest_funcs=len(rest),rest_exactly1=c_,rest_ge2=d_,
      pct_rest=round(100.0*c_/max(len(rest),1),2),
      table=[[a_,b_],[c_,d_]],fisher_p=fish(a_,b_,c_,d_),
      chi2_yates=ch,chi2_p=chi2p(ch))
def sites_of(T):
    raw=[base+m.start() for m in re.finditer(re.escape(b'\x68'+T.to_bytes(4,'little')),text)]
    return raw,[a for a in raw if a in pushset and pushset[a]==T and sz_at[a-base]==5]
T1=0x7f7c80; T3=0x7ed358
raw1,s1=sites_of(T1); raw3,s3=sites_of(T3)
GROUPS={}
for m in VIEWS:
    grp=collections.defaultdict(list)
    for a in s1:
        if m=='A_containment':
            enc=enclosing(a)
            if enc: grp[max(enc)].append(a)
        elif m=='B_innermost':
            enc=enclosing(a)
            if enc: grp[max(enc)].append(a)
        elif m=='C_addr_range_to_next_entry':
            grp[next_entry(a)].append(a)
        elif m=='D_enclosure_else_nearest_B2':
            enc=enclosing(a)
            if enc: grp[max(enc)].append(a)
            else:
                nb=nearest_B2(a)
                if nb: grp[nb].append(a)
        elif m=='E_nearest_B2_always':
            nb=nearest_B2(a); grp[nb].append(a)
    GROUPS[m]=grp
# function-level Ole facts via forward walk over the graph (bounded)
def fn_slots(fs,cap=20000):
    seen=set(); work=[fs]; n=0
    while work:
        a=work.pop()
        while True:
            o=a-base
            if o<0 or o>=TL or sz_at[o]==0 or a in seen: break
            seen.add(a); n+=1
            kk=kd_at[o]; t=tg_at[o]
            if kk in (1,5,7): break
            if kk==2:
                if base<=t<tend: work.append(t)
                break
            if kk in (6,3) and base<=t<tend: work.append(t)
            a=a+sz_at[o]
            if n>cap: break
    slots=set()
    for ref,slot in zip(iatref,iatslot):
        if int(ref) in seen: slots.add(int(slot))
    return slots,n
IATNAME={0x7e15f8:'OleLoadFromStream',0x7e15f4:'OleSaveToStream',0x7e15e4:'StgOpenStorage',
         0x7e15c8:'StgCreateDocfile',0x7e15fc:'CoCreateInstance',0x7e1600:'OleRun'}
# ---------- assemble ----------
R={}
R['pe']=dict(file_len=hex(len(d)),e_lfanew=hex(e),ImageBase=hex(IB),SizeOfImage=hex(SOI),
  entry_rva=hex(struct.unpack_from('<I',d,e+24+16)[0]),entry_va=hex(ENTRY),num_sections=nsec,
  sections={k:dict(va=hex(IB+v['va']),vsize=hex(v['vs']),rawptr=hex(v['raw']),rawsize=hex(v['rawsz']),
    file_backed_va_range=hex(IB+v['va'])+'-'+hex(IB+v['va']+min(v['vs'],v['rawsz'])),
    zero_fill_bytes=max(0,v['vs']-v['rawsz'])) for k,v in SEC.items()},
  data_dirs={str(i):[hex(x) for x in DIRS[i]] for i in range(16) if any(DIRS[i])},
  import_dir=dict(rva=hex(DIRS[1][0]),size=hex(DIRS[1][1])),
  ole_iat_slots={hex(k):IATNAME[k] for k in IATNAME})
R['sweep']=dict(mode='capstone CS_MODE_32, disasm_lite, 65536-byte chunks, byte-wise resync on decode gaps, never detail=True, never materialising the instruction list',
  instructions=NS, resync_points=json.load(open(OUT+'x120exec_sweep_meta.json'))['resync'],
  push_imm_instructions=len(pushes), call_instructions=len(calls),
  iat_operand_references=len(iatref))
R['iid_census']=dict(rule='A is a 4-byte-aligned address inside file-backed bytes of .rdata or .data; reading 16 bytes at A: dword[1]==0, (dword[2]&0xFFFF)==0x00C0, dword[3]==0x46000000 (little-endian)',
  count=len(iid),addrs=[hex(a) for a in iidaddrs],
  per_addr={hex(a):dict(section=iid[a],dwords=[hex(x) for x in struct.unpack('<4I',d[(a-IB):(a-IB)+16])],
     push_imm_site_count=sum(1 for x,v in IIDP if v==a)) for a in iidaddrs})
# Q1
Q1=dict(target=hex(T1),raw_5byte_hits=len(raw1),sites=len(s1),
  site_addrs=[hex(a) for a in s1],
  rejected_raw_hits=[hex(a) for a in raw1 if a not in set(s1)],
  push_detection='regex 68+LE32(0x7f7c80) over .text; keep a hit only when its address is an instruction start of the linear sweep, capstone reports mnemonic=push, op_str=0x7f7c80, and insn size==5 (so bytes[1:5] are the imm32 operand)',
  boundary_criteria_tested={
    'B1_first_insn_after_int3_padding':len([a for a in SL if (a-base)>0 and text[a-base-1]==0xCC]),
    'B2_insn_after_ret_or_uncond_jmp':len(B2),
    'B3_direct_rel32_call_target':len(ENTRIES)-1,
    'RD_recursive_descent_call_target':len({int(t) for t,k in zip(ld('rd2_tgt','I'),ld('rd2_kind','B')) if k==3})},
  primary_criterion='A_containment (= B_innermost on this population): reverse-CFG enclosure, walking predecessors of the site over fall-through / jcc-target / jmp-target / call-target edges until an entry (PE entry point or direct E8 call target) is hit. Unique for 60/60 sites.',
  per_view={})
for m in ('A_containment','B_innermost','C_addr_range_to_next_entry','D_enclosure_else_nearest_B2','E_nearest_B2_always'):
    grp=GROUPS[m]; fd=VIEWS[m]
    Q1['per_view'][m]=dict(n_functions=len(grp),
      functions=[dict(func_start=hex(fs),site_count=len(v),sites=[hex(x) for x in sorted(v)],
        n_distinct=len(fd.get(fs,{}).get('distinct',[])),
        distinct_iids=[hex(x) for x in fd.get(fs,{}).get('distinct',[])]) for fs,v in sorted(grp.items())],
      summary=dict(funcs=len(grp),
        exactly1=sum(1 for fs in grp if len(fd.get(fs,{}).get('distinct',[]))==1),
        ge2=sum(1 for fs in grp if len(fd.get(fs,{}).get('distinct',[]))>=2),
        zero=sum(1 for fs in grp if len(fd.get(fs,{}).get('distinct',[]))==0)),
      table_vs_rest=table(set(grp),fd))
# ambiguity table for Q1
amb=[]
for a in s1:
    amb.append(dict(site=hex(a),B1=hex([x for x in SL if x<=a and (x-base)>0 and text[x-base-1]==0xCC][-1]),
      B2=hex(nearest_B2(a)), next_entry=hex(next_entry(a)),
      enclosure=[hex(x) for x in sorted(enclosing(a))]))
Q1['per_site_boundary_candidates']=amb
Q1['boundary_agreement']=dict(
  B1_equals_enclosure=sum(1 for r in amb if r['B1']==r['enclosure'][0]) if all(r['enclosure'] for r in amb) else None,
  B2_equals_enclosure=sum(1 for r in amb if r['B2']==r['enclosure'][0]) if all(r['enclosure'] for r in amb) else None,
  next_entry_equals_enclosure=sum(1 for r in amb if r['next_entry']==r['enclosure'][0]) if all(r['enclosure'] for r in amb) else None,
  n_sites=len(amb))
R['q1']=Q1
# Q2
Q2=dict(population_definition='every function that pushes at least one address A which is in the 11-address IID census',
  per_view={})
for m in VIEWS:
    fd=VIEWS[m]
    d_=dist(fd)
    Q2['per_view'][m]=dict(distribution=d_,
      unresolved_sites=len(UNRES.get(m,[])),
      functions=[dict(func_start=hex(fs),n_sites=f['n_sites'],sites=[hex(x) for x in f['sites']],
        n_distinct=len(f['distinct']),distinct=[hex(x) for x in f['distinct']]) for fs,f in sorted(fd.items())],
      q1_group_table=Q1['per_view'][m]['table_vs_rest'])
R['q2']=Q2
# Q3
conf={}
for a in s3:
    enc=sorted(enclosing(a))
    ca=[]
    for fs in enc:
        slots,n=fn_slots(fs)
        ca.append(dict(func_start=hex(fs),reachable_insns=n,
          ole_slots=[IATNAME.get(x,hex(x)) for x in sorted(slots)],
          has_OleLoadFromStream=(0x7e15f8 in slots),
          has_OleSaveToStream=(0x7e15f4 in slots)))
    nb=nearest_B2(a)
    slots_nb,n_nb=fn_slots(nb)
    conf[hex(a)]=dict(enclosure_starts=[hex(x) for x in enc],enclosure_detail=ca,
      nearest_B2=hex(nb),nearest_B2_ole_slots=[IATNAME.get(x,hex(x)) for x in sorted(slots_nb)],
      nearest_B2_has_OleLoadFromStream=(0x7e15f8 in slots_nb),
      nearest_B2_reachable=reach[nb-base]==1 if 0<=nb-base<TL else None)
Q3=dict(target=hex(T3),target_bytes16=d[(T3-IB):(T3-IB)+16].hex(),
  target_dwords=[hex(x) for x in struct.unpack('<4I',d[(T3-IB):(T3-IB)+16])],
  is_a_census_IID=(T3 in iidset),
  census_failure_reason=None if T3 in iidset else 'dword[1] is 0x11d19841 (not 0), dword[2]&0xFFFF is 0x09b7 (not 0x00C0), dword[3] is 0xd1afdd24 (not 0x46000000): the bytes at 0x7ed358 are not a GUID at all',
  raw_5byte_hits=len(raw3),sites=len(s3),site_addrs=[hex(a) for a in s3],
  rejected=[hex(a) for a in raw3 if a not in set(s3)],
  per_site=conf,
  per_view={})
for m in VIEWS:
    grp=collections.defaultdict(list)
    for a in s3:
        if m in ('A_containment','B_innermost','D_enclosure_else_nearest_B2'):
            enc=enclosing(a)
            if enc: grp[max(enc)].append(a)
            elif m=='D_enclosure_else_nearest_B2':
                nb=nearest_B2(a)
                if nb: grp[nb].append(a)
        elif m=='C_addr_range_to_next_entry': grp[next_entry(a)].append(a)
        elif m=='E_nearest_B2_always': grp[nearest_B2(a)].append(a)
    fd=VIEWS[m]
    Q3['per_view'][m]=dict(n_functions=len(grp),
      functions=[dict(func_start=hex(fs),site_count=len(v),sites=[hex(x) for x in sorted(v)],
        n_distinct=len(fd.get(fs,{}).get('distinct',[])),
        distinct_iids=[hex(x) for x in fd.get(fs,{}).get('distinct',[])]) for fs,v in sorted(grp.items())],
      table_vs_rest=table(set(grp),fd))
R['q3']=Q3
# Q4
Q4={}
ca=scan(d4=0x46000001)
Q4['a_dword3_46000001']=dict(rule='identical to census but dword[3]==0x46000001',
  count=len(ca),addrs=[hex(x) for x in sorted(ca)],expected=0,pass_=(len(ca)==0))
cb=scan(drop_d2=True)
Q4['b_drop_dword1_eq_0']=dict(rule='drop only the dword[1]==0 clause',
  count=len(cb),baseline=len(iid),strictly_greater=len(cb)>len(iid),
  pass_as_specified=(len(cb)>len(iid)),
  explanation='FAILS as specified: on this image every aligned window that already has (dword[2]&0xFFFF)==0x00C0 and dword[3]==0x46000000 also has dword[1]==0, so removing that clause changes nothing (11 -> 11). The clause is therefore non-selective here; it is not what does the filtering.',
  addrs=[hex(x) for x in sorted(cb)])
cb2=scan(drop_d2=True,d3low=None)
Q4['b2_drop_dword1_and_dword2clause']=dict(rule='drop dword[1]==0 AND drop (dword[2]&0xFFFF)==0x00C0',
  count=len(cb2),baseline=len(iid),strictly_greater=len(cb2)>len(iid),addrs=[hex(x) for x in sorted(cb2)],
  explanation='this is the version that does show the criterion filtering: 12 > 11')
cb3=scan(drop_d2=False,d3low=None)
Q4['b3_drop_dword2clause_only']=dict(rule='drop only (dword[2]&0xFFFF)==0x00C0',count=len(cb3),
  baseline=len(iid),strictly_greater=len(cb3)>len(iid))
for tgt,label in ((0x7f7c84,'true_plus4'),(0x7f7c94,'card_claims_plus4'),(0x7f7c90,'plus0x10')):
    r=[base+m.start() for m in re.finditer(re.escape(b'\x68'+tgt.to_bytes(4,'little')),text)]
    s=[a for a in r if a in pushset and pushset[a]==tgt]
    Q4['c_anti_%s_%x'%(label,tgt)]=dict(target=hex(tgt),is_census_iid=(tgt in iidset),
      raw_68_hits=len(r),push_imm_sites=len(s),
      imm32_occurrences_anywhere_in_text=len(re.findall(re.escape(tgt.to_bytes(4,'little')),text)))
def fake(site,delta=0x200):
    fs=site-delta; vals=set()
    for (aa,sz,m,op) in md.disasm_lite(text[fs-base:fs-base+delta],fs):
        if m=='push' and re.fullmatch(r'0x[0-9a-f]+',op):
            v=int(op,16)
            if v in iidset: vals.add(v)
    return fs,len(vals)
fk=[fake(a) for a in s1]
realA=Q1['per_view']['A_containment']['summary']
Q4['d_anti_fake_boundary']=dict(rule='function start := site-0x200, extent := the following 0x200 bytes',
  fake=dict(funcs=len({f for f,_ in fk}),exactly1=sum(1 for _,n in fk if n==1),
    ge2=sum(1 for _,n in fk if n>=2),zero=sum(1 for _,n in fk if n==0)),
  real=realA,
  numbers_differ=(len({f for f,_ in fk})!=realA['funcs'] or
                  sum(1 for _,n in fk if n==1)!=realA['exactly1']))
rows=[]
for a in s1:
    ca=None; ck=None; ct=None
    ob=text[a-base:a-base+64]
    for (aa,sz,m,op) in md.disasm_lite(ob,a):
        if m=='call':
            ca=aa
            ck=3 if text[aa-base]==0xE8 else 4
            ct=tg_at[aa-base] if ck==4 else int(op,16)
            break
    enc=enclosing(a); fs=max(enc) if enc else None
    slots,_=fn_slots(fs) if fs else (set(),0)
    rows.append(dict(site=hex(a),first_call=(hex(ca) if ca else None),
      first_call_kind=('direct' if ck==3 else ('indirect' if ck==4 else None)),
      first_call_iat_slot=(hex(ct) if ck==4 and ct in IATNAME else None),
      first_call_is_OleSaveToStream=(ck==4 and ct==0x7e15f4),
      function=(hex(fs) if fs else None),
      function_has_OleSaveToStream_operand=(0x7e15f4 in slots)))
Q4['e_first_call_vs_OleSaveToStream']=dict(
  n_sites=len(rows),
  count_first_call_is_directly_to_OleSaveToStream_IAT=sum(1 for r in rows if r['first_call_is_OleSaveToStream']),
  count_function_contains_OleSaveToStream_operand=sum(1 for r in rows if r['function_has_OleSaveToStream_operand']),
  first_call_kind_histogram=dict(collections.Counter(r['first_call_kind'] for r in rows)),
  first_call_iat_slot_histogram=dict(collections.Counter(str(r['first_call_iat_slot']) for r in rows)),
  two_counts_agree=(sum(1 for r in rows if r['first_call_is_OleSaveToStream'])==
                    sum(1 for r in rows if r['function_has_OleSaveToStream_operand'])),
  per_site=rows)
R['q4']=Q4
R['entries']=dict(tier1_pe_entry_plus_direct_call_targets=len(ENTRIES),
   tier1_forward_reachable_insns=sum(reach),
   note='only %d of %d decoded instructions are reachable from PE entry + direct call targets; the rest are reachable only through indirect calls / data pointers'%(sum(reach),NS))
R['unresolved']={m:[[hex(a),hex(v)] for a,v in UNRES.get(m,[])] for m in VIEWS}
json.dump(R,open(OUT+'x120exec_final.json','w'),indent=1)
# --- per-question files
json.dump({'pe':R['pe'],'sweep':R['sweep'],'iid_census':R['iid_census'],'q1':R['q1'],
           'entries':R['entries']},open(OUT+'x120exec_q1.json','w'),indent=1)
json.dump({'pe':R['pe'],'iid_census':R['iid_census'],'q2':R['q2'],
           'unresolved':R['unresolved']},open(OUT+'x120exec_q2.json','w'),indent=1)
json.dump({'pe':R['pe'],'q3':R['q3']},open(OUT+'x120exec_q3.json','w'),indent=1)
json.dump({'pe':R['pe'],'q4':R['q4']},open(OUT+'x120exec_q4.json','w'),indent=1)
print('IID census',len(iid))
print('sites 0x7f7c80',len(s1),'sites 0x7ed358',len(s3))
print('=== Q1 per view ===')
for m in Q1['per_view']: print(' ',m,Q1['per_view'][m]['summary'])
print('boundary agreement',Q1['boundary_agreement'])
print('=== Q2 per view ===')
for m in R['q2']['per_view']:
    v=R['q2']['per_view'][m]
    print(' ',m,v['distribution'],'unres',v['unresolved_sites'])
    t=v['q1_group_table']; print('     group',t['group_funcs'],t['group_exactly1'],t['pct_group'],
        '| rest',t['rest_funcs'],t['rest_exactly1'],t['pct_rest'],'| fisher',t['fisher_p'],'chi2p',t['chi2_p'])
print('=== Q3 ===',len(s3),'sites; census IID?',T3 in iidset)
for k,v in conf.items(): print(' ',k,v['enclosure_starts'],v['nearest_B2'],v['nearest_B2_has_OleLoadFromStream'],
   [c['has_OleLoadFromStream'] for c in v['enclosure_detail']])
for m in Q3['per_view']:
    t=Q3['per_view'][m]['table_vs_rest']
    print('  view',m,'fns',Q3['per_view'][m]['n_functions'],'e1',t['group_exactly1'],
       'pct',t['pct_group'],'rest',t['rest_funcs'],t['rest_exactly1'],t['pct_rest'],'fisher',t['fisher_p'])
print('=== Q4 ===')
for k,v in Q4.items():
    if k=='e_first_call_vs_OleSaveToStream':
        print(' ',k,{a:b for a,b in v.items() if a!='per_site'})
    else: print(' ',k,{a:b for a,b in v.items() if a not in ('addrs','per_site')})
