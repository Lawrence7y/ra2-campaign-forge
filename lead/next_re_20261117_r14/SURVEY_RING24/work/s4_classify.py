
import json,collections,re,time,sys
from pathlib import Path
import pefile, capstone
from array import array
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

t0=time.time()
ROOT=Path(r'D:\Project\ra2-campaign-forge')
EXE=ROOT/'ra2youli'/'gamemd.exe'
OUT=ROOT/'lead/next_re_20261117_r14/SURVEY_RING24'
raw=EXE.read_bytes()
pe=pefile.PE(data=raw, fast_load=True); ib=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    secs.append(dict(name=s.Name.rstrip(b'\0').decode('latin1'),va=ib+s.VirtualAddress,
                     vs=s.Misc_VirtualSize, rs=s.SizeOfRawData, ptr=s.PointerToRawData))
by={s['name']:s for s in secs}
def va2off(va):
    for s in secs:
        if s['va']<=va<s['va']+s['rs']:
            o=s['ptr']+va-s['va']
            if o+4<=len(raw): return o
    return None
def u32(va):
    o=va2off(va)
    if o is None: return None
    return int.from_bytes(raw[o:o+4],'little')
text=by['.text']; tva=text['va']; tlen=text['vs']
code=raw[text['ptr']:text['ptr']+tlen]
def in_text(v): return v is not None and tva<=v<tva+tlen

# ---- build CFG arrays (atlas-independent extents)
NN=tlen+16
sz=bytearray(NN); kind=bytearray(NN); tgt={}
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail=True; md.skipdata=True
RET=1; JMP=2; JCC=3; CALL=4
JCCS={'je','jne','jz','jnz','jg','jge','jl','jle','ja','jae','jb','jbe','js','jns','jo','jno','jp','jnp','jcxz','jecxz'}
nins=0
for ins in md.disasm(code,tva):
    nins+=1
    o=ins.address-tva
    sz[o]=ins.size
    mn=ins.mnemonic
    if mn=='ret' or mn.startswith('ret') or mn in ('retn','retf'): kind[o]=RET
    elif mn=='jmp':
        kind[o]=JMP
        try: ops=ins.operands
        except Exception: ops=[]
        if ops and ops[0].type==X86_OP_IMM: tgt[o]=int(ops[0].imm)&0xffffffff
    elif mn in JCCS:
        kind[o]=JCC
        try: ops=ins.operands
        except Exception: ops=[]
        if ops and ops[0].type==X86_OP_IMM: tgt[o]=int(ops[0].imm)&0xffffffff
    elif mn=='call': kind[o]=CALL
print('cfg built',nins,'t=%.1f'%(time.time()-t0),flush=True)

ALLENTRY=set()

def extent(entry, cap=8000, stopset=None):
    """self-written CFG extent: returns (lo, hi, addrs) using branch following."""
    if not in_text(entry): return (entry,entry,[])
    seen=set(); stack=[entry]; addrs=[]
    lo=hi=entry; n=0
    while stack:
        a=stack.pop()
        while True:
            if not in_text(a): break
            if a in seen: break
            if stopset and a in stopset and a!=entry: break
            o=a-tva
            s=sz[o]
            if s==0: break
            seen.add(a); addrs.append(a); n+=1
            if n>cap: stack=[]; break
            if a<lo: lo=a
            if a+s>hi: hi=a+s
            k=kind[o]
            if k==RET: break
            if k==JMP:
                t=tgt.get(o)
                if t: stack.append(t); break
                break
            if k==JCC:
                t=tgt.get(o)
                if t: stack.append(t)
                a=a+s
                continue
            a=a+s
    return (lo,hi,sorted(addrs))

# ---- inputs
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATLASP=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
lines=COV.read_text(encoding='utf-8-sig').splitlines(); hdr=lines[0].split(',')
cov=[]
for l in lines[1:]:
    if not l.strip(): continue
    q=l.split('\t'); q+=['']*(8-len(q)); cov.append(dict(zip(hdr,q[:8])))
al=ATLASP.read_text(encoding='utf-8-sig').splitlines(); ah=al[0].split('\t')
atlas={}
for l in al[1:]:
    if not l.strip(): continue
    q=l.split('\t'); q+=['']*(len(ah)-len(q)); r=dict(zip(ah,q[:len(ah)]))
    k=r['entry'].strip().upper().replace('0X','')
    atlas[k]=dict(size=int(r['size']) if r['size'].strip().isdigit() else int(r['size'],0), n_instr=r['n_instr'])
def norm(e): return e.strip().upper().replace('0X','')

idx=json.load(open(OUT/'work'/'index.json'))
e2s={int(k,16):v for k,v in idx['entry2slots'].items()}
direct={int(k,16):v for k,v in idx['direct'].items()}
livevt={int(k,16):v for k,v in idx['livevt'].items()}
yr=json.load(open(OUT/'work'/'yrpp.json'))
bind={int(k,16):v for k,v in yr['bindings'].items()}
caddrs={k:set(v) for k,v in yr['class_addrs'].items()}

# ---- YRpp byte conformance (uses self-written CFG extent, NOT atlas size)
def yrpp_conform(entry):
    bl=bind.get(entry)
    if not bl: return None
    cls=bl[0][3]
    cand=caddrs.get(cls,set())
    if not cand: return dict(ok=False,cls=cls,n_cand=0,n_hit=0,why='class_has_no_absolute_addrs')
    lo,hi,addrs=extent(entry, cap=6000)
    hits=set()
    for a in addrs:
        o=a-tva
        b=code[o:o+sz[o]]
        # scan for 4-byte immediates matching candidate absolute addresses
        for c in cand:
            if c.to_bytes(4,'little') in b:
                hits.add(c)
    ok = len(hits)>=2 and len(addrs)>0
    return dict(ok=ok,cls=cls,n_cand=len(cand),n_hit=len(hits),
                hits=sorted(hits)[:8],n_ins=len(addrs),why=('ok' if ok else 'insufficient_byte_match'))

# ---- classify
rows=[]
for r in cov:
    sub=r['subsystem'].strip().upper()
    if not re.fullmatch(r'S(0[1-9]|1[0-9]|2[01])', sub): continue
    if r['grade'].strip()!='[静态推断]': continue
    k=norm(r['entry'])
    if k not in atlas: continue
    e=int(k,16)
    slots=e2s.get(e,[])
    has2_rtti=bool(slots)
    dc=direct.get(e,[]); lv=livevt.get(e,[])
    has4=bool(dc) or bool(lv)
    yc=None
    if not has2_rtti and not has4 and e in bind:
        yc=yrpp_conform(e)
    rows.append(dict(entry=k,sub=sub,name=r['name'],e=e,
        has2_rtti=has2_rtti,has4=has4,
        n_direct=len(dc),n_livevt=len(lv),
        rtti_cls=sorted({s[2] for s in slots})[:2], rtti_vt=(hex(slots[0][0]) if slots else ''), rtti_slot=(slots[0][1] if slots else ''),
        yrpp=(bind.get(e) or [None])[0], yrpp_conf=yc,
        size=atlas[k]['size']))
print('rows',len(rows),'t=%.1f'%(time.time()-t0),flush=True)
json.dump(rows, open(OUT/'work'/'rows.json','w'), ensure_ascii=False)
print('saved rows.json')
