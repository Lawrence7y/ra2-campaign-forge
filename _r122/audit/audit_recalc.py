#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AUDIT independent recalc for R122 claims P1-P5.
Read-only against original exe and _r122 outputs; writes only stdout.
All numbers printed here are measured, not copied from main-session json.
"""
import collections, hashlib, json, re, struct
import pefile

EXE='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
D=open(EXE,'rb').read()
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
SECS=[]
for s in pe.sections:
    nm=s.Name.rstrip(b'\0').decode()
    SECS.append(dict(name=nm,va=IB+s.VirtualAddress,vs=s.Misc_VirtualSize,pr=s.PointerToRawData,rs=s.SizeOfRawData))
def sec_of(va):
    for x in SECS:
        if x['va']<=va<x['va']+x['vs']: return x
    return None
def rd(va,n):
    x=sec_of(va)
    if x is None: return None
    if va-x['va']+n>x['rs']: return None
    off=x['pr']+(va-x['va'])
    return D[off:off+n] if off+n<=len(D) else None
def u32(va):
    b=rd(va,4)
    return None if b is None else struct.unpack('<I',b)[0]
def region(va):
    x=sec_of(va)
    if x is None: return 'NONE',None
    return ('RAW' if va<x['va']+x['rs'] else 'BSS'),x['name']

DS=[x for x in SECS if x['name']=='.data'][0]
BSS_LO=DS['va']+DS['rs']; BSS_HI=DS['va']+DS['vs']
TXT=[x for x in SECS if x['name']=='.text'][0]
TDATA=D[TXT['pr']:TXT['pr']+TXT['rs']]; TBASE=TXT['va']
print('SHA256',hashlib.sha256(D).hexdigest())
print('BSS_LO=%08x BSS_HI=%08x size=%d'%(BSS_LO,BSS_HI,BSS_HI-BSS_LO))

# ---- recalc 35 edx from scratch (same selection rule, independent bytes) ----
calls={}
for i in range(len(TDATA)-5):
    if TDATA[i]!=0xe8: continue
    rel=struct.unpack_from('<i',TDATA,i+1)[0]
    va=TBASE+i; tgt=va+5+rel
    if 0x67fdf0<=tgt<=0x680f80: calls.setdefault(tgt,[]).append(va)
sites=sorted(s for ss in calls.values() for s in ss)
extra=sorted(set(sites)-set([0x67df0f,0x67df29,0x67df43,0x67df5d,0x67df77,0x67df91,0x67dfab,0x67dfc5,0x67dfdf,0x67dff9,0x67e013,0x67e02d,0x67e047,0x67e061,0x67e07b,0x67e095,0x67e0af,0x67e0c9,0x67e0e3,0x67e0fd,0x67e117,0x67e1e7,0x67e201,0x67e21b,0x67e235,0x67e24f,0x67e28f,0x67e2a9,0x67e2c3,0x67e2dd,0x67e2f7,0x67e311,0x67e32b,0x67e390,0x67e3aa]))
twin=sorted(set(sites)-set(extra))
EDX=[]
for s in twin:
    b=rd(s-7,7)
    EDX.append(struct.unpack_from('<I',b,1)[0])
print('call entries=%d sites=%d extra=%s twin=%d'%(len(calls),len(sites),[hex(x) for x in extra],len(twin)))
print('EDX count=%d distinct=%d'%(len(EDX),len(set(EDX))))
print('EDX regions',collections.Counter(region(a) for a in EDX))
print('EDX in BSS range',sum(1 for a in EDX if BSS_LO<=a<BSS_HI),'/',len(EDX))
print('EDX min=%08x max=%08x'%(min(EDX),max(EDX)))

# ---- all c7 05 writes into BSS ----
writes={}
i=0
while i<len(TDATA)-10:
    if TDATA[i]==0xc7 and TDATA[i+1]==0x05:
        t=struct.unpack_from('<I',TDATA,i+2)[0]
        if BSS_LO<=t<BSS_HI: writes.setdefault(t,[]).append(TBASE+i)
    i+=1
nsites=sum(len(v) for v in writes.values())
print('BSS c7 05: targets=%d sites=%d'%(len(writes),nsites))
print('writes-per-target hist',sorted(collections.Counter(len(v) for v in writes.values()).items()))
print('35 covered=%d hist35=%s'%(sum(1 for a in EDX if a in writes),dict(collections.Counter(len(writes[a]) for a in EDX))))

def name_of_vtable(vt):
    col=u32(vt-4) if vt is not None else None
    if col is None: return None,'no-COL'
    b=rd(col,0x18)
    if b is None: return None,'no-COL-body'
    sig,off,cd,td,chd,selfv=struct.unpack('<IIIIII',b)
    if sig!=0 or td==0: return None,'bad-COL'
    s=rd(td+8,0x100)
    if s is None: return None,'no-TD'
    nm=s.split(b'\0')[0].decode('ascii','replace')
    if not nm.startswith('.?AV'): return None,'not-class:'+nm[:20]
    return nm,'ok'

# ---- 70 names ----
allnames=[]; obj_info=[]
for a in EDX:
    nm_list=[]
    for s in sorted(writes[a]):
        b=rd(s,10)
        vt=struct.unpack_from('<I',b,6)[0]
        nm,w=name_of_vtable(vt)
        nm_list.append(nm)
        allnames.append(nm)
    obj_info.append((a,nm_list))
print('70 names resolved=%d distinct_all=%d'%(sum(1 for n in allnames if n),len(set(allnames))))
elems=[n.split('VectorClass@')[1].split('@@@')[0] for n in allnames if n]
print('elem types distinct=%d all PAV=%s'%(len(set(elems)),all(e.startswith('PAV') for e in elems)))
print('first object sample', [hex(x) for x in EDX[:1]], obj_info[0])

# ---- path B: all VectorClass-family RTTI targets (independent rebuild) ----
VECRE=re.compile(r'^\.\?AV\?\$(Dynamic)?VectorClass@')
b_class=collections.Counter(); why=collections.Counter(); imm_by_why=collections.defaultdict(list)
for tgt,sites in writes.items():
    for s in sites:
        b=rd(s,10)
        if b is None: continue
        vt=struct.unpack_from('<I',b,6)[0]
        nm,w=name_of_vtable(vt)
        if nm is None:
            why[w]+=1
            imm_by_why[w].append(vt)
        elif VECRE.match(nm):
            why['VectorClass']+=1
            b_class[tgt]+=1
        else:
            why['other-RTTI']+=1
print('write-side census',dict(why))
print('ALL_VEC_OBJS=%d'%len(b_class))
print('OBJ35 subset=%d'%sum(1 for a in EDX if a in b_class))
EXTRA=sorted(set(b_class)-set(EDX))
print('EXTRA=%d'%len(EXTRA))

# ---- shape check: extra with Dynamic+Vector same element ----
extra_dual=[]
for t in EXTRA:
    names=[]
    for s in sorted(writes[t]):
        b=rd(s,10)
        vt=struct.unpack_from('<I',b,6)[0]
        names.append(name_of_vtable(vt)[0])
    real=[n for n in names if n]
    vec=[n for n in real if n and not n.startswith('.?AV?$Dynamic')]
    dyn=[n for n in real if n and n.startswith('.?AV?$Dynamic')]
    if len(vec)==1 and len(dyn)==1:
        e1=vec[0].split('VectorClass@')[1].split('@@@')[0]
        e2=dyn[0].split('VectorClass@')[1].split('@@@')[0]
        if e1==e2: extra_dual.append((t,e1))
print('EXTRA dual-form same-elem=%d'%len(extra_dual))
print('EXTRA dual sample',[(hex(a),b) for a,b in extra_dual[:5]])

# ---- A5: imm32 histogram by VA region ----
# real vptr range from .rdata: 0x7e1000..0x811074
RD=[x for x in SECS if x['name']=='.rdata'][0]
RD_LO=RD['va']; RD_HI=RD['va']+RD['vs']
print('.rdata range [%08x,%08x)'%(RD_LO,RD_HI))
max_end=max(x['va']+x['vs'] for x in SECS)
print('max section end=%08x SizeOfImageVA=%08x'%(max_end,IB+pe.OPTIONAL_HEADER.SizeOfImage))
for w,vals in imm_by_why.items():
    if not vals: continue
    buckets=collections.Counter()
    lo=min(vals); hi=max(vals)
    for v in vals:
        x=sec_of(v)
        if x is None: buckets['NOWHERE']+=1
        else: buckets[x['name']+(' RAW' if v<x['va']+x['rs'] else ' BSS')]+=1
    print('WHY=%s n=%d min=%08x max=%08x buckets=%s'%(w,len(vals),lo,hi,dict(buckets)))

# ---- detailed interval histogram over NOWHERE imm32 ----
nw=imm_by_why.get('no-COL',[])+imm_by_why.get('no-COL-body',[])+imm_by_why.get('bad-COL',[])+imm_by_why.get('no-TD',[])+imm_by_why.get('not-class',[])
if nw:
    bins=collections.Counter()
    for v in nw:
        if v<0x400000: k='[00000000,00400000) image-base-below'
        elif v<0x7e1000: k='[00400000,007e1000) .text/.rdata-gap'
        elif v<0x811074: k='[007e1000,00811074) .rdata'
        elif v<0x812000: k='[00811074,00812000) rdata-data-gap'
        elif v<0x87e000: k='[00812000,0087e000) .data RAW'
        elif v<0xb79be4: k='[0087e000,00b79be4) .data BSS'
        elif v<0xb7a000: k='[00b79be4,00b7a000) data-rsrc-gap'
        elif v<0xb92128: k='[00b7a000,00b92128) .rsrc'
        elif v<0xb93000: k='[00b92128,00b93000) rsrc-detour-gap'
        elif v<0xb95718: k='[00b93000,00b95718) .detour'
        elif v<0xb96000: k='[00b95718,00b96000) detour-image-end'
        else: k='[00b96000,FFFFFFFF) beyond-image'
        bins[k]+=1
    print('NOWHERE interval histogram:')
    for k,v in sorted(bins.items()): print('  %-45s %d'%(k,v))
