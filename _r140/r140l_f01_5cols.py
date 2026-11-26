import struct, re, json, collections
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
def indata(va): return va is not None and sec_of(va-IB) in ('.data','.rdata')
pat=re.compile(rb'\.\?A[VU][!-~]{1,200}?@@')
strings=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        for m in pat.finditer(data[raw:raw+rs]): strings.append((IB+va+m.start(), m.group()))
TDs={s-8:g for s,g in strings if dw(s-8) is not None and dw(s-4)==0 and indata(dw(s-8))}
tdset=set(TDs); colset=set(); col2td={}
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in tdset:
                c=IB+va+i*4-12
                if dw(c)==0 and dw(c+12)==v: colset.add(c); col2td[c]=v
vts=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in colset:
                vt=IB+va+i*4+4
                if dw(vt-4)==v: vts.append((vt,v))
vt_by=collections.defaultdict(list)
for vt,c in vts: vt_by[c].append(vt)
backed=set(vt_by)
mult=collections.Counter(col2td.values())
low={}
for c,t in col2td.items():
    if t not in low or c<low[t]: low[t]=c

print('=== the 5 COLs excluded by mdisp<=0x1000 ===')
for c in sorted(colset):
    if dw(c+4)>0x1000:
        n=TDs[col2td[c]].decode()
        print('COL %s  +4=%#x  +8=%#x  +12=%#x  +16=%s  name=%s' %
              (hex(c),dw(c+4),dw(c+8),dw(c+12),hex(dw(c+16)) if dw(c+16) else 'null',n))
        print('   backed=%s  nvt=%d  td_mult=%d  is_lowest_VA=%s' % (c in backed,len(vt_by.get(c,[])),mult[col2td[c]], c==low.get(col2td[c])))
        print('   +4 in a section? %s  (+4 as VA %s)' % (sec_of(dw(c+4)-IB) if dw(c+4)>=IB else 'below IB', hex(dw(c+4))))
print()
print('=== the 3 with mdisp 0x5518: what is 0x5518? ===')
print('0x5518 =', 0x5518, 'decimal')
# is 0x5518 a pointer? -> 0x5518 < IB so no. Is it a size?
for c in sorted(colset):
    if dw(c+4)==0x5518:
        print(' ', hex(c), TDs[col2td[c]].decode(), 'mult', mult[col2td[c]], 'lowest', c==low.get(col2td[c]))
        print('    all dwords:', [hex(dw(c+4*i)) for i in range(5)])
        for vt in vt_by.get(c,[])[:2]:
            print('    vt', hex(vt), 'slots0..7:', [hex(dw(vt+4*j)) if dw(vt+4*j) else None for j in range(8)])
print()
print('=== is 0x5518 the max object size / a .data offset? ===')
print('0x5518 vs .data RVA range 0x412000..0x779be4 : no')
print()
print('=== 2 unbacked COLs: are their +4 a pointer into .data? ===')
for c in (0x80f060,0x80f0a0):
    v=dw(c+4)
    print(' COL %s +4=%s sec=%s  +4-IB RVA=%s' % (hex(c),hex(v),sec_of(v-IB),hex(v-IB)))
    # maybe this is a "pVirtualBaseTable"? print what's at that address
    print('   dwords at +4:', [hex(dw(v+4*i)) for i in range(4)])
    print('   is +4 == COL-0x18?', hex(v)==hex(c-0x18), ' COL-0x18=',hex(c-0x18))
print()
print('=== decisive: 1211 = |backed & mdisp<=0x1000| = |backed| - 3 ? ===')
b3={c for c in backed if dw(c+4)>0x1000}
print('backed=%d  backed with mdisp>0x1000=%d -> %d' % (len(backed),len(b3),len(backed)-len(b3)))
print('those:', [(hex(c),TDs[col2td[c]].decode()) for c in sorted(b3)])
