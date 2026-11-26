import struct, re, json, itertools
import pefile
EXE='ra2bench/gamemd.exe'
data=open(EXE,'rb').read()
pe=pefile.PE(EXE, fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[(s.Name.decode().rstrip('\x00'), s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
def rva2off(rva):
    for nm,va,vs,raw,rs in secs:
        if va<=rva<va+max(vs,rs):
            d=rva-va
            return raw+d if d<rs else None
    return None
def sec_of_rva(rva):
    for nm,va,vs,raw,rs in secs:
        if va<=rva<va+max(vs,rs): return nm
    return None
def dw(va):
    o=rva2off(va-IB)
    if o is None or o+4>len(data): return None
    return struct.unpack_from('<I',data,o)[0]
pat=re.compile(rb'\.\?A[VU][!-~]{1,200}?@@')
strings=[]
for nm,va,vs,raw,rs in secs:
    if nm not in ('.data','.rdata'): continue
    for m in pat.finditer(data[raw:raw+rs]):
        strings.append((IB+va+m.start(), m.group()))
TDs=[(s-8,s) for s,_ in strings if dw(s-8) is not None and dw(s-4)==0 and sec_of_rva(dw(s-8)-IB) in ('.data','.rdata')]
tdset={v for v,_ in TDs}
refs=[]
for nm,va,vs,raw,rs in secs:
    if nm not in ('.data','.rdata'): continue
    blob=data[raw:raw+rs]
    for i in range(len(blob)//4):
        v=struct.unpack_from('<I',blob,i*4)[0]
        if v in tdset: refs.append((IB+va+i*4, v, nm))
cols=[]  # (col_va, td, refsec)
for r,td,nm in refs:
    c=r-12
    if dw(c)==0 and dw(c+12)==td: cols.append((c,td,nm))
colset={c for c,_,_ in cols}
vtrefs=[]  # (vt_va, col)
for nm,va,vs,raw,rs in secs:
    if nm not in ('.data','.rdata'): continue
    blob=data[raw:raw+rs]
    for i in range(len(blob)//4):
        v=struct.unpack_from('<I',blob,i*4)[0]
        if v in colset:
            vt=IB+va+i*4+4
            if dw(vt-4)==v: vtrefs.append((vt,v))
backed={t for _,t in vtrefs}
print('BASE n_col=%d n_col_backed=%d' % (len(colset), len(backed)))
# overlap check: COL windows of 20 bytes overlapping each other?
cs=sorted(colset)
ov=[(a,b) for a,b in zip(cs,cs[1:]) if b-a<20]
print('adjacent COL within 20B:', len(ov), [(hex(a),hex(b)) for a,b in ov][:10])

def rep(name,ncol,nback):
    print('%-46s col=%-5d backed=%-5d %s' % (name,ncol,nback,'<== MATCH' if (ncol,nback)==(1211,1201) else ''))

# variants
def var(name, colfilter, backrule):
    cs2={c for c,td,_ in cols if colfilter(c,td)}
    if backrule=='recompute': bs={t for _,t in vtrefs} & cs2
    else: bs={t for _,t in vtrefs} & cs2
    rep(name, len(cs2), len(bs))

var('base (.data+.rdata)', lambda c,td: True, 'x')
var('COL in .data only', lambda c,td: sec_of_rva(c-IB)=='.data','x')
var('COL in .rdata only', lambda c,td: sec_of_rva(c-IB)=='.rdata','x')
var('refs from .data only', lambda c,td: None, 'x') if False else None
# ref-section restricted
for s in ('.data','.rdata'):
    cs2={c for c,td,nm in cols if nm==s}
    rep('ref-from %s'%s, len(cs2), len({t for _,t in vtrefs}&cs2))
var('+8==0 too', lambda c,td: dw(c+8)==0,'x')
var('+16 nonzero & in sec', lambda c,td: dw(c+16) is not None and sec_of_rva(dw(c+16)-IB) in ('.data','.rdata'),'x')
var('+16==0', lambda c,td: dw(c+16)==0,'x')
var('all 5 dwords in-image-plausible', lambda c,td: all(dw(c+4*i) is not None for i in range(5)),'x')
var('mdisp==0 only', lambda c,td: dw(c+4)==0,'x')
var('td .?AV only', lambda c,td: td is not None and dw(td+8) is not None and True,'x')
# distinct by tuple
seen=set(); u=[]
for c,td,_ in cols:
    k=tuple(dw(c+4*i) for i in range(5))
    if k in seen: continue
    seen.add(k); u.append((c,td))
rep('distinct by 5-dword tuple', len(u), len({t for _,t in u}&backed))
seen=set(); u2=[]
for c,td,_ in cols:
    k=(dw(c+4),dw(c+8),td,dw(c+16))
    if k in seen: continue
    seen.add(k); u2.append((c,td))
rep('distinct by (mdisp,cd,td,pcd)', len(u2), len({t for _,t in u2}&backed))
seen=set(); u3=[]
for c,td,_ in cols:
    if td in seen: continue
    seen.add(td); u3.append((c,td))
rep('distinct by TD (first only)', len(u3), len({t for _,t in u3}&backed))
# unique-TD COL only (COL whose TD appears exactly once)
from collections import Counter
cnt=Counter(td for _,td,_ in cols)
cs4={c for c,td,_ in cols if cnt[td]==1}
rep('only COL whose TD is unique', len(cs4), len(backed&cs4))
# TD referenced by >=2 COL
cs5={c for c,td,_ in cols if cnt[td]>=2}
rep('only COL whose TD shared', len(cs5), len(backed&cs5))
# excluding overlapping-with-previous 20B
overlap_hi={b for a,b in ov}
cs6=colset-overlap_hi
rep('minus overlapping-later COL', len(cs6), len(backed&cs6))
overlap_lo={a for a,b in ov}
cs7=colset-overlap_lo
rep('minus overlapping-earlier COL', len(cs7), len(backed&cs7))
# vt count based
rep('occurrences of vt-4 refs', len(vtrefs), len({t for _,t in vtrefs}))
print('vt refs total', len(vtrefs), 'distinct vt', len({v for v,_ in vtrefs}))
json.dump({'n_col':len(colset),'n_backed':len(backed)}, open('_r140/r140b.json','w'))
