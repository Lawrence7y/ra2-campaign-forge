# Fix Fisher (exact via math.comb) + register-tracking control e + card-arithmetic note.
import struct, json, bisect, re, array as _ar, math
P='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r120/'
d=open(P,'rb').read()
e=struct.unpack_from('<I',d,0x3c)[0]
nsec=struct.unpack_from('<H',d,e+6)[0]; optsz=struct.unpack_from('<H',d,e+20)[0]
IB=struct.unpack_from('<I',d,e+24+28)[0]
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
pushset={a:v for a,v in zip(pushes,pushv)}; startset=set(starts); ns=len(starts)
def sidx(a):
    i=bisect.bisect_left(starts,a); return i if i<ns and starts[i]==a else None
B3=sorted({int(callt[i]) for i in range(len(calls)) if callk[i]==3 and base<=int(callt[i])<tend and int(callt[i]) in startset})
rd_tgt=ld('rd2_tgt','I'); rd_kind=ld('rd2_kind','B')
RDB=sorted({int(t) for t,k in zip(rd_tgt,rd_kind) if k==3 and base<=int(t)<tend and int(t) in startset})
def nearest(arr,a):
    i=bisect.bisect_right(arr,a)-1; return arr[i] if i>=0 else None
def nextb(arr,fs):
    i=bisect.bisect_right(arr,fs); return arr[i] if i<len(arr) else tend
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
def fisher_exact(a,b,c,d):
    n=a+b+c+d
    def p_of(x):
        bb=(a+b)-x; cc=(a+c)-x
        dd=n-x-bb-cc
        if bb<0 or cc<0 or dd<0: return 0.0
        return (math.comb(a+b,x)*math.comb(c+d,a+c-x))/math.comb(n,a+c)
    p0=p_of(a); tot=0.0
    for x in range(0,min(a+b,a+c)+1):
        p=p_of(x)
        if p<=p0*(1+1e-9): tot+=p
    return min(1.0,tot)
def chi2y(a,b,c,d):
    n=a+b+c+d; num=(abs(a*d-b*c)-n/2.0)**2*n; den=(a+b)*(c+d)*(a+c)*(b+d)
    return (num/den) if den else float('nan')
def chi2p(x):
    if x!=x: return float('nan')
    return math.erfc(math.sqrt(max(x,0.0)/2.0))

T1=0x7f7c80; T3=0x7ed358
raw1=[base+m.start() for m in re.finditer(re.escape(b'\x68'+T1.to_bytes(4,'little')),text)]
sites1=[a for a in raw1 if a in pushset and pushset[a]==T1 and sizes[sidx(a)]==5]
IIDP=[(a,v) for a,v in zip(pushes,pushv) if v in iid]
IAT_SAVE=0x7e15f4; IAT_LOAD=0x7e15f8
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)

def reg_state_before(fs,site):
    """track reg <- [IAT slot] loads in a linear pass over [fs,site)"""
    st={}
    ob=text[fs-base:site-base]
    for (a,sz,m,op) in md.disasm_lite(ob,fs):
        if m=='mov':
            try:
                dst,src=[x.strip() for x in op.split(',',1)]
            except ValueError: continue
            st[dst]=None
            mm=re.fullmatch(r'dword ptr \[(0x[0-9a-f]+)\]',src)
            if mm: st[dst]=int(mm.group(1),16)
    return st
def call_after(site,window=48):
    for k in range(1,window):
        a=site+k
        if a in set(calls): 
            i=bisect.bisect_left(calls,a)
            return a,callk[i],callt[i],None
    return None,None,None,None
calls_by_addr={int(a):(int(callk[i]),int(callt[i])) for i,a in enumerate(calls)}
def first_call(site,window=48):
    for k in range(1,window):
        if site+k in calls_by_addr:
            return site+k,calls_by_addr[site+k]
    return None,None
def first_call_op(site,window=48):
    ob=text[site-base:site-base+window]
    for (a,sz,m,op) in md.disasm_lite(ob,site):
        if m=='call': return a,op
    return None,None

rowsE=[]
for a in sites1:
    for cname,arr in (('B3_direct_call_target',B3),('RD_direct_call_target',RDB)):
        fs=nearest(arr,a); fe=nextb(arr,fs)
        st=reg_state_before(fs,a)
        ca,cop=first_call_op(a)
        opreg=cop.strip() if cop else None
        holds = st.get(opreg) if opreg in st else None
        ob=text[fs-base:min(fe,tend)-base]
        has_save=any('0x%x'%IAT_SAVE in op for (aa,sz,m,op) in md.disasm_lite(ob,fs))
        rowsE.append(dict(criterion=cname,site=hex(a),func_start=hex(fs),
            first_call=(hex(ca) if ca else None),first_call_op=cop,
            first_call_reg_holds_IAT=(hex(holds) if holds else None),
            first_call_is_OleSaveToStream=(holds==IAT_SAVE),
            func_has_OleSaveToStream_operand=has_save))
RES={'fisher_helper_note':'exact two-sided Fisher via math.comb hypergeometric enumeration',
     'q2_fisher':{},'q3_fisher':{},'ctrl_e':{}}
for cname,arr in (('B1',None),('B3_direct_call_target',B3),('RD_direct_call_target',RDB)):
    if arr is None: continue
    fl=funcs_for(arr,IIDP); fdict={f['fs']:f for f in fl}
    G=sorted({nearest(arr,a) for a in sites1})
    g1=sum(1 for fs in G if fs in fdict and len(fdict[fs]['distinct'])==1); g2=len(G)-g1
    ex=[f for f in fl if f['fs'] not in G]
    e1=sum(1 for f in ex if len(f['distinct'])==1); er=len(ex)-e1
    RES['q2_fisher'][cname]=dict(table=[[g1,g2],[e1,er]],a=g1,b=g2,c=e1,d=er,
        fisher_p=fisher_exact(g1,g2,e1,er),chi2_yates=chi2y(g1,g2,e1,er),
        chi2_p=chi2p(chi2y(g1,g2,e1,er)),group_funcs=len(G),rest_funcs=len(ex))
ra3=[base+m.start() for m in re.finditer(re.escape(b'\x68'+T3.to_bytes(4,'little')),text)]
sites3=[a for a in ra3 if a in pushset and pushset[a]==T3 and sizes[sidx(a)]==5]
for cname,arr in (('B3_direct_call_target',B3),('RD_direct_call_target',RDB)):
    fl=funcs_for(arr,IIDP); fdict={f['fs']:f for f in fl}
    G=sorted({nearest(arr,a) for a in sites3})
    g1=sum(1 for fs in G if fs in fdict and len(fdict[fs]['distinct'])==1); g2=len(G)-g1
    ex=[f for f in fl if f['fs'] not in G]
    e1=sum(1 for f in ex if len(f['distinct'])==1); er=len(ex)-e1
    RES['q3_fisher'][cname]=dict(table=[[g1,g2],[e1,er]],fisher_p=fisher_exact(g1,g2,e1,er),
        chi2_yates=chi2y(g1,g2,e1,er),chi2_p=chi2p(chi2y(g1,g2,e1,er)),
        group_funcs=len(G),group_exactly1=g1,rest_funcs=len(ex),rest_exactly1=e1,
        pct_group=round(100.0*g1/max(len(G),1),2),pct_rest=round(100.0*e1/max(len(ex),1),2))
by={}
for r in rowsE: by.setdefault(r['criterion'],[]).append(r)
for c,v in by.items():
    RES['ctrl_e'][c]=dict(n_sites=len(v),
        sites_first_call_is_OleSaveToStream_via_tracked_reg=sum(1 for r in v if r['first_call_is_OleSaveToStream']),
        sites_func_has_OleSaveToStream_operand=sum(1 for r in v if r['func_has_OleSaveToStream_operand']),
        first_call_opcode_histogram={},
        examples=[dict(site=r['site'],first_call=r['first_call'],first_call_op=r['first_call_op'],
                       reg_holds=r['first_call_reg_holds_IAT']) for r in v[:6]],
        per_site=v)
    for r in v:
        op=r['first_call_op'] or 'none'
        RES['ctrl_e'][c]['first_call_opcode_histogram'][op]=RES['ctrl_e'][c]['first_call_opcode_histogram'].get(op,0)+1
# card arithmetic check
RES['card_arithmetic_note']=dict(card_says='0x7f7c80 +4 == 0x7f7c94',
   actual={'0x7f7c80+4':'0x7f7c84','0x7f7c80+0x14':'0x7f7c94'},
   measured_for_both={})
for tgt in (0x7f7c84,0x7f7c94,0x7f7c90):
    r=[base+m.start() for m in re.finditer(re.escape(b'\x68'+tgt.to_bytes(4,'little')),text)]
    s=[a for a in r if a in pushset and pushset[a]==tgt]
    RES['card_arithmetic_note']['measured_for_both'][hex(tgt)]=dict(
        is_iid_start=(tgt in iid),raw68_hits=len(r),push_imm_sites=len(s))
# fake boundary control recompute with clean numbers
fake=[]
for a in sites1:
    fs=a-0x200
    vals=[]
    for (aa,sz,m,op) in md.disasm_lite(text[fs-base:fs-base+0x200],fs):
        if m=='push' and re.fullmatch(r'0x[0-9a-f]+',op):
            v=int(op,16)
            if v in iid: vals.append(v)
    fake.append(dict(func_start=hex(fs),n_distinct=len(set(vals))))
realB3=funcs_for(B3,[(a,pushset[a]) for a in sites1])
RES['ctrl_d']=dict(real_B3=dict(funcs=len(realB3),
    exactly1=sum(1 for f in realB3 if len(f['distinct'])==1),
    ge2=sum(1 for f in realB3 if len(f['distinct'])>=2)),
  fake_0x200=dict(funcs=len({f['func_start'] for f in fake}),
    exactly1=sum(1 for f in fake if f['n_distinct']==1),
    ge2=sum(1 for f in fake if f['n_distinct']>=2),
    zero=sum(1 for f in fake if f['n_distinct']==0)),
  differ=('yes' if (len(realB3),sum(1 for f in realB3 if len(f['distinct'])==1))
          !=(len({f['func_start'] for f in fake}),sum(1 for f in fake if f['n_distinct']==1)) else 'NO'))
json.dump(RES,open(OUT+'x120exec_fix.json','w'),indent=1)
print(json.dumps({k:v for k,v in RES.items() if k not in ('ctrl_e',)},indent=1)[:3000])
for c,v in RES['ctrl_e'].items():
    print(c,{k:vv for k,vv in v.items() if k not in ('per_site','examples')})
