# Q1/Q2/Q3/Q4 core measurements. Pure self-written PE parse + capstone lite sweep reuse.
import struct, json, bisect, re, math
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
def va2off(va):
    rva=va-IB
    for nm,s in S.items():
        if s['va']<=rva<s['va']+s['vs']:
            o=s['raw']+(rva-s['va'])
            if o< s['raw']+s['rawsz']: return o
    return None
tv=S['.text']; text=d[tv['raw']:tv['raw']+tv['vs']]; base=IB+tv['va']
starts=array=None
import array as _ar
starts=_ar.array('I'); starts.frombytes(open(OUT+'x120_starts.bin','rb').read())
kinds=_ar.array('B'); kinds.frombytes(open(OUT+'x120_kinds.bin','rb').read())
A=json.load(open(OUT+'x120_stageA.json'))
pushes=[(a,v) for a,v in A['pushes']]; calls=[(a,k,o) for a,k,o in A['calls']]
pushset={a:v for a,v in pushes}
calladdrs=[c[0] for c in calls]
startset=starts  # array, sorted ascending by construction
def is_start(a):
    i=bisect.bisect_left(starts,a)
    return i<len(starts) and starts[i]==a
res={}
res['pe']=dict(IB=IB,text=dict(va=tv['va'],vs=tv['vs'],raw=tv['raw'],rawsz=tv['rawsz']),
               sections={k:dict(v) for k,v in S.items()},
               insn_count=len(starts), resync=A['resync'], push_imm_count=len(pushes), call_count=len(calls))

# ---------- IID definition scans ----------
def guid_ok(b, drop_d2=False, d4=0x46000000):
    d1,d2,d3,d4_=struct.unpack('<4I',b)
    if d4_!=d4: return False
    if not drop_d2 and d2!=0: return False
    if (d3 & 0xFFFF)!=0x00C0: return False
    return True
def scan_iids(drop_d2=False,d4=0x46000000):
    hits={}
    for nm in ('.rdata','.data'):
        s=S[nm]; blob=d[s['raw']:s['raw']+s['vs']]
        for off in range(0,len(blob)-16,4):
            b=blob[off:off+16]
            if guid_ok(b,drop_d2,d4):
                hits[IB+s['va']+off]=(nm,off)
    return hits
iid=scan_iids()
res['iid_full_image']=dict(count=len(iid),addrs=[hex(a) for a in sorted(iid)],
   detail={hex(a):dict(section=iid[a][0]) for a in sorted(iid)})
# control a: d4=0x46000001
ca=scan_iids(d4=0x46000001); res['ctrl_a_d4_46000001']=dict(count=len(ca),addrs=[hex(x) for x in sorted(ca)])
# control b: drop d2==0
cb=scan_iids(drop_d2=True); res['ctrl_b_drop_d2']=dict(count=len(cb),addrs=[hex(x) for x in sorted(cb)])

# ---------- function boundary criteria ----------
padcand=[a for i,a in enumerate(starts)
         if (a-base)>0 and text[a-base-1]==0xCC and text[a-base]!=0xCC]
padcand.sort()
res['pad_candidates']=dict(count=len(padcand))
def bound_M1(addr):
    # nearest candidate start <= addr  (criterion: first insn after >=1 byte 0xCC padding)
    i=bisect.bisect_right(padcand,addr)-1
    if i<0: return base
    return padcand[i]
def bound_M2(addr):
    # nearest preceding terminator (ret / uncond jmp) then the next insn start
    i=bisect.bisect_left(starts,addr)
    j=i-1
    while j>=0 and kinds[j] not in (1,2): j-=1
    if j<0: return base
    return starts[j+1] if j+1<len(starts) else base
def extent_M1(fs):
    i=bisect.bisect_right(padcand,fs)
    return padcand[i] if i<len(padcand) else base+len(text)
def insns_in(fs,fe):
    i=bisect.bisect_left(starts,fs); j=bisect.bisect_left(starts,fe)
    return i,j

# ---------- Q1 sites ----------
TARGET=0x7f7c80
raw_hits=[m.start() for m in re.finditer(re.escape(b'\x68'+TARGET.to_bytes(4,'little')),text)]
raw_hits=[base+h for h in raw_hits]
sites=[a for a in raw_hits if a in pushset and pushset[a]==TARGET]
rejected=[a for a in raw_hits if a not in sites]
res['q1_sites']=dict(target=hex(TARGET),raw_opcode68_hits=len(raw_hits),
    valid_push_imm_sites=len(sites),sites=[hex(a) for a in sites],
    rejected_not_insn_start_or_diff_imm=[hex(a) for a in rejected],
    validation_method='imm32 bytes of 0x7f7c80 must appear as the direct operand of a 0x68 push, decoded by a chunked capstone linear sweep of .text; site address must equal a decoded instruction start, and capstone must report push with that exact immediate')
# per site: M1 and M2 boundaries
per_site=[]
for a in sites:
    per_site.append(dict(site=hex(a),M1=hex(bound_M1(a)),M2=hex(bound_M2(a))))
res['q1_per_site_boundary']=per_site
ambig=[p for p in per_site if p['M1']!=p['M2']]
res['q1_boundary_ambiguity']=dict(n_sites=len(per_site),n_disagree=len(ambig),examples=ambig[:20])

def group_by(fn_start_fn):
    g={}
    for a in sites:
        fs=fn_start_fn(a); g.setdefault(fs,[]).append(a)
    out={}
    for fs,ss in g.items():
        fe=extent_M1(fs)
        i,j=insns_in(fs,fe)
        iidpush=[]
        for k in range(i,j):
            v=pushset.get(starts[k])
            if v is not None and v in iid: iidpush.append(v)
        out[fs]=dict(sites=sorted(ss),sites_hex=[hex(x) for x in sorted(ss)],site_count=len(ss),
                     distinct_iids=[hex(x) for x in sorted(set(iidpush))],n_distinct=len(set(iidpush)))
    return out
g_M1=group_by(bound_M1); g_M2=group_by(bound_M2)
def summ(g):
    one=sum(1 for v in g.values() if v['n_distinct']==1)
    two=sum(1 for v in g.values() if v['n_distinct']>=2)
    return dict(funcs=len(g),exactly1=one,ge2=two,zero=sum(1 for v in g.values() if v['n_distinct']==0))
res['q1_functions_M1']=dict(funcs={hex(k):v for k,v in sorted(g_M1.items())},summary=summ(g_M1),
    criterion='M1: nearest prior instruction start p with text[p-1]==0xCC and text[p]!=0xCC (first insn after int3 padding); function extent = (p, next pad-candidate)')
res['q1_functions_M2']=dict(funcs={hex(k):v for k,v in sorted(g_M2.items())},summary=summ(g_M2),
    criterion='M2: nearest prior ret/uncond-jmp instruction; function start = next instruction start after it; extent = same M1 extent of that start')
json.dump(res,open(OUT+'x120exec_q1.json','w'),indent=1)
print('IID count',len(iid),'ctrlA',len(ca),'ctrlB',len(cb))
print('raw68',len(raw_hits),'sites',len(sites),'rejected',rejected)
print('M1 sum',summ(g_M1)); print('M2 sum',summ(g_M2))
print('ambiguity',len(ambig))
for f,v in sorted(g_M1.items()): print('  %08x n=%d sites=%d iids=%s'%(f,v['site_count'],v['n_distinct'],v['distinct_iids']))
