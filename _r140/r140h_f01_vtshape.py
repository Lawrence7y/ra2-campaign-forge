import struct, re, json
from collections import Counter
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
pat=re.compile(rb'\.\?A[VU][!-~]{1,200}?@@')
strings=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        for m in pat.finditer(data[raw:raw+rs]): strings.append((IB+va+m.start(), m.group()))
TDs={s-8:g for s,g in strings if dw(s-8) is not None and dw(s-4)==0 and sec_of(dw(s-8)-IB) in ('.data','.rdata')}
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
vt_by_col={}
for vt,c in vts: vt_by_col.setdefault(c,[]).append(vt)
TARGETS={1201,1211}
def rep(n,v):
    m='  <<<< MATCH' if v in TARGETS else ''
    print('%-56s %-6d%s'%(n,v,m))
print('COL=%d vt=%d'%(len(colset),len(vts)))
# vtable shape: first k slots in .text
for k in range(1,9):
    s={c for c,vl in vt_by_col.items() if any(all(in_text(dw(vt+4*j)) for j in range(k)) for vt in vl)}
    rep('first %d slots in .text'%k, len(s))
    s2={c for c in s if dw(c+4)<=0x1000}
    rep('  + mdisp<=0x1000', len(s2))
# slot count in .text >= n
for n in (2,4,8,16,32,46):
    s={c for c,vl in vt_by_col.items() if any(sum(1 for j in range(64) if in_text(dw(vt+4*j)))>=n for vt in vl)}
    rep('>=%d .text slots in first 64'%n, len(s))
# vtable address in .rdata and vt+4k...
# COL multiplicity based
mult=Counter(col2td.values())
for k in (1,2,3,4):
    s={c for c,t in col2td.items() if mult[t]==k}
    rep('COL whose TD has exactly %d COLs'%k, len(s))
rep('COL whose TD is unique (858)', len({c for c,t in col2td.items() if mult[t]==1}))
# lowest-VA COL per TD
low={}
for c,t in col2td.items():
    if t not in low or c<low[t]: low[t]=c
rep('lowest-VA COL per TD', len(set(low.values())))
rep('  & mdisp<=0x1000', len({c for c in set(low.values()) if dw(c+4)<=0x1000}))
# mdisp==0 intersects
rep('mdisp==0 & backed', len({c for c in colset if dw(c+4)==0} & set(vt_by_col)))
# COL whose pCD unique
pcds=Counter(dw(c+16) for c in colset)
rep('COL with unique pCD', sum(1 for c in colset if pcds[dw(c+16)]==1))
rep('distinct pCD (955)', len(pcds))
# name-based
rep('COL name has $', sum(1 for c in colset if b'$' in TDs[col2td[c]]))
rep('COL name has @ (nested)', sum(1 for c in colset if TDs[col2td[c]].count(b'@')>2))
rep('COL name without ! or $', sum(1 for c in colset if b'$' not in TDs[col2td[c]]))
json.dump({'col':len(colset)},open('_r140/r140h.json','w'))
