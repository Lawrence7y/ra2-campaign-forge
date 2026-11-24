# -*- coding: utf-8 -*-
"""Diagnostic: full-table class_to_sub application via RTTI slot classes."""
import os,re,sys,struct,collections,json,math,csv
import pefile
sys.stdout.reconfigure(encoding='utf-8')
HERE=os.path.dirname(os.path.abspath(__file__));PROJ=os.path.abspath(os.path.join(HERE,'..','..','..','..'))
ROOT=os.path.join(PROJ,'lead','next_re_20261117_r14')
EXE=os.path.join(PROJ,'ra2youli','gamemd.exe');COV=os.path.join(ROOT,'COVERAGE','coverage.tsv');ATL=os.path.join(PROJ,'lead','next_re_20261112_r10','W130_atlas','function_atlas.tsv')
pe=pefile.PE(EXE);IB=pe.OPTIONAL_HEADER.ImageBase;SZ=pe.OPTIONAL_HEADER.SizeOfImage
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
def dem(x):
    if x.startswith('.?AV') or x.startswith('.?AU'):x=x[4:]
    if x.endswith('@@'):x=x[:-2]
    return x.replace('?$','T_').replace('@','::')
rdb=blob[r.PointerToRawData:r.PointerToRawData+RSZ];nw=len(rdb)//4;w=struct.unpack_from('<%dI'%nw,rdb,0)
def it(v):return TLO<=v<THI
fmap=collections.defaultdict(list);i=0
while i<nw:
    if it(w[i]):
        j=i
        while j<nw and it(w[j]):j+=1
        cp=w[i-1] if i>=1 else 0;raw=rn(cp)
        if raw:
            c=dem(raw)
            for k in range(j-i):fmap[w[i+k]].append((c,raw,k))
        i=j
    else:i+=1
CONTAINER=('vectorclass','typelist','tclassfactory','vectorcursor','dynamicvector')
def c2s(c,raw):
    low=(c+' '+raw).lower()
    if any(k in low for k in CONTAINER):return 'S22'
    if 'locomotionclass' in low:return 'S11'
    if 'teamclass' in low or 'houseclass' in low:return 'S14'
    if 'weapontypeclass' in low:return 'S13'
    if 'commandclass' in low:return 'S09'
    if 't_blit' in low or 'rleblit' in low:return 'S07'
    return None
def ne(e):
    e=e.strip().upper()
    if e.startswith('0X'):e=e[2:]
    try:return '%08X'%int(e,16)
    except:return e
atlas=set()
with open(ATL,encoding='utf-8-sig') as f:
    for i,ln in enumerate(f):
        if i==0:continue
        p=ln.rstrip('\r\n').split('\t')
        if p and p[0].strip():atlas.add(ne(p[0]))
cov=[]
with open(COV,encoding='utf-8-sig') as f:
    for row in list(csv.reader(f,delimiter='\t'))[1:]:
        if len(row)>=8:cov.append(dict(entry=ne(row[0]),sub=row[1].strip(),name=row[2].strip(),sem=row[3],grade=row[4].strip()))
# full table: for each row with RTTI class, target from class_to_sub
move=collections.Counter(); examples=collections.defaultdict(list)
cur_vs_target=collections.Counter()
for rr in cov:
    mem=fmap.get(int(rr['entry'],16))
    if not mem:continue
    tgts=set()
    for c,raw,slot in mem:
        x=c2s(c,raw)
        if x:tgts.add(x)
    if not tgts:continue
    ns=sorted(tgts)
    target=ns[0] if len(ns)==1 else None  # ambiguous skip
    if target is None:continue
    cur_vs_target[(rr['sub'],target)]+=1
    if rr['sub']!=target:
        move[(rr['sub'],target)]+=1
        if len(examples[(rr['sub'],target)])<4:examples[(rr['sub'],target)].append((rr['entry'],rr['name'],mem[0][0]))
print('=== full-table rows with RTTI class, current -> target (ALL, atlas+outside) ===')
for k,v in sorted(cur_vs_target.items(),key=lambda x:-x[1]):print('  %s -> %s : %d'%(k[0],k[1],v))
print('\n=== rows that WOULD MOVE (current != target) ===')
tot=0
for k,v in sorted(move.items(),key=lambda x:-x[1]):
    print('  %s -> %s : %d  ex=%s'%(k[0],k[1],v,examples[k][:2]));tot+=v
print('TOTAL moves =',tot)
# S13 specifically
s13=[rr for rr in cov if rr['sub']=='S13']
s13_move=[rr for rr in s13 if fmap.get(int(rr['entry'],16)) and c2s(fmap[int(rr['entry'],16)][0][0],fmap[int(rr['entry'],16)][0][1])=='S22']
print('\nS13 rows total=%d, RTTI->S22(container)=%d'%(len(s13),len(s13_move)))
s13_in=[rr for rr in s13 if rr['entry'] in atlas]
s13_move_in=[rr for rr in s13_in if fmap.get(int(rr['entry'],16)) and c2s(fmap[int(rr['entry'],16)][0][0],fmap[int(rr['entry'],16)][0][1])=='S22']
print('S13 atlas-in=%d, RTTI->S22 atlas-in=%d'%(len(s13_in),len(s13_move_in)))
