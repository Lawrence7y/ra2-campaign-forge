# DEFINITIVE: reverse-CFG enclosure on the COMPLETE linear-sweep graph (1.39M insns in .text).
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
NS=len(starts)
# per-offset arrays indexed by (addr-base); -1 = not an insn start
ISZ=_ar.array('b',[-1])*TL  # placeholder; build via dict? use bytearray with 0 = none
sz_at=bytearray(TL); kd_at=bytearray(TL); tg_at=_ar.array('I',[0])*TL
starts_l=[int(x) for x in starts]
for idx in range(NS):
    a=starts_l[idx]; o=a-base
    sz_at[o]=int(sizes[idx]); kd_at[o]=int(kinds[idx])
callmap={int(a):(int(callk[i]),int(callt[i])) for i,a in enumerate(calls)}
for a,(k,t) in callmap.items():
    if k==3: tg_at[a-base]=t
# jmp/jcc targets: recompute from the sweep JSON? we did not store jcc targets. Rebuild from text by
# re-decoding only instructions whose kind==6 or 2 (cheap: 128858 of them).
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
jn=0
for idx in range(NS):
    if kinds[idx] in (2,6):
        a=starts_l[idx]; o=a-base
        ins=None
        for i in md.disasm(text[o:o+16],a): ins=i; break
        if ins and ins.op_str.startswith('0x'):
            tg_at[o]=int(ins.op_str,16); jn+=1
print('insn starts',NS,'jump targets recorded',jn)
ALLCALL=set(int(callt[i]) for i in range(len(calls)) if callk[i]==3)
ENTRIES=sorted({int(t) for t in ALLCALL if base<=t<tend and sz_at[t-base]>0}|{ENTRY})
ENTRIESET=set(ENTRIES)
print('entries',len(ENTRIES))
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
iid=scan(); iidset=set(iid)
IIDP=[(int(a),int(v)) for a,v in zip(pushes,pushv) if v in iidset]
t0=time.time()
assign={}; un=[]
for a,v in IIDP:
    enc=enclosing(a)
    if not enc: un.append((a,v)); continue
    assign.setdefault(max(enc),[]).append((a,v))
print('IID sites',len(IIDP),'unresolved',len(un),'funcs',len(assign),'%.1fs'%(time.time()-t0))
FND={fs:dict(func_start=fs,n_sites=len(I),sites=sorted({a for a,_ in I}),
             distinct=sorted({v for _,v in I})) for fs,I in assign.items()}
def dist(fd):
    return dict(funcs=len(fd),exactly1=sum(1 for f in fd.values() if len(f['distinct'])==1),
      ge2=sum(1 for f in fd.values() if len(f['distinct'])>=2),
      ge3=sum(1 for f in fd.values() if len(f['distinct'])>=3),
      zero=sum(1 for f in fd.values() if len(f['distinct'])==0))
def sites_of(T):
    raw=[base+m.start() for m in re.finditer(re.escape(b'\x68'+T.to_bytes(4,'little')),text)]
    return raw,[a for a in raw if a in pushset and pushset[a]==T and sz_at[a-base]==5]
def report(T):
    raw,ok=sites_of(T); grp=collections.defaultdict(list); amb=[]
    for a in ok:
        enc=enclosing(a)
        rows=dict(site=hex(a),enclosing=[hex(x) for x in sorted(enc)],n=len(enc))
        if len(enc)!=1: amb.append(rows)
        grp[max(enc) if enc else None].append(a)
    return dict(target=hex(T),raw_5byte_hits=len(raw),sites=len(ok),
      site_addrs=[hex(a) for a in ok],rejected=[hex(a) for a in raw if a not in set(ok)],
      n_functions=len(grp),ambiguity=amb,
      functions=[dict(func_start=(hex(fs) if fs else None),site_count=len(v),
        sites=[hex(x) for x in sorted(v)],
        n_distinct=len(FND.get(fs,{}).get('distinct',[])),
        distinct_iids=[hex(x) for x in FND.get(fs,{}).get('distinct',[])]) for fs,v in sorted(grp.items(),key=lambda kv:(kv[0] or 0))])
T1=0x7f7c80; T3=0x7ed358
r1=report(T1); r3=report(T3)
D=dist(FND)
print('T1',r1['sites'],'funcs',r1['n_functions'],'amb',len(r1['ambiguity']))
print('T3',r3['sites'],'funcs',r3['n_functions'],'amb',len(r3['ambiguity']))
print('full dist',D)
json.dump(dict(entries=len(ENTRIES),entry_point=hex(ENTRY),direct_call_targets=len(ALLCALL),
  full_text_distribution=D,
  full_text_functions=[dict(func_start=hex(k),n_sites=len(v['sites']),
     sites=[hex(x) for x in v['sites']],distinct=[hex(x) for x in v['distinct']])
     for k,v in sorted(FND.items())],
  unresolved=[[hex(a),hex(v)] for a,v in un],
  q1=r1,q3=r3,iid_census=dict(count=len(iid),addrs=[hex(a) for a in sorted(iid)],
     section={hex(a):iid[a] for a in sorted(iid)})),
  open(OUT+'x120exec_def.json','w'),indent=1)
