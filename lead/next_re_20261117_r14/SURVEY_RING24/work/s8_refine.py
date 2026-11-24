
import json,collections,time
from pathlib import Path
import pefile, capstone
from capstone.x86 import X86_OP_IMM, X86_OP_MEM

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
text=by['.text']; tva=text['va']; tlen=text['vs']
code=raw[text['ptr']:text['ptr']+tlen]
def in_text(v): return v is not None and tva<=v<tva+tlen
NN=tlen+16
sz=bytearray(NN); kind=bytearray(NN); tgt={}
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail=True; md.skipdata=True
RET=1;JMP=2;JCC=3;CALL=4
JCCS={'je','jne','jz','jnz','jg','jge','jl','jle','ja','jae','jb','jbe','js','jns','jo','jno','jp','jnp','jcxz','jecxz'}
for ins in md.disasm(code,tva):
    o=ins.address-tva; sz[o]=ins.size; mn=ins.mnemonic
    if mn.startswith('ret'): kind[o]=RET
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
print('cfg',time.time()-t0,flush=True)

def extent(entry, cap=6000):
    if not in_text(entry): return (entry,entry,0)
    seen=set(); stack=[entry]; lo=hi=entry; n=0
    while stack:
        a=stack.pop()
        while True:
            if not in_text(a) or a in seen: break
            o=a-tva; s=sz[o]
            if s==0: break
            seen.add(a); n+=1
            if a<lo: lo=a
            if a+s>hi: hi=a+s
            if n>cap: stack=[]; break
            k=kind[o]
            if k==RET: break
            if k==JMP:
                t=tgt.get(o)
                if t: stack.append(t)
                break
            if k==JCC:
                t=tgt.get(o)
                if t: stack.append(t)
                a=a+s; continue
            a=a+s
    return (lo,hi,n)

rows=json.load(open(OUT/'work'/'rows.json'))
idx=json.load(open(OUT/'work'/'index.json'))
e2s={int(k,16):v for k,v in idx['entry2slots'].items()}
direct={int(k,16):v for k,v in idx['direct'].items()}
livevt={int(k,16):v for k,v in idx['livevt'].items()}
yr=json.load(open(OUT/'work'/'yrpp.json'))
bind={int(k,16):v for k,v in yr['bindings'].items()}
caddrs={k:set(v) for k,v in yr['class_addrs'].items()}

def yrpp_conform(entry, addrs):
    bl=bind.get(entry)
    if not bl: return None
    cls=bl[0][3]; cand=caddrs.get(cls,set())
    if not cand: return dict(ok=False,cls=cls,n_cand=0,n_hit=0,why='class_has_no_absolute_addrs')
    hits=set()
    for a in addrs:
        o=a-tva; b=code[o:o+sz[o]]
        for c in cand:
            if c.to_bytes(4,'little') in b: hits.add(c)
    ok=len(hits)>=2
    return dict(ok=ok,cls=cls,n_cand=len(cand),n_hit=len(hits),hits=sorted(hits)[:8],why=('ok' if ok else 'insufficient_byte_match'))

out=[]
agree=0; tot=0; ratios=[]
for r in rows:
    e=r['e']
    lo,hi,nins=extent(e)
    dc=[s for s in direct.get(e,[]) if not (lo<=s<hi)]
    lv=[x for x in livevt.get(e,[]) if not (lo<=x[3]<hi)]
    has4=bool(dc) or bool(lv)
    ad=[a for a in range(lo,hi) if sz[a-tva]>0] if nins<=6000 else []
    r2=dict(r)
    r2['n_direct_all']=len(direct.get(e,[]))
    r2['n_direct_out']=len(dc); r2['direct_out']=dc[:6]
    r2['n_livevt']=len(lv); r2['livevt']=lv[:4]
    r2['has4']=has4
    r2['ext_lo']=lo; r2['ext_hi']=hi; r2['ext_n']=nins
    r2['ext_size']=hi-lo
    if not r['has2_rtti']:
        r2['yrpp_conf']=yrpp_conform(e,ad) if e in bind else None
    else:
        r2['yrpp_conf']=None
    # atlas size agreement
    if r['size'] and nins<6000:
        tot+=1
        if hi-lo==r['size']: agree+=1
    out.append(r2)
print('rows',len(out),'extent==atlas size',agree,'/',tot,'t=%.1f'%(time.time()-t0),flush=True)
json.dump(out, open(OUT/'work'/'rows2.json','w'), ensure_ascii=False, default=int)
print('A', sum(1 for x in out if x['has2_rtti'] and x['has4']))
