# R120 FINAL: Q1..Q4 all numbers, mechanical, self-written PE parse.
import struct, json, bisect, re, array as _ar, math
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
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
    vs,va,rs,ra=struct.unpack_from('<IIII',d,sec+40*i+8)
    SEC[nm]=dict(va=va,vs=vs,raw=ra,rawsz=rs)
tv=SEC['.text']; text=d[tv['raw']:tv['raw']+tv['vs']]; base=IB+tv['va']; tend=base+len(text)
def ld(nm,ty):
    a=_ar.array(ty); a.frombytes(open(OUT+nm+'.bin','rb').read()); return a
starts=ld('a2_starts','I'); kinds=ld('a2_kinds','B'); sizes=ld('a2_sizes','B')
pushes=ld('a2_pushes','I'); pushv=ld('a2_pushv','I')
calls=ld('a2_calls','I'); callk=ld('a2_callk','B'); callt=ld('a2_callt','I')
sweepmeta=json.load(open(OUT+'x120exec_sweep_meta.json'))
pushset={a:v for a,v in zip(pushes,pushv)}
startset=set(starts); ns=len(starts)
def startidx(a):
    i=bisect.bisect_left(starts,a); return i if i<ns and starts[i]==a else None
# call index lookups
callpos={a:i for i,a in enumerate(calls)}
IAT_LOAD=0x7e15f8; IAT_SAVE=0x7e15f4
IATNAME={0x7e15f8:'OleLoadFromStream',0x7e15f4:'OleSaveToStream',0x7e15e4:'StgOpenStorage',
         0x7e15c8:'StgCreateDocfile',0x7e15fc:'CoCreateInstance',0x7e1600:'OleRun'}
# --- imports (self-parsed) for the IAT slot -> name map
imp_rva,imp_sz=DIRS[1]
def rva2off(rva):
    for nm,s in SEC.items():
        if s['va']<=rva<s['va']+min(s['vs'],s['rawsz']): return s['raw']+(rva-s['va'])
    return None
impname={}
o=rva2off(imp_rva); i=0
while True:
    ilt,ts,fc,nr,iat=struct.unpack_from('<IIIII',d,o+20*i)
    if nr==0 and iat==0: break
    dll=d[rva2off(nr):rva2off(nr)+32].split(b'\0')[0].decode('latin1')
    j=0
    while True:
        v=struct.unpack_from('<I',d,rva2off(iat)+4*j)[0]
        if v==0: break
        nm=None
        if not (v&0x80000000): nm=d[rva2off(v)+2:rva2off(v)+66].split(b'\0')[0].decode('latin1')
        impname[IB+iat+4*j]=(dll,nm)
        j+=1
    i+=1
md=Cs(CS_ARCH_X86,CS_MODE_32)
# ---------- boundary criteria ----------
B1=[a for a in starts if (a-base)>0 and text[a-base-1]==0xCC]
B2=sorted({int(starts[i]) for i in range(1,ns) if kinds[i-1] in (1,2)})
B3=sorted({int(callt[i]) for i in range(len(calls)) if callk[i]==3
           and base<=int(callt[i])<tend and int(callt[i]) in startset})
rd_addr=ld('rd2_addr','I'); rd_tgt=ld('rd2_tgt','I'); rd_kind=ld('rd2_kind','B')
RDB=sorted({int(t) for t,k in zip(rd_tgt,rd_kind) if k==3 and base<=int(t)<tend and int(t) in startset})
CRIT=[('B1_after_int3_padding',B1),('B2_after_ret_or_uncond_jmp',B2),
      ('B3_direct_call_target',B3),('RD_direct_call_target',RDB)]
def nearest(arr,a):
    i=bisect.bisect_right(arr,a)-1
    return arr[i] if i>=0 else None
def nextb(arr,fs):
    i=bisect.bisect_right(arr,fs)
    return arr[i] if i<len(arr) else tend
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
iid=scan(); iid_addrs=sorted(iid)
# ---------- per-function IID extraction ----------
def funcs_for(arr,items):
    g={}
    for a,v in items:
        fs=nearest(arr,a)
        g.setdefault(fs,[]).append((a,v))
    out=[]
    for fs,I in sorted(g.items()):
        fe=nextb(arr,fs)
        i=startidx(fs); j=bisect.bisect_left(starts,fe)
        if i is None: i=bisect.bisect_left(starts,fs)
        vals=[pushset[int(starts[k])] for k in range(i,j) if int(starts[k]) in pushset]
        dv=sorted({v for v in vals if v in iid})
        out.append(dict(func_start=fs,func_end=fe,site_count=len(I),
            sites=sorted({a for a,_ in I}),distinct=dv,n_distinct=len(dv)))
    return out
IIDP=[(a,v) for a,v in zip(pushes,pushv) if v in iid]
def summarize(fl):
    return dict(funcs=len(fl),exactly1=sum(1 for f in fl if f['n_distinct']==1),
        ge2=sum(1 for f in fl if f['n_distinct']>=2),
        ge3=sum(1 for f in fl if f['n_distinct']>=3),
        zero=sum(1 for f in fl if f['n_distinct']==0))
FUNCS={c:funcs_for(arr,IIDP) for c,arr in CRIT}
DIST={c:summarize(FUNCS[c]) for c,_ in CRIT}

HEAD=dict(target=P,file_len=hex(len(d)),e_lfanew=hex(e),ImageBase=hex(IB),
  SizeOfImage=hex(SOI),entry_va=hex(ENTRY),
  sections={k:dict(va=hex(IB+v['va']),vsize=hex(v['vs']),raw=hex(v['raw']),rawsize=hex(v['rawsz']),
     file_backed_va=hex(IB+v['va'])+'..'+hex(IB+v['va']+min(v['vs'],v['rawsz'])),
     bss_bytes=max(0,v['vs']-v['rawsz'])) for k,v in SEC.items()},
  data_dirs={'import':[hex(x) for x in DIRS[1]],'resource':[hex(x) for x in DIRS[2]],
             'reloc':[hex(x) for x in DIRS[5]]},
  sweep=dict(mode='capstone CS_MODE_32 disasm_lite, 64KB chunks, detail=False, no whole-listing retention',
     insn_decoded=sweepmeta['n_insn'],resync_points=sweepmeta['resync'],
     push_imm_insns=sweepmeta['n_push_imm'],call_insns=sweepmeta['n_calls']),
  rd=json.load(open(OUT+'rd2_meta.json')),
  imports_of_interest={hex(k):v for k,v in impname.items()
     if v[1] in ('OleLoadFromStream','OleSaveToStream','StgOpenStorage','StgCreateDocfile',
                 'CoCreateInstance','OleRun','CLSIDFromString','StringFromGUID2')})
R={'header':HEAD}
R['iid_census']=dict(rule='4-byte-aligned A in .rdata/.data (file-backed bytes only) with dword[1]==0, (dword[2]&0xFFFF)==0x00C0, dword[3]==0x46000000',
   count=len(iid),addrs=[hex(a) for a in iid_addrs],
   section={hex(a):iid[a] for a in iid_addrs},
   dwords={hex(a):[hex(x) for x in struct.unpack('<4I',d[rva2off(a-IB):rva2off(a-IB)+16])] for a in iid_addrs})
# ---------- Q1 ----------
T1=0x7f7c80
raw1=[base+m.start() for m in re.finditer(re.escape(b'\x68'+T1.to_bytes(4,'little')),text)]
sites1=[a for a in raw1 if a in pushset and pushset[a]==T1 and sizes[startidx(a)]==5]
Q1=dict(target=hex(T1),raw_5byte_hits=len(raw1),sites=len(sites1),
  site_addrs=[hex(a) for a in sites1],rejected=[hex(a) for a in raw1 if a not in sites1],
  method='bytes 68+LE32(0x7f7c80) in .text; accept only if addr is a decoded instruction start from the chunked linear sweep, the decoded mnemonic is push, op_str==0x7f7c80, instruction size==5, i.e. bytes[1:5] IS the imm32 operand',
  criterion_note='each criterion is used both for start assignment and for extent (end=next boundary under the SAME criterion), so a site always lies inside its own function by construction',
  per_criterion=[])
fisher_cache={}
def fisher(a,b,c,d):
    lf=math.lgamma
    n=a+b+c+d
    def lp(x):
        bb=a+b-x; cc=a+c-x; dd=d-(a+c-x)
        if bb<0 or cc<0 or dd<0: return None
        return (lf(a+b+1)+lf(c+d+1)+lf(a+c+1)+lf(b+d+1)-lf(n+1)-lf(x+1)-lf(a+b-x+1)
                -lf(a+c-x+1)-lf(n-a-c+x+1))
    base_lp=lp(a)
    p=0.0
    for x in range(0,min(a+b,a+c)+1):
        v=lp(x)
        if v is None: continue
        if v<=base_lp+1e-12: p+=math.exp(v)
    return min(1.0,p)
def chi2y(a,b,c,d):
    n=a+b+c+d
    num=(abs(a*d-b*c)-n/2.0)**2*n; den=(a+b)*(c+d)*(a+c)*(b+d)
    return (num/den) if den else float('nan')
def chi2p(x): return math.erfc(math.sqrt(max(x,0.0)/2.0))
for cname,arr in CRIT:
    fl=funcs_for(arr,[(a,pushset[a]) for a in sites1])
    Q1['per_criterion'].append(dict(criterion=cname,candidates=len(arr),
      n_functions=len(fl),summary=summarize(fl),
      functions=[dict(func_start=hex(f['func_start']),func_end=hex(f['func_end']),
        site_count=f['site_count'],sites=[hex(x) for x in f['sites']],
        distinct_iids=[hex(x) for x in f['distinct']],n_distinct=f['n_distinct']) for f in fl]))
# ambiguity listing
amb=[]
for a in sites1:
    cands={c:(hex(nearest(arr,a)) if nearest(arr,a) is not None else None) for c,arr in CRIT}
    amb.append(dict(site=hex(a),candidates=cands))
Q1['per_site_candidates']=amb
Q1['distinct_candidate_vectors']=sorted({json.dumps(x['candidates'],sort_keys=True) for x in amb})
Q1['distinct_candidate_vectors']=[json.loads(v) for v in Q1['distinct_candidate_vectors']]
R['q1']=Q1
print('Q1 sites',len(sites1))
for p in Q1['per_criterion']: print('  ',p['criterion'],'cands',p['candidates'],'fns',p['n_functions'],p['summary'])
print('  candidate vectors:',len(Q1['distinct_candidate_vectors']))
json.dump(R,open(OUT+'x120exec_q1.json','w'),indent=1)
json.dump(dict(DIST=DIST),open(OUT+'_tmp_dist.json','w'),indent=1)
