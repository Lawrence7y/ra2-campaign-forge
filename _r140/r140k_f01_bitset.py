import struct, re, json, collections, itertools
import pefile
data=open('ra2bench/gamemd.exe','rb').read(); N=len(data)
pe=pefile.PE('ra2bench/gamemd.exe', fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[(s.Name.decode().rstrip('\x00'), s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
def rva2off(rva):
    for nm,va,vs,raw,rs in secs:
        if va<=rva<va+max(vs,rs):
            d=rva-va
            return raw+d if d<rs else None
    return None
def sec_of(rva):
    for nm,va,vs,raw,rs in secs:
        if va<=rva<va+max(vs,rs): return nm
    return None
def dw(va):
    if va is None: return None
    o=rva2off(va-IB)
    if o is None or o+4>N: return None
    return struct.unpack_from('<I',data,o)[0]
def in_text(va): return va is not None and sec_of(va-IB)=='.text'
def indata(va): return va is not None and sec_of(va-IB) in ('.data','.rdata')
pat=re.compile(rb'\.\?A[VU][!-~]{1,200}?@@')
strings=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        for m in pat.finditer(data[raw:raw+rs]): strings.append((IB+va+m.start(), m.group()))
TDs={s-8:g for s,g in strings if dw(s-8) is not None and dw(s-4)==0 and indata(dw(s-8))}
tdset=set(TDs)
refs=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in tdset:
                c=IB+va+i*4-12
                if dw(c)==0 and dw(c+12)==v: refs.append((c,v))
colset=sorted({c for c,_ in refs}); col2td={c:t for c,t in refs}
vts=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in set(colset):
                vt=IB+va+i*4+4
                if dw(vt-4)==v: vts.append((vt,v))
vt_by=collections.defaultdict(list)
for vt,c in vts: vt_by[c].append(vt)
IDX={c:i for i,c in enumerate(colset)}
def mask(f):
    m=0
    for c in colset:
        if f(c): m|=1<<IDX[c]
    return m
mult=collections.Counter(col2td.values())
low={}
for c,t in col2td.items():
    if t not in low or c<low[t]: low[t]=c
lowset=set(low.values()); pcdc=collections.Counter(dw(c+16) for c in colset)
def slots(c):
    return max([sum(1 for j in range(64) if in_text(dw(vt+4*j))) for vt in vt_by.get(c,[])] or [0])
P={}
P['backed']=mask(lambda c: c in vt_by)
P['mdisp<=0x1000']=mask(lambda c: dw(c+4)<=0x1000)
P['mdisp==0']=mask(lambda c: dw(c+4)==0)
P['pcd_in_sec']=mask(lambda c: indata(dw(c+16)))
P['not_AU']=mask(lambda c: not TDs[col2td[c]].startswith(b'.?AU'))
P['lowest_VA']=mask(lambda c: c in lowset)
P['td_unique']=mask(lambda c: mult[col2td[c]]==1)
P['td_multi']=mask(lambda c: mult[col2td[c]]>1)
P['pcd_unique']=mask(lambda c: pcdc[dw(c+16)]==1)
P['one_vt']=mask(lambda c: len(vt_by.get(c,[]))==1)
P['slot1_text']=mask(lambda c: any(in_text(dw(vt+4)) for vt in vt_by.get(c,[])))
P['cd==0']=mask(lambda c: dw(c+8)==0)
P['name_no_dollar']=mask(lambda c: b'$' not in TDs[col2td[c]])
P['sym_name']=mask(lambda c: not TDs[col2td[c]].startswith(b'.?'))
for k in (2,4,6,8,9,10,12,16):
    P['slots>=%d'%k]=mask(lambda c,k=k: slots(c)>=k)
ALL=(1<<len(colset))-1
BASE=P['backed']
names=list(P)
print('COL=%d backed=%d' % (len(colset), bin(BASE).count('1')))
print()
print('=== single predicates |P & backed| (target 1201) ===')
for n in names:
    v=bin(P[n]&BASE).count('1'); print('  %-18s %d %s' % (n, v, '  <<<< MATCH 1201' if v==1201 else ''))
print()
print('=== pairs |Pa & Pb & backed| ===')
found=[]
for a,b in itertools.combinations(names,2):
    v=bin(P[a]&P[b]&BASE).count('1')
    if v in (1201,1211): found.append((v,a,b))
for v,a,b in sorted(found): print('  %d  %s & %s' % (v,a,b))
print('pair hits:', len(found))
print()
print('=== round-boundary truncation of .rdata scan (is 1201 a window artefact?) ===')
bnames=dict(rva2off=rva2off)
vtpos=[]  # (file offset of ref dword, col)
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in set(colset) and dw(IB+va+i*4)==v:
                vtpos.append((raw+i*4, v))
vtpos.sort()
print('backed at round file-offset windows:')
for T in (0x3e1000,0x3e8000,0x3f0000,0x3f4000,0x3f6000,0x3f7000,0x3f8000,0x3f9000,0x3fa000,0x3fb000,0x400000,0x410000,0x412000):
    b={v for fo,v in vtpos if fo<T}
    print('   T=%#09x backed=%d %s' % (T,len(b),'<<<< MATCH' if len(b)==1201 else ('<<< MATCH 1211' if len(b)==1211 else '')))
json.dump({'col':len(colset),'backed':bin(BASE).count('1')},open('_r140/r140k.json','w'))
