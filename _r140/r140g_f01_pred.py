import struct, re, json
from collections import Counter
import pefile
data=open('ra2bench/gamemd.exe','rb').read(); N=len(data)
pe=pefile.PE('ra2bench/gamemd.exe', fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[(s.Name.decode().rstrip('\x00'), s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
SEC={nm:(va,vs,raw,rs) for nm,va,vs,raw,rs in secs}
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
print('COL=%d vt=%d' % (len(colset), len(vts)))
vt_by_col={}
for vt,c in vts: vt_by_col.setdefault(c,[]).append(vt)

def rep(name, val):
    flag='  <<<<<< MATCH 1201' if val==1201 else ''
    print('%-58s %-6d%s' % (name, val, flag))

# A. backing predicates
for nm_,f in [
  ('backed by any vt', lambda vt: True),
  ('vt slot0 in .text', lambda vt: in_text(dw(vt))),
  ('vt slot0 in image sec', lambda vt: dw(vt) is not None and sec_of(dw(vt)-IB)!='.text'),
  ('vt has >=5 slots', lambda vt: all(dw(vt+4*i) is not None for i in range(5))),
  ('vt slot0 nonzero', lambda vt: dw(vt) not in (None,0)),
]:
    s={c for c,vl in vt_by_col.items() if any(f(vt) for vt in vl)}
    rep('A: COL backed where '+nm_, len(s))
# B. COL-count predicates
def rep2(name, s): rep('B: COL count where '+name, len(s))
rep2('all', colset)
rep2('mdisp<=0x1000', {c for c in colset if dw(c+4)<=0x1000})
rep2('pCD in .data/.rdata', {c for c in colset if dw(c+16) is not None and sec_of(dw(c+16)-IB) in ('.data','.rdata')})
rep2('mdisp<=0x1000 & pCD in sec', {c for c in colset if dw(c+4)<=0x1000 and dw(c+16) is not None and sec_of(dw(c+16)-IB) in ('.data','.rdata')})
rep2('mdisp<=44', {c for c in colset if dw(c+4)<=44})
rep2('mdisp<=0x1000 & backed', {c for c in colset if dw(c+4)<=0x1000} & {t for _,t in vts})
rep2('cd(+8)==0', {c for c in colset if dw(c+8)==0})
rep2('cd==0 & mdisp<=0x1000', {c for c in colset if dw(c+8)==0 and dw(c+4)<=0x1000})
# distinct keys
rep('C: distinct COL', len(colset))
rep('C: distinct TD', len({t for _,t in cols}))
rep('C: distinct pCD', len({dw(c+16) for c in colset}))
rep('C: distinct vt', len({v for v,_ in vts}))
rep('C: distinct (TD,mdisp)', len({(t,dw(c+4)) for c,t in cols}))
rep('C: distinct (TD,pCD)', len({(t,dw(c+16)) for c,t in cols}))
rep('C: distinct TD among backed', len({col2td[c] for c in {t for _,t in vts}}))
# per-COL vt count distribution
cnt=Counter(len(v) for v in vt_by_col.values())
print('vt-per-COL hist:', sorted(cnt.items()))
# show multi-vt COLs
multi=[(hex(c),len(v),TDs[col2td[c]].decode()) for c,v in vt_by_col.items() if len(v)>1]
print('COL with >1 vt:', multi)
# AU-only exclusion effects
au={c for c,t in col2td.items() if TDs[t].startswith(b'.?AU')}
print('AU COL:', [(hex(c),TDs[col2td[c]].decode()) for c in au])
rep('B: exclude AU', len(colset-au))
rep('B: exclude AU & backed', len((colset-au) & {t for _,t in vts}))
json.dump({'col':len(colset),'vt':len(vts)}, open('_r140/r140g.json','w'))
