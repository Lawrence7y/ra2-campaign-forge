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
COL={c for c in cand if dw(c+16)!=0}
bytd=collections.defaultdict(list)
for c in COL: bytd[col2td[c]].append(c)
A=1
def chk(n,c):
    global A
    print('  %s %-64s' % ('PASS' if c else 'FAIL', n)); assert c, n; A+=1
print('=== is mdisp==0 unique per TD? ===')
cnt0=collections.Counter()
for t,cs in bytd.items():
    cnt0[sum(1 for c in cs if dw(c+4)==0)]+=1
print('  histogram (#mdisp0 COLs per TD -> #TD):', sorted(cnt0.items()))
chk('every one of the 954 TDs has EXACTLY one mdisp==0 COL',
    cnt0.get(1,0)==954 and len([k for k in cnt0 if k!=1])==0)
chk('so 954 = #TD = #mdisp0 COL, two independent counts agree', len(bytd)==954 and len({c for c in COL if dw(c+4)==0})==954)
print()
print('=== is the mdisp==0 COL the highest-VA COL of its TD? ===')
nh=0
for t,cs in bytd.items():
    if len(cs)<2: continue
    m0=[c for c in cs if dw(c+4)==0][0]
    if m0==max(cs): nh+=1
multi=sum(1 for cs in bytd.values() if len(cs)>1)
print('  multi-COL TDs=%d ; mdisp0 COL == highest-VA COL in %d of them' % (multi,nh))
chk('for all multi-COL TDs the mdisp0 COL is the highest-VA one', nh==multi==94)
print()
print('=== concrete example (first multi-COL TD), byte-level ===')
t=min(t for t,cs in bytd.items() if len(cs)>1)
for c in sorted(bytd[t]):
    print('    COL %s mdisp=%#x cd=%#x pTD=%s pCD=%s' % (hex(c),dw(c+4),dw(c+8),hex(dw(c+12)),hex(dw(c+16))))
print('    class:', TDs[t].decode())
print()
print('=== R89 wording check ===')
low={t:min(cs) for t,cs in bytd.items()}; hi={t:max(cs) for t,cs in bytd.items()}
md0={c for c in COL if dw(c+4)==0}
print('  R89: "col_va 954/954 = 该 TD 的最低 VA COL" -> lowest set size %d, one per TD: %s'
      % (len(set(low.values())), len({col2td[c] for c in low.values()})==954))
print('  R89: "与 dword[V-4] 不等 88 条" -> my three candidate numbers:')
vtref=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in COL:
                vt=IB+va+i*4+4
                if dw(vt-4)==v: vtref.append((vt,v))
# per TD: COL(s) that are pointed back by SOME vtable
backed={v for _,v in vtref}
print('      #TD where a non-lowest COL is also vtable-backed:',
      len({col2td[c] for c in COL if c in backed and c!=low[col2td[c]]}))
print('      #COL vtable-backed that are NOT the lowest of their TD:',
      len({c for c in backed if c!=low[col2td[c]]}))
print('      #TD whose highest-VA COL is vtable-backed:',
      len({t for t in hi if hi[t] in backed}))
print('      (none of these is 88; R89 number stays unreproduced)')
print()
print('=== CROSS-FACT consequence for F29 ===')
print('  F01 parenthetical rule  : main COL = one per class, picked as lowest VA')
print('  F29 limits rule         : main table = COL with mdisp==0')
print('  both give 954 ; they are the SAME 954 only if the two rules agree')
print('  they disagree on %d classes -> the two facts name different COL objects' % len([1 for t in bytd if low[t] not in md0]))
chk('the two rules disagree on exactly the 94 multi-COL classes',
    len([1 for t in bytd if low[t] not in md0])==94)
print('TOTAL ASSERTIONS: %d PASS' % (A-1))
json.dump({'td':len(bytd),'md0':len(md0),'multi':multi,'nh':nh,
           'disagree':len([1 for t in bytd if low[t] not in md0])}, open('_r140/r140q.json','w'), indent=1)
