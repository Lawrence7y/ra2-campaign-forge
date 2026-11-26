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

print('=== FALSIFY the >=8 .text-slot match: is there a natural break? ===')
# distribution of .text slot count in first 64 per COL (max over its vts)
cnts=sorted(max(sum(1 for j in range(64) if in_text(dw(vt+4*j))) for vt in vl) for c,vl in vt_by_col.items())
import collections
h=collections.Counter(cnts)
print('hist of max .text-slot count (value: #COL):')
for k in sorted(h): print('   %3d : %d' % (k,h[k]))
# cumulative from top
tot=len(cnts)
print('cumulative: #COL with count>=k')
run=0
for k in sorted(h, reverse=True):
    run+=h[k]
    if 4<=k<=20 or k in (0,1,2,3): print('   >=%2d : %d' % (k,run))

print()
print('=== does 1201 equal "backed minus COL whose vt slot0 not in objdump starts"? ===')
starts=set()
for line in open('_r140/obj_starts.txt'):
    starts.add(int(line.strip(),16))
print('objdump starts:', len(starts))
def slot0_in_starts(c):
    return any(dw(vt) in starts for vt in vt_by_col.get(c,[]))
bad={c for c in vt_by_col if not slot0_in_starts(c)}
print('backed COL with vt slot0 NOT in objdump starts:', len(bad))
print('backed - those:', len(vt_by_col)-len(bad))
s2={c for c in vt_by_col if all(dw(vt) in starts for vt in vt_by_col[c])}
print('backed COL with ALL vts slot0 in starts:', len(s2))
# all slots in starts
def allslots(c):
    for vt in vt_by_col[c]:
        for j in range(4):
            v=dw(vt+4*j)
            if v is None: return False
            if v not in starts: return False
    return True
print('backed with first 4 slots all in starts:', len({c for c in vt_by_col if allslots(c)}))

print()
print('=== mdisp natural break? ===')
md=sorted(dw(c+4) for c in colset)
d=collections.Counter(md)
print('mdisp values sorted:', md)
print('largest gaps:')
for a,b in zip(md,md[1:]):
    if b-a>100: print('   %d -> %d (gap %d)' % (a,b,b-a))
print()
print('=== the 5 COL excluded by mdisp<=0x1000, one is mdisp=1728 ===')
for c in sorted(colset):
    v=dw(c+4)
    if v>44: print('   %s mdisp=%d (%#x) %s' % (hex(c), v, v, TDs[col2td[c]].decode()))
json.dump({'backed':len(vt_by_col)},open('_r140/r140i.json','w'))
