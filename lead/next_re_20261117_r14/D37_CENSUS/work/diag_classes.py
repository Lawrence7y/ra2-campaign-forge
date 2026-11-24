# -*- coding: utf-8 -*-
"""Diagnostic: enumerate all distinct RTTI classes among nameable S22 rows, flag keyword hits."""
import os,re,sys,struct,collections,json
import pefile
sys.stdout.reconfigure(encoding='utf-8')
HERE=os.path.dirname(os.path.abspath(__file__)); PROJ=os.path.abspath(os.path.join(HERE,'..','..','..','..'))
EXE=os.path.join(PROJ,'ra2youli','gamemd.exe'); COV=os.path.join(PROJ,'lead','next_re_20261117_r14','COVERAGE','coverage.tsv')
pe=pefile.PE(EXE); IB=pe.OPTIONAL_HEADER.ImageBase; SZ=pe.OPTIONAL_HEADER.SizeOfImage
def sec(n):return [s for s in pe.sections if s.Name.rstrip(b'\0').decode('latin1')==n][0]
t=sec('.text');r=sec('.rdata');TLO=IB+t.VirtualAddress;THI=TLO+t.Misc_VirtualSize;RLO=IB+r.VirtualAddress;RSZ=r.SizeOfRawData
blob=open(EXE,'rb').read()
def off(va):
    rv=va-IB
    if rv<0 or rv>=SZ:return None
    for s in pe.sections:
        sv=s.VirtualAddress;vs=max(s.Misc_VirtualSize,s.SizeOfRawData)
        if sv<=rv<sv+vs:
            o=s.PointerToRawData+(rv-sv);return o if 0<=o<len(blob) else None
    return None
def u32(va):
    o=off(va);return struct.unpack_from('<I',blob,o)[0] if o is not None and o+4<=len(blob) else None
def cs(va,cap=256):
    o=off(va)
    if o is None or o+cap>len(blob):return b''
    b=blob[o:o+cap];z=b.find(b'\0');return b[:z] if z>0 else b''
def rn(cp):
    if not(IB<=cp<IB+SZ):return None
    sig=u32(cp);td=u32(cp+0xC);cd=u32(cp+0x10)
    if sig not in(0,1) or td is None or not(IB<=td<IB+SZ):return None
    nm=cs(td+8)
    return nm.decode('latin1') if nm.startswith(b'.?AV') or nm.startswith(b'.?AU') else None
def dem(t):
    if t.startswith('.?AV') or t.startswith('.?AU'):t=t[4:]
    if t.endswith('@@'):t=t[:-2]
    return t.replace('?$','T_').replace('@','::')
rdb=blob[r.PointerToRawData:r.PointerToRawData+RSZ];nw=len(rdb)//4;w=struct.unpack_from('<%dI'%nw,rdb,0)
def it(v):return TLO<=v<THI
fmap=collections.defaultdict(list);i=0
while i<nw:
    if it(w[i]):
        j=i
        while j<nw and it(w[j]):j+=1
        cp=w[i-1] if i>=1 else 0;raw=rn(cp)
        if raw is not None:
            c=dem(raw)
            for k in range(j-i):fmap[w[i+k]].append((c,raw))
        i=j
    else:i+=1
cov={}
with open(COV,encoding='utf-8-sig') as f:
    f.readline()
    for ln in f:
        p=ln.rstrip('\r\n').split('\t')
        if len(p)>=5: cov[p[0].strip().upper()]=p[1].strip()
s22e=[e for e,s in cov.items() if s=='S22']
classes=collections.Counter()
for e in s22e:
    for c,raw in fmap.get(int(e,16),[]):classes[(c,raw)]+=1
print('distinct (cls,raw) among nameable S22 =',len(classes),' total memberships=',sum(classes.values()))
CONTAINER=('vectorclass','typelist','tclassfactory','vectorcursor','dynamicvector')
KW=dict(S11=('locomotionclass',),S14=('teamclass','houseclass'),S13=('weapontypeclass',),S09=('commandclass',),S07=('t_blit','rleblit'))
def hit(c,raw):
    low=(c+' '+raw).lower()
    if any(k in low for k in CONTAINER):return 'CONTAINER->S22'
    hits=[]
    for s,ks in KW.items():
        if any(k in low for k in ks):hits.append(s)
    return ','.join(hits) if hits else 'DEFAULT->S22'
buckets=collections.Counter()
kw_hits=[]
for (c,raw),n in classes.items():
    h=hit(c,raw);buckets[h]+=1
    if h not in ('CONTAINER->S22','DEFAULT->S22'):
        kw_hits.append((c,raw,n,h))
print('buckets by class:',dict(buckets))
print('KEYWORD-HIT classes (non-container, non-default):',len(kw_hits))
for c,raw,n,h in sorted(kw_hits,key=lambda x:-x[2])[:60]:
    print('  %4d %-8s %-55s %s'%(n,h,c[:55],raw[:60]))
# also: how many S22 ROWS have a keyword-hit class (not just distinct classes)
row_kw=collections.Counter()
for e in s22e:
    hs=set(hit(c,raw) for c,raw in fmap.get(int(e,16),[]))
    for h in hs:row_kw[h]+=1
print('ROW-level bucket counts (a row may appear in >1):',dict(row_kw))
