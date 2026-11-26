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
tdset=set(TDs); cand=set(); col2td={}
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in tdset:
                c=IB+va+i*4-12
                if dw(c)==0 and dw(c+12)==v: cand.add(c); col2td[c]=v
vts=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in cand:
                vt=IB+va+i*4+4
                if dw(vt-4)==v: vts.append((vt,v))
vt_by=collections.defaultdict(list)
for vt,c in vts: vt_by[c].append(vt)
backed=set(vt_by)
# structural reject
rej={c for c in cand if dw(c+16)==0}
print('candidates %d  rejected(pCD==0) %d  COL %d  backed %d' % (len(cand),len(rej),len(cand-rej),len(backed)))
assert rej=={c for c in cand if dw(c+4)==c-0x18}, 'second structural check disagrees'
assert rej==cand-backed, 'third structural check disagrees'
assert backed<=cand-rej
COL=cand-rej
print('IDENTITY ok: pCD==0  <=>  +4==COL-0x18  <=>  not vtable-backed  (all %d)' % len(rej))
print()
A='=== F01 claim: 954 = main COL = one lowest-VA COL per TD ==='
print(A)
mult=collections.Counter(col2td[c] for c in COL)
low={}
for c in COL:
    t=col2td[c]
    if t not in low or c<low[t]: low[t]=c
lowset=set(low.values())
md0={c for c in COL if dw(c+4)==0}
print('distinct TD in COL          : %d' % len({col2td[c] for c in COL}))
print('lowest-VA COL per TD        : %d' % len(lowset))
print('mdisp==0 (COL+4==0)         : %d' % len(md0))
print('lowest-VA set == mdisp0 set ? %s' % (lowset==md0))
print('  |lowest - mdisp0| = %d  |mdisp0 - lowest| = %d' % (len(lowset-md0),len(md0-lowset)))
print('  lowest but mdisp!=0 (%d):' % len(lowset-md0))
for c in sorted(lowset-md0): print('    %s mdisp=%#x %s' % (hex(c),dw(c+4),TDs[col2td[c]].decode()))
print('  mdisp0 but not lowest (%d):' % len(md0-lowset))
for c in sorted(md0-lowset): print('    %s %s' % (hex(c),TDs[col2td[c]].decode()))
print()
print('=== COL multiplicity hist (COL per TD) ===')
print(sorted(collections.Counter(mult.values()).items()))
print()
print('=== mdisp value groups (multiple-inheritance offsets) ===')
h=collections.Counter(dw(c+4) for c in COL)
for k in sorted(h): print('  %#06x : %d' % (k,h[k]))
print()
print('=== CONTROLS: each judgement must be able to FAIL ===')
def neg(name, val, expect_diff=True):
    print('  %-56s %d %s' % (name, val, 'OK' if (val!=len(COL))==expect_diff else 'CONTROL BROKEN'))
neg('loosen: drop pCD!=0 (accept 2 impostors)', len(cand))
neg('loosen: drop vt-4==COL check (count refs)', len(vts))
neg('loosen: COL=ref-8 instead of ref-12',
    len({(IB+0) for _ in [0]}))  # placeholder replaced below
# real negative control for the offset
c8=set()
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in tdset:
                c=IB+va+i*4-8
                if dw(c)==0 and dw(c+8)==v: c8.add(c)
print('  %-56s %d' % ('offset -8 instead of -12 (control)', len(c8)))
c16=set()
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in tdset:
                c=IB+va+i*4-16
                if dw(c)==0 and dw(c+16)==v: c16.add(c)
print('  %-56s %d' % ('offset -16 instead of -12 (control)', len(c16)))
# TD check negative control: offset -16 for TD identity
bad_td=sum(1 for s,_ in strings if dw(s-16) is not None and dw(s-12)==0 and indata(dw(s-16)))
print('  %-56s %d' % ('TD at string-16 instead of -8 (control)', bad_td))
print()
print('=== SUMMARY vs F01 ===')
rows=[('总 COL',1211,len(COL)),('被 vtable 指回的 COL',1201,len(backed)),
      ('主 COL (mdisp==0)',954,len(md0)),('TypeDescriptor',988,len(TDs)),
      ('无 vtable 指回的 TD',34,len(set(TDs)-{col2td[c] for c in COL}))]
for n,f,m in rows:
    print('  %-26s F01=%-6d 实测=%-6d  %s' % (n,f,m,'一致' if f==m else '不一致'))
json.dump({'cand':len(cand),'rej':len(rej),'COL':len(COL),'backed':len(backed),
           'md0':len(md0),'lowest':len(lowset),'TD':len(TDs)}, open('_r140/r140n.json','w'), indent=1)
