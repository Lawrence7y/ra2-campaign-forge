# -*- coding: utf-8 -*-
"""S13-K8RECHK step5b: detection-power counter-evidence + 5-precedent ㉓ check (corrected).
Read-only on exe. Writes only under S13_K8RECHK\work."""
import sys, struct, json, bisect, re, random, collections
import pefile, capstone
sys.stdout.reconfigure(encoding='utf-8')
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
DATA=open(EXE,'rb').read(); pe=pefile.PE(EXE,fast_load=True); IMG=pe.OPTIONAL_HEADER.ImageBase
SECS=[]
for s in pe.sections:
    nm=s.Name.rstrip(b'\x00').decode('latin1')
    SECS.append(dict(name=nm,va=IMG+s.VirtualAddress,raw=s.PointerToRawData,rs=s.SizeOfRawData,
        end=IMG+s.VirtualAddress+s.Misc_VirtualSize))
def sec_of(va):
    for s in SECS:
        if s['va']<=va<s['end']: return s
    return None
def va2fo(va):
    s=sec_of(va); return None if s is None else s['raw']+(va-s['va'])
def u32va(va):
    fo=va2fo(va)
    if fo is None or fo+4>len(DATA): return None
    return struct.unpack('<I',DATA[fo:fo+4])[0]
def cstr(va,maxn=160):
    s=sec_of(va)
    if s is None: return ''
    b=DATA[s['raw']+(va-s['va']):s['raw']+(va-s['va'])+maxn]
    z=b.find(b'\x00'); return (b[:z] if z>=0 else b).decode('latin1','replace')
def rdva(va,n):
    s=sec_of(va); return b'' if s is None else DATA[s['raw']+(va-s['va']):s['raw']+(va-s['va'])+n]
TEXT=[s for s in SECS if s['name']=='.text'][0]; TA=TEXT['va']; TE=TA+TEXT['rs']
TB=DATA[TEXT['raw']:TEXT['raw']+TEXT['rs']]
MD=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); MD.detail=True; MD.skipdata=True
INSNS=list(MD.disasm(TB,TA))
OPDEL=0x7C8B3D; ATEXIT=0x7C978A

# ---- ③' dtor-shape detector ----
def dtor_shape(va,maxbytes=96):
    ins=list(MD.disasm(rdva(va,maxbytes),va))
    has_opdel=False; has_test1=False; ret4=False; test_at=None; opdel_at=None
    for x in ins:
        if x.mnemonic=='call' and x.op_str.startswith('0x') and int(x.op_str,16)==OPDEL:
            has_opdel=True; opdel_at=x.address
        if x.mnemonic=='test' and 'esp + 8' in x.op_str and x.op_str.rstrip().endswith(', 1'):
            has_test1=True; test_at=x.address
        if x.mnemonic=='ret' and x.op_str.strip()=='4': ret4=True
    tbd=bool(has_test1 and has_opdel and test_at and opdel_at and test_at<opdel_at)
    return dict(test1=has_test1,opdel=has_opdel,ret4=ret4,test_before_del=tbd,
                hit=tbd and ret4,nins=len(ins))

# ---- vtable enumeration (TD may be .data or .rdata) ----
VTBASES={}
for sec in SECS:
    if sec['name'] not in ('.rdata','.data'): continue
    n=sec['rs']//4
    for i in range(1,n):
        v=sec['va']+i*4
        col=u32va(v-4)
        if col is None or sec_of(col) is None: continue
        td=u32va(col+0xC)
        if td is None or sec_of(td) is None: continue
        nm=cstr(td+8,80)
        if nm.startswith('.?A'):
            VTBASES[v]=(col,td,nm)
print('vtable bases found',len(VTBASES))
ENTRY_VTS={}
for v,(col,td,nm) in VTBASES.items():
    for k in range(0,260):
        sv=u32va(v+k*4)
        if sv is None or not (TA<=sv<TE): break
        ENTRY_VTS.setdefault(sv,[]).append((v,k,nm))

# ---- liveness ----
CTORS=set(); x=0x812004
for _ in range(3944):
    y=u32va(x)
    if y and TA<=y<TE: CTORS.add(y)
    x+=4
atexit_reg={}
for k,ins in enumerate(INSNS):
    if ins.mnemonic=='call' and ins.op_str.startswith('0x'):
        try: t=int(ins.op_str,16)
        except: continue
        if t==ATEXIT:
            for j in range(max(0,k-14),k):
                p=INSNS[j]
                if p.mnemonic=='push':
                    try: pv=int(p.op_str,16)
                    except: continue
                    if TA<=pv<TE:
                        atexit_reg.setdefault(pv,[]).append((hex(p.address),hex(ins.address)))
                        break
ATEXIT_DTOR=set(atexit_reg)
FS=set(CTORS)|set(ATEXIT_DTOR)
for ins in INSNS:
    if ins.mnemonic in ('call','push') and ins.op_str.startswith('0x'):
        try: t=int(ins.op_str,16)
        except: continue
        if TA<=t<TE: FS.add(t)
for va in range(TA,TE,16):
    b=rdva(va,1)
    if b and b[0] in (0x55,0x53,0x56,0x57,0x6a,0x68,0x81,0x83,0xa1,0xa3,0x8b): FS.add(va)
FS=sorted(FS)
def func_of(w):
    k=bisect.bisect_right(FS,w)-1
    return FS[k] if k>=0 else None
MEMRE=re.compile(r'\[([^\]]+)\]')
VTWRITES={}
for ins in INSNS:
    if ins.mnemonic!='mov' or 'ptr [' not in ins.op_str or ',' not in ins.op_str: continue
    imm=ins.op_str.rsplit(',',1)[1].strip()
    if not imm.startswith('0x'): continue
    try: iv=int(imm,16)
    except: continue
    m=MEMRE.search(ins.op_str); mem=m.group(1) if m else '?'
    f=func_of(ins.address)
    cls='CTOR' if f in CTORS else ('ATEXIT_DTOR' if f in ATEXIT_DTOR else 'OTHER')
    is_global=mem.startswith('0x')
    VTWRITES.setdefault(iv,[]).append(dict(site=hex(ins.address),mem=mem,func=hex(f) if f else None,cls=cls,glob=is_global))
def vt_liveness(vt):
    gl=[w for w in VTWRITES.get(vt,[]) if w['glob']]
    ctor=[w for w in gl if w['cls']=='CTOR']; adt=[w for w in gl if w['cls']=='ATEXIT_DTOR']
    oth=[w for w in gl if w['cls']=='OTHER']
    if ctor: return 'LIVE'
    if adt: return 'DEAD'
    return 'NO_GLOBAL'

# ---- S13 pool ----
cov=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
s13=[]
for ln in open(cov,encoding='utf-8').read().splitlines()[1:]:
    p=ln.split('\t')
    if len(p)>=5 and p[1].strip()=='S13':
        s13.append(dict(entry=p[0].strip(),name=p[2].strip(),grade=p[4].strip()))
grade_static='[静态推断]'
static=[r for r in s13 if r['grade']==grade_static]
print('S13 total',len(s13),'static',len(static))

# Apply ③' detector to ALL S13; count hits by grade
hit_by_grade=collections.Counter()
hit_rows=[]
for r in s13:
    sh=dtor_shape(int(r['entry'],16))
    if sh['hit']:
        hit_by_grade[r['grade']]+=1
        hit_rows.append((r['entry'],r['name'],r['grade']))
print('③\' detector hits by grade:',dict(hit_by_grade))
print('hit rows:',hit_rows)

# N/M on static pool: ③' hit among static = would-be false positives if used to upgrade
static_hits=[h for h in hit_rows if h[2]==grade_static]
print('STATIC POOL: 恰命中 N =',len(static_hits),'rows:',static_hits)
# Among static hits, how many survive ㉓ (live vptr) => genuine vs false
for ea,nm,g in static_hits:
    vts=ENTRY_VTS.get(int(ea,16),[])
    print('  static-hit',ea,nm,'vts',[(hex(v),k,vt_liveness(v)) for v,k,_ in vts])

# ---- random 16B-aligned baseline ----
def baseline(seed, samples):
    rnd=random.Random(seed)
    hits=0
    for _ in range(samples):
        off=rnd.randrange(0, len(TB)-96)
        va=TA+off
        va=(va+15)&~15  # 16B align
        if va>=TE-96: continue
        sh=dtor_shape(va)
        if sh['hit']: hits+=1
    return hits
for seed in (20261118,20261119,7,424242):
    h=baseline(seed,600)
    print('baseline seed',seed,'hits',h,'/600 = %.3f%%'%(100*h/600))

# ---- 5 precedents ㉓ check ----
PREC=['004393F0','0046B5C0','0046C890','0062AF70','007730F0']
prec_out=[]
for ea in PREC:
    e=int(ea,16)
    sh=dtor_shape(e)
    vts=ENTRY_VTS.get(e,[])
    det=[]
    for v,k,nm in vts:
        lv=vt_liveness(v)
        gl=[w for w in VTWRITES.get(v,[]) if w['glob']]
        det.append(dict(vt=hex(v),slot=k,name=nm,liveness=lv,
                        ctor_writes=[w for w in gl if w['cls']=='CTOR'],
                        adtor_writes=[w for w in gl if w['cls']=='ATEXIT_DTOR']))
    prec_out.append(dict(entry=ea,dtor_shape=sh,vts=det))
    print('\nPREC',ea,'dtor_shape_hit',sh['hit'],'vts',len(vts))
    for d in det:
        print('   vt',d['vt'],'slot',d['slot'],d['liveness'],d['name'],
              'ctor',d['ctor_writes'],'adtor',d['adtor_writes'])

json.dump(dict(vtbases=len(VTBASES),hit_by_grade=dict(hit_by_grade),
    static_hits=static_hits,hit_rows=hit_rows,precedents=prec_out),
    open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K8RECHK\work\s5b_results.json','w'),indent=1)
print('\nDONE step5b')
