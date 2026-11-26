import struct, re, json, itertools, collections
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
cols=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in tdset:
                c=IB+va+i*4-12
                if dw(c)==0 and dw(c+12)==v: cols.append((c,v))
colset={c for c,_ in cols}; col2td={c:t for c,t in cols}
vts=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in colset:
                vt=IB+va+i*4+4
                if dw(vt-4)==v: vts.append((vt,v))
vt_by_col=collections.defaultdict(list)
for vt,c in vts: vt_by_col[c].append(vt)
mult=collections.Counter(col2td.values())
low={}
for c,t in col2td.items():
    if t not in low or c<low[t]: low[t]=c
lowset=set(low.values())
pcdcnt=collections.Counter(dw(c+16) for c in colset)

def slots(c,k=64):
    best=0
    for vt in vt_by_col.get(c,[]):
        best=max(best,sum(1 for j in range(k) if in_text(dw(vt+4*j))))
    return best

P={}
P['backed']       = lambda c: c in vt_by_col
P['mdisp<=0x1000']= lambda c: dw(c+4)<=0x1000
P['mdisp==0']     = lambda c: dw(c+4)==0
P['pcd_in_sec']   = lambda c: indata(dw(c+16))
P['not_AU']       = lambda c: not TDs[col2td[c]].startswith(b'.?AU')
P['lowest_VA']    = lambda c: c in lowset
P['td_unique']    = lambda c: mult[col2td[c]]==1
P['td_multi']     = lambda c: mult[col2td[c]]>1
P['pcd_unique']   = lambda c: pcdcnt[dw(c+16)]==1
P['one_vt']       = lambda c: len(vt_by_col.get(c,[]))==1
P['slot1_text']   = lambda c: any(in_text(dw(vt+4)) for vt in vt_by_col.get(c,[]))
P['slot2_text']   = lambda c: any(in_text(dw(vt+8)) for vt in vt_by_col.get(c,[]))
P['cd==0']        = lambda c: dw(c+8)==0
P['name_no_dollar']=lambda c: b'$' not in TDs[col2td[c]]
P['slots>=8']     = lambda c: slots(c)>=8
P['slots>=9']     = lambda c: slots(c)>=9

names=list(P)
hits=[]
for r in range(0,6):
    for combo in itertools.combinations(names,r):
        s={c for c in colset if all(P[n](c) for n in combo)}
        if len(s) in (1201,1211):
            hits.append((len(s),combo))
print('=== conjunctions reaching 1201 or 1211 ===')
for n,combo in sorted(hits):
    print(n, ' AND '.join(combo) if combo else '(empty→all)')
print()
print('=== how many combos reach each target ===')
print(collections.Counter(n for n,_ in hits))
print()
print('=== decisive asymmetry test for slots>=9 ===')
for k in range(6,13):
    print('  slots>=%2d -> %d' % (k, len({c for c in colset if slots(c)>=k})))
print()
print('=== 1211 exact decomposition check (mirror R89) ===')
inimg={c for c in colset if indata(dw(c+16))}
over={c for c in colset if dw(c+4)>0x1000}
print('COL %d ; pcd-in-sec %d ; mdisp>0x1000 %d ; pcd-in-sec minus mdisp>0x1000 = %d'
      % (len(colset), len(inimg), len(over), len(inimg-over)))
print('the 3 removed:', [(hex(c),hex(dw(c+4)),TDs[col2td[c]].decode()) for c in sorted(inimg&over)])
