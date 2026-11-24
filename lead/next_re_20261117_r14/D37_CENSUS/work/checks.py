# -*- coding: utf-8 -*-
"""Supplementary checks: nameability split, dup entries, reference instances, raw mangled top-20."""
import os, re, sys, struct, collections, json
import pefile
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE,'..','..','..','..'))
EXE = os.path.join(PROJ,'ra2youli','gamemd.exe')
COV = os.path.join(PROJ,'lead','next_re_20261117_r14','COVERAGE','coverage.tsv')
ATL = os.path.join(PROJ,'lead','next_re_20261112_r10','W130_atlas','function_atlas.tsv')
TAB=chr(9)
pe=pefile.PE(EXE); IB=pe.OPTIONAL_HEADER.ImageBase; SZIMG=pe.OPTIONAL_HEADER.SizeOfImage
def sec(n):
    return [s for s in pe.sections if s.Name.rstrip(b'\x00').decode('latin1')==n][0]
txt=sec('.text'); rdat=sec('.rdata')
TLO=IB+txt.VirtualAddress; THI=TLO+txt.Misc_VirtualSize
RLO=IB+rdat.VirtualAddress; RSZ=rdat.SizeOfRawData
blob=open(EXE,'rb').read()
def va_off(va):
    rva=va-IB
    if rva<0 or rva>=SZIMG: return None
    for s in pe.sections:
        sv=s.VirtualAddress; vs=max(s.Misc_VirtualSize,s.SizeOfRawData)
        if sv<=rva<sv+vs:
            o=s.PointerToRawData+(rva-sv)
            return o if 0<=o<len(blob) else None
    return None
def u32(va):
    o=va_off(va)
    return struct.unpack_from('<I',blob,o)[0] if o is not None and o+4<=len(blob) else None
def cstr(va,cap=256):
    o=va_off(va)
    if o is None or o+cap>len(blob): return b''
    b=blob[o:o+cap]; z=b.find(b'\x00'); return b[:z] if z>0 else b''
def col_raw(colp):
    if not (IB<=colp<IB+SZIMG): return None
    sig=u32(colp); off=u32(colp+4); cd=u32(colp+8); tdp=u32(colp+0xC); pcd=u32(colp+0x10)
    if None in (sig,off,cd,tdp,pcd) or sig not in (0,1): return None
    if not (IB<=tdp<IB+SZIMG): return None
    nm=cstr(tdp+8)
    if not (nm.startswith(b'.?AV') or nm.startswith(b'.?AU')): return None
    return nm.decode('latin1')
def demangle(t):
    if t.startswith('.?AV') or t.startswith('.?AU'): t=t[4:]
    if t.endswith('@@'): t=t[:-2]
    return t.replace('?$','T_').replace('@','::')
rdata_blob=blob[rdat.PointerToRawData:rdat.PointerToRawData+RSZ]
nw=len(rdata_blob)//4; words=struct.unpack_from('<%dI'%nw,rdata_blob,0)
def in_text(v): return TLO<=v<THI
fmap=collections.defaultdict(list)
rawname_by_cls={}
i=0; runs=[]
while i<nw:
    if in_text(words[i]):
        j=i
        while j<nw and in_text(words[j]): j+=1
        runs.append((i,j)); i=j
    else: i+=1
for i,j in runs:
    colp=words[i-1] if i>=1 else 0
    raw=col_raw(colp)
    if raw is None: continue
    cls=demangle(raw); rawname_by_cls.setdefault(cls,raw)
    vt=RLO+4*i
    for k in range(j-i):
        fmap[words[i+k]].append((cls,vt,k,raw))
# coverage
cov=[]
with open(COV,encoding='utf-8',errors='replace') as f:
    f.readline()
    for ln in f:
        p=ln.rstrip('\n').split(TAB)
        if len(p)>=5: cov.append(dict(entry=p[0].upper(),sub=p[1],name=p[2],sem=p[3],grade=p[4]))
atlas=set()
with open(ATL,encoding='utf-8',errors='replace') as f:
    f.readline()
    for ln in f:
        p=ln.rstrip('\n').split(TAB)
        if p and p[0]: atlas.add(p[0].upper())
s22=[r for r in cov if r['sub']=='S22']
# duplicate entries check
ec=collections.Counter(r['entry'] for r in cov)
dup22=[(e,n) for e,n in ec.items() if n>1 and any(r['entry']==e for r in s22)]
print('duplicate entries in coverage affecting S22:', dup22[:10], 'count=',len(dup22))
# nameability split
def nameable(e):
    return fmap.get(int(e,16))
in_n=in_y=out_n=out_y=0
for r in s22:
    nm = nameable(r['entry'])
    if r['entry'] in atlas:
        if nm: in_y+=1
        else: in_n+=1
    else:
        if nm: out_y+=1
        else: out_n+=1
print('S22 atlas-in: nameable=%d unnameable=%d (%.2f%%)'%(in_y,in_n,100.0*in_y/(in_y+in_n)))
print('S22 atlas-out: nameable=%d unnameable=%d (%.2f%%)'%(out_y,out_n,100.0*out_y/(out_y+out_n)))
print('S22 all: nameable=%d unnameable=%d'%(in_y+out_y,in_n+out_n))
# grade distribution with explicit safe print
gc=collections.Counter(r['grade'] for r in s22)
print('grade keys repr:', [(repr(k),v) for k,v in gc.items()])
# top 20 raw mangled
ctr=collections.Counter()
for r in s22:
    nm=fmap.get(int(r['entry'],16))
    if nm:
        for c in set(x[0] for x in nm): ctr[c]+=1
print('distinct determinable classes:', len(ctr))
print('TOP20 demangled:')
for c,n in ctr.most_common(20):
    print('  %4d  %s   [raw %s]'%(n,c,rawname_by_cls.get(c,'')))
# reference instances
refs=['006B6EA0','006B6FA0','006B6C90','006B7F10','006B8120','004E0E80']
print('REFERENCE INSTANCES:')
cov_by_e={r['entry']:r for r in cov}
for e in refs:
    r=cov_by_e.get(e); nm=fmap.get(int(e,16))
    print('  %s: sub=%s grade=%s name=%s | RTTI=%s'%(e, r['sub'] if r else '-', r['grade'] if r else '-', r['name'] if r else '-', [x[0] for x in nm] if nm else '-'))
# write clean summary json
out=dict(dup22_count=len(dup22),
         atlas_in_nameable=in_y,atlas_in_unnameable=in_n,
         atlas_out_nameable=out_y,atlas_out_unnameable=out_n,
         grade={repr(k):v for k,v in gc.items()},
         distinct_classes=len(ctr),
         top20=[dict(cls=c,n=n,raw=rawname_by_cls.get(c,'')) for c,n in ctr.most_common(20)])
with open(os.path.join(HERE,'checks.json'),'w',encoding='utf-8') as f:
    json.dump(out,f,ensure_ascii=False,indent=1)
