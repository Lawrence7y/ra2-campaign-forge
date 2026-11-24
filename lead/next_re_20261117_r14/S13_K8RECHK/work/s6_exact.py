# -*- coding: utf-8 -*-
"""S13-K8RECHK step6: replicate audit t25.py full4/ring3 detector EXACTLY (independent copy),
apply to full S13 pool, [静态推断] pool, random 16B baseline, and 5 precedents ㉓ check.
Read-only on exe. Writes only under S13_K8RECHK\work."""
import sys, struct, json, random, collections, bisect, re
import pefile, capstone
sys.stdout.reconfigure(encoding='utf-8')
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
DATA=open(EXE,'rb').read(); pe=pefile.PE(EXE,fast_load=True); IMG=pe.OPTIONAL_HEADER.ImageBase
SECS=[]
for s in pe.sections:
    nm=s.Name.rstrip(b'\x00').decode('latin1')
    SECS.append(dict(name=nm,va=IMG+s.VirtualAddress,vs=s.Misc_VirtualSize,raw=s.PointerToRawData,rs=s.SizeOfRawData,
        end=IMG+s.VirtualAddress+s.Misc_VirtualSize))
def sec_of(va):
    for s in SECS:
        if s['va']<=va<s['end']: return s
    return None
def in_raw(va,n=1):
    s=sec_of(va); return s is not None and (va-s['va'])+n<=s['rs']
def va2fo(va):
    s=sec_of(va); return None if s is None else s['raw']+(va-s['va'])
def u32va(va):
    fo=va2fo(va)
    if fo is None or fo+4>len(DATA): return None
    return struct.unpack('<I',DATA[fo:fo+4])[0]
def rdva(va,n):
    s=sec_of(va); return b'' if s is None else DATA[s['raw']+(va-s['va']):s['raw']+(va-s['va'])+n]
def cstr(va,maxn=200):
    b=rdva(va,maxn); z=b.find(b'\x00'); return (b[:z] if z>=0 else b)
TEXT=[s for s in SECS if s['name']=='.text'][0]; TEXTA=TEXT['va']; TEXTEND=TEXT['va']+TEXT['rs']
TB=DATA[TEXT['raw']:TEXT['raw']+TEXT['rs']]
MD=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); MD.detail=True; MD.skipdata=True

# ---- exact replicas from t25.py ----
def is_colptr(v):
    sc=sec_of(v)
    if not sc or sc['name']!='.rdata': return False
    td=u32va(u32va(v+0xC)+8) if u32va(v+0xC) is not None else None
    try:
        coltd=u32va(v+0xC)
        return cstr(coltd+8,5).startswith(b'.?AV')
    except: return False
def vtable_base(S):
    for k in range(0,60):
        cand=S-4*k
        if not in_raw(cand-4,4): return None
        if is_colptr(u32va(cand-4)): return cand
    return None
def rtti(vt):
    try:
        col=u32va(vt-4)
        if not is_colptr(col): return None
        return cstr(u32va(col+0xC)+8,200).decode('latin1')
    except: return None
def slots_of(entry):
    out=[]
    for s in SECS:
        if s['name'] not in ('.rdata','.data'): continue
        blob=DATA[s['raw']:s['raw']+s['rs']]
        pat=struct.pack('<I',entry); i=blob.find(pat)
        while i!=-1:
            if i%4==0: out.append(s['va']+i)
            i=blob.find(pat,i+1)
    return out
def cfg(entry,limit=0x600):
    seen={}; wl=[entry]; ins=[]
    while wl:
        a=wl.pop()
        if a in seen or not (TEXTA<=a<TEXTEND): continue
        while True:
            if a in seen or a>=entry+limit: break
            try: it=next(MD.disasm(rdva(a,16),a,count=1))
            except StopIteration: break
            seen[a]=it; ins.append(it); m=it.mnemonic
            if m.startswith('ret'): break
            try: ops=it.operands
            except: break
            if m=='jmp':
                if ops and ops[0].type==capstone.x86.X86_OP_IMM: wl.append(ops[0].imm)
                break
            if m.startswith('j'):
                if ops and ops[0].type==capstone.x86.X86_OP_IMM: wl.append(ops[0].imm)
                a+=it.size; continue
            a+=it.size
    ins.sort(key=lambda x:x.address); return ins
def ring3(ins):
    if not ins: return False
    dcall=[]; ret4=False; gate=False
    for i,it in enumerate(ins):
        try: ops=it.operands
        except: continue
        if it.mnemonic=='call' and ops and ops[0].type==capstone.x86.X86_OP_IMM and ops[0].imm==0x7C8B3D:
            dcall.append(i)
            for j in range(max(0,i-7),i):
                if ins[j].mnemonic=='test' and ins[j].op_str.replace(' ','').endswith(',1'): gate=True
        if it.mnemonic.startswith('ret') and it.op_str=='4': ret4=True
    return bool(dcall) and ret4 and gate
def full4(entry):
    if not (TEXTA<=entry<TEXTEND): return False
    if entry%16: return False
    b0=rdva(entry,1)
    if not b0 or b0[0] in (0xE8,0xE9,0xEB): return False
    bases=set(b for b in (vtable_base(x) for x in slots_of(entry)) if b)
    if not bases: return False
    if not any(rtti(b) for b in bases): return False
    ins=cfg(entry)
    if not ring3(ins): return False
    return True

# ① verify detector reproduces audit: run over its 859-list a few + check S13 18
dtor_list=set(json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K8\_audit\EVIDENCE\dtor_shaped_functions.json')))
spot=['00401950','0040BBC0','0040BC10','0065BED0','0046B5C0','0075E510']
for ea in spot:
    e=int(ea,16)
    print('spot',ea,'inAuditList',ea in dtor_list,'full4',full4(e),'ring3',ring3(cfg(e)))

# ② apply full4 to full S13 pool
cov=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
s13=[]
for ln in open(cov,encoding='utf-8').read().splitlines()[1:]:
    p=ln.split('\t')
    if len(p)>=5 and p[1].strip()=='S13':
        s13.append(dict(entry=p[0].strip(),name=p[2].strip(),grade=p[4].strip()))
hit_by_grade=collections.Counter(); hits=[]
for r in s13:
    if full4(int(r['entry'],16)):
        hit_by_grade[r['grade']]+=1; hits.append((r['entry'],r['name'],r['grade']))
print('\nFULL S13 POOL (%d rows) full4 hits by grade:'%len(s13),dict(hit_by_grade))
print('hits:',hits)

# ③ [静态推断] pool specific
static=[r for r in s13 if r['grade']=='[静态推断]']
static_hits=[h for h in hits if h[2]=='[静态推断]']
print('\n[静态推断] pool size',len(static),'hits N=',len(static_hits),static_hits)
# check: any false positive = a hit that is NOT a defensible deleting dtor
fp=[h for h in static_hits if 'dtor' not in h[1].lower() and 'deleting' not in h[1].lower()]
print('static false positives M=',len(fp),fp)

# ④ random 16B baseline (exact t25 method)
print('\nRANDOM 16B baseline (full4):')
lo,hi=TEXTA,TEXTEND-0x1000
for seed in (20261118,20261119,424242,7):
    rnd=random.Random(seed); n=150; hit=0
    for _ in range(n):
        a=(rnd.randrange(lo,hi)//16)*16
        if full4(a): hit+=1
    print('  seed=%d n=%d pass=%d rate=%.3f%%'%(seed,n,hit,100.0*hit/n))

# ⑤ 5 precedents full4 + ㉓ liveness
# liveness helpers (ctor set + atexit dtors + global writes)
CTORS=set(); x=0x812004
for _ in range(3944):
    y=u32va(x)
    if y and TEXTA<=y<TEXTEND: CTORS.add(y)
    x+=4
ALLINS=list(MD.disasm(TB,TEXTA))
atexit_reg={}
for k,ins in enumerate(ALLINS):
    if ins.mnemonic=='call' and ins.op_str.startswith('0x'):
        try: t=int(ins.op_str,16)
        except: continue
        if t==0x7C978A:
            for j in range(max(0,k-14),k):
                p=ALLINS[j]
                if p.mnemonic=='push':
                    try: pv=int(p.op_str,16)
                    except: continue
                    if TEXTA<=pv<TEXTEND: atexit_reg.setdefault(pv,[]).append((hex(p.address),hex(ins.address))); break
ATEXIT_DTOR=set(atexit_reg)
FS=set(CTORS)|set(ATEXIT_DTOR)
for ins in ALLINS:
    if ins.mnemonic in ('call','push') and ins.op_str.startswith('0x'):
        try: t=int(ins.op_str,16)
        except: continue
        if TEXTA<=t<TEXTEND: FS.add(t)
for va in range(TEXTA,TEXTEND,16):
    b=rdva(va,1)
    if b and b[0] in (0x55,0x53,0x56,0x57,0x6a,0x68,0x81,0x83,0xa1,0xa3,0x8b): FS.add(va)
FS=sorted(FS)
def func_of(w):
    k=bisect.bisect_right(FS,w)-1; return FS[k] if k>=0 else None
MEMRE=re.compile(r'\[([^\]]+)\]')
VTWRITES={}
for ins in ALLINS:
    if ins.mnemonic!='mov' or 'ptr [' not in ins.op_str or ',' not in ins.op_str: continue
    imm=ins.op_str.rsplit(',',1)[1].strip()
    if not imm.startswith('0x'): continue
    try: iv=int(imm,16)
    except: continue
    m=MEMRE.search(ins.op_str); mem=m.group(1) if m else '?'
    f=func_of(ins.address)
    cls='CTOR' if f in CTORS else ('ATEXIT_DTOR' if f in ATEXIT_DTOR else 'OTHER')
    if mem.startswith('0x'):  # global
        VTWRITES.setdefault(iv,[]).append(dict(site=hex(ins.address),mem=mem,func=hex(f) if f else None,cls=cls))
def liveness(vt):
    ws=VTWRITES.get(vt,[])
    ctor=[w for w in ws if w['cls']=='CTOR']; adt=[w for w in ws if w['cls']=='ATEXIT_DTOR']
    if ctor: return 'LIVE',ctor,adt
    if adt: return 'DEAD',ctor,adt
    return 'NO_GLOBAL_WRITE',ctor,adt
PREC=['004393F0','0046B5C0','0046C890','0062AF70','007730F0']
print('\n5 PRECEDENTS (full4 + ㉓):')
prec_out=[]
for ea in PREC:
    e=int(ea,16)
    f4=full4(e)
    bases=set(b for b in (vtable_base(x) for x in slots_of(e)) if b)
    liv=[]
    for b in sorted(bases):
        lv,ctor,adt=liveness(b)
        liv.append(dict(vt=hex(b),rtti=rtti(b),liveness=lv,ctor=ctor,adt=adt))
    prec_out.append(dict(entry=ea,full4=f4,inAuditList=ea in dtor_list,vts=liv))
    print(' ',ea,'full4',f4,'inAuditList',ea in dtor_list)
    for d in liv:
        print('     vt',d['vt'],d['rtti'],'->',d['liveness'],'ctor',d['ctor'],'adtor',d['adt'])

json.dump(dict(full4_hits=hits,hit_by_grade=dict(hit_by_grade),
    static_pool=len(static),static_hits=static_hits,static_fp=fp,precedents=prec_out),
    open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K8RECHK\work\s6_results.json','w'),indent=1)
print('\nDONE step6')
