# -*- coding: utf-8 -*-
"""S13-K8RECHK step5: detection-power counter-evidence + 5-precedent ㉓ check.
Read-only on exe. Writes only under S13_K8RECHK\work."""
import sys, struct, json, bisect, re, random
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
def va2fo(va):
    s=sec_of(va); return None if s is None else s['raw']+(va-s['va'])
def u32va(va):
    fo=va2fo(va); return struct.unpack('<I',DATA[fo:fo+4])[0] if fo is not None else None
def cstr(va,maxn=200):
    s=sec_of(va)
    if s is None: return ''
    b=DATA[s['raw']+(va-s['va']):s['raw']+(va-s['va'])+maxn]
    z=b.find(b'\x00'); return (b[:z] if z>=0 else b).decode('latin1','replace')
def rdva(va,n):
    s=sec_of(va); return b'' if s is None else DATA[s['raw']+(va-s['va']):s['raw']+(va-s['va'])+n]
TEXT=[s for s in SECS if s['name']=='.text'][0]; TA=TEXT['va']; TE=TA+TEXT['rs']
MD=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); MD.detail=True; MD.skipdata=True
INSNS=list(MD.disasm(DATA[TEXT['raw']:TEXT['raw']+TEXT['rs']],TA))
OPDEL=0x7C8B3D; ATEXIT=0x7C978A

# ---- ③' dtor-shape detector (from audit VERDICT: test [esp+8],1 gated call op_delete + ret 4) ----
def dtor_shape(va, maxbytes=96):
    """Return dict of features for a candidate function body."""
    ins=list(MD.disasm(rdva(va,maxbytes),va))
    has_opdel=False; has_test1=False; ret4=False; test_before_del=False; vptr_write=False
    opdel_at=None; test_at=None
    for i,x in enumerate(ins):
        if x.mnemonic=='call' and x.op_str.startswith('0x') and int(x.op_str,16)==OPDEL:
            has_opdel=True; opdel_at=x.address
        if x.mnemonic=='test' and 'esp + 8' in x.op_str and x.op_str.rstrip().endswith(', 1'):
            has_test1=True; test_at=x.address
        if x.mnemonic=='ret' and x.op_str.strip()=='4': ret4=True
        if x.mnemonic=='mov' and 'dword ptr [' in x.op_str and ',' in x.op_str:
            # self vptr write pattern: mov [reg], imm where imm in vtable range
            imm=x.op_str.rsplit(',',1)[1].strip()
            if imm.startswith('0x'):
                try:
                    iv=int(imm,16)
                    if 0x7e0000<=iv<0x820000: vptr_write=True
                except: pass
    if has_test1 and has_opdel and test_at is not None and opdel_at is not None:
        test_before_del = test_at < opdel_at
    return dict(has_test1=has_test1,has_opdel=has_opdel,test_before_del=test_before_del,
                ret4=ret4,vptr_write=vptr_write,
                hit=has_test1 and has_opdel and test_before_del and ret4,
                nins=len(ins))

# ---- detect vtable membership for an entry: scan .rdata/.data aligned dwords for vt bases ----
# Build map entry -> list of (vt,slot,col,name) by enumerating every plausible vt base.
# A vt base v: u32(v-4)=COL in .rdata; u32(COL+0xC)=TD in .rdata; cstr(TD+8) startswith .?A
VTBASES={}
for sec in SECS:
    if sec['name'] not in ('.rdata','.data'): continue
    n=sec['rs']//4
    for i in range(1,n):
        v=sec['va']+i*4
        col=u32va(v-4)
        if col is None or sec_of(col) is None or sec_of(col)['name']!='.rdata': continue
        td=u32va(col+0xC)
        if td is None or sec_of(td) is None or sec_of(td)['name']!='.rdata': continue
        nm=cstr(td+8,80)
        if nm.startswith('.?A'):
            VTBASES[v]=(col,td,nm)
print('vtable bases found',len(VTBASES))

# build entry->vts map by reading slots (up to 200 slots each)
ENTRY_VTS={}
for v,(col,td,nm) in VTBASES.items():
    for k in range(0,200):
        sv=u32va(v+k*4)
        if sv is None or not (TA<=sv<TE): break
        ENTRY_VTS.setdefault(sv,[]).append((v,k,col,nm))

# ---- install classification: for a vt, is it installed by a ctor (live) or only atexit dtor (dead)? ----
CTORS=set(); x=0x812004
for _ in range(3944):
    y=u32va(x)
    if y and TA<=y<TE: CTORS.add(y)
    x+=4
# atexit dtors from push;call
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
# FS for function attribution
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
# all mov [mem],imm writes
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
    is_global = mem.startswith('0x')  # absolute address => global
    cls='CTOR' if f in CTORS else ('ATEXIT_DTOR' if f in ATEXIT_DTOR else 'OTHER')
    VTWRITES.setdefault(iv,[]).append(dict(site=hex(ins.address),mem=mem,func=hex(f) if f else None,cls=cls,global_write=is_global))

def vt_liveness(vt):
    ws=VTWRITES.get(vt,[])
    gl=[w for w in ws if w['global_write']]
    ctor=[w for w in gl if w['cls']=='CTOR']
    adt=[w for w in gl if w['cls']=='ATEXIT_DTOR']
    other=[w for w in gl if w['cls']=='OTHER']
    if ctor: return 'LIVE',dict(ctor=ctor,adt=adt,other=other)
    if adt and not ctor: return 'DEAD',dict(ctor=ctor,adt=adt,other=other)
    return 'NO_GLOBAL_WRITE',dict(ctor=ctor,adt=adt,other=other)

# ---- S13 pool from coverage.tsv ----
f=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
s13=[]
for ln in open(f,encoding='utf-8').read().splitlines()[1:]:
    p=ln.split('\t')
    if len(p)>=5 and p[1].strip()=='S13':
        s13.append(dict(entry=p[0].strip(),subsystem=p[1].strip(),name=p[2].strip(),
                        sem=p[3].strip(),grade=p[4].strip()))
print('S13 pool',len(s13),'grades', {g:sum(1 for r in s13 if r['grade']==g) for g in set(r['grade'] for r in s13)})

# Apply ③' detector to S13 pool; report hits by grade
det_results=[]
for r in s13:
    ea=int(r['entry'],16)
    sh=dtor_shape(ea)
    vts=ENTRY_VTS.get(ea,[])
    liv=[]
    for v,k,col,nm in vts:
        lv,_=vt_liveness(v)
        liv.append((hex(v),k,lv,nm))
    det_results.append(dict(entry=r['entry'],name=r['name'],grade=r['grade'],dtor=sh,vts=liv))

# hits among [静态推断] pool
UNKNOWN='[静态推断]'  # actual may be encoded; use the raw from file
# determine actual grade strings present
grades=set(r['grade'] for r in s13)
static_grades=[g for g in grades if '̬' in g or '态' in g or '̶̬' in g]
print('grade repr', [ (g, repr(g)) for g in grades])

json.dump(dict(vtbases=len(VTBASES),det=det_results),
    open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K8RECHK\work\s5_detection.json','w'),indent=1)
print('DONE step5 part A')
