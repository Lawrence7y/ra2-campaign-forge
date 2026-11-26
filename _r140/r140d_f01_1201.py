import struct, re, json
from collections import Counter
import pefile
data=open('ra2bench/gamemd.exe','rb').read()
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
    if o is None or o+4>len(data): return None
    return struct.unpack_from('<I',data,o)[0]
pat=re.compile(rb'\.\?A[VU][!-~]{1,200}?@@')
strings=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        for m in pat.finditer(data[raw:raw+rs]): strings.append((IB+va+m.start(), m.group()))
TDs={s-8:g for s,g in strings if dw(s-8) is not None and dw(s-4)==0 and sec_of(dw(s-8)-IB) in ('.data','.rdata')}
tdset=set(TDs)
refs=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in tdset: refs.append((IB+va+i*4, v))
cols=[]
for r,td in refs:
    c=r-12
    if dw(c)==0 and dw(c+12)==td: cols.append((c,td))
colset={c for c,_ in cols}; col2td={c:t for c,t in cols}
au_cols={c for c,t in col2td.items() if TDs[t].startswith(b'.?AU')}
av_cols=colset-au_cols
vtrefs=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in colset:
                vt=IB+va+i*4+4
                if dw(vt-4)==v: vtrefs.append((vt,v))
backed={t for _,t in vtrefs}
print('COL %d  AV %d  AU %d' % (len(colset),len(av_cols),len(au_cols)))
print('backed %d = AV %d + AU %d' % (len(backed), len(backed&av_cols), len(backed&au_cols)))
print('not backed:', [(hex(c),TDs[col2td[c]].decode()) for c in colset-backed])
m1000={c for c,_ in cols if dw(c+4)<=0x1000}
print('mdisp<=0x1000: col=%d backed=%d' % (len(m1000), len(m1000&backed)))
print('over-0x1000:', [(hex(c),hex(dw(c+4)),TDs[col2td[c]].decode()) for c,_ in cols if dw(c+4)>0x1000])
# vtable-index based: is the vtable's COL at index0 of some TD's COL-list?
print('COL count by TD multiplicity:', sorted(Counter(Counter(col2td.values()).values()).items()))
# which distinct COLs are "first/lowest VA per TD"
lowest={}
for c,t in col2td.items():
    if t not in lowest or c<lowest[t]: lowest[t]=c
print('distinct TD %d ; lowest-VA COL set %d' % (len(lowest), len(set(lowest.values()))))
# TARGET tests
def rep(n,a,b): print('%-44s col=%-5d backed=%-5d %s' % (n,a,b,'<<< MATCH' if (a,b)==(1211,1201) else ''))
rep('all', len(colset), len(backed))
rep('AV-side only', len(av_cols), len(backed&av_cols))
rep('AV+AU', len(colset), len(backed))
rep('mdisp<=0x1000', len(m1000), len(m1000&backed))
rep('AV-side & mdisp<=0x1000', len(av_cols&m1000), len(backed&av_cols&m1000))
# backed restricted to AV
rep('backed AV-only', len(colset), len(backed&av_cols))
# COL whose vt is in .rdata vs .data
def vt_sec(c):
    for vt,cc in vtrefs:
        if cc==c: return sec_of(vt-IB)
    return None
d={}
for c in colset: d[vt_sec(c)]=d.get(vt_sec(c),0)+1
print('vtable section distribution:', d)
json.dump({'col':len(colset),'av':len(av_cols),'au':len(au_cols),'backed':len(backed),
           'm1000':len(m1000),'td':len(TDs)}, open('_r140/r140d.json','w'))
