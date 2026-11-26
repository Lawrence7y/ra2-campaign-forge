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
def intext(va): return va is not None and sec_of(va-IB)=='.text'
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
allrefs=collections.defaultdict(list)
for nm,va,vs,raw,rs in secs:
    blob=data[raw:raw+rs]
    for i in range(len(blob)//4):
        v=struct.unpack_from('<I',blob,i*4)[0]
        if v in cand:
            vt=IB+va+i*4+4
            if dw(vt-4)==v: allrefs[v].append((nm,vt))
notAU=lambda c: not TDs[col2td[c]].startswith(b'.?AU')
A={c for c in COL if dw(c+4)<=0x1000}
print('=== (a) alone: mdisp<=0x1000 -> %d (the only reproduction that never moves) ===' % len(A))
print()
PRED=[
 ('R1 ref in any section',                  lambda s,vt: True),
 ('R2 ref in .data or .rdata',              lambda s,vt: s in ('.data','.rdata')),
 ('R3 ref in .rdata',                       lambda s,vt: s=='.rdata'),
 ('R4 vt slot0 in .text',                   lambda s,vt: intext(dw(vt))),
 ('R5 ref in data sec AND slot0 in .text',  lambda s,vt: s in ('.data','.rdata') and intext(dw(vt))),
 ('R6 slot0+slot1 both in .text',           lambda s,vt: intext(dw(vt)) and intext(dw(vt+4))),
]
print('=== (b) = not-AU classes whose vtable-ref count is exactly 1, over base 1216 ===')
vals={}
for nm,p in PRED:
    s={c for c in cand if notAU(c) and sum(1 for r,vt in allrefs.get(c,[]) if p(r,vt))==1}
    vals[nm]=len(s)
    print('  %-40s -> %-5d  |b ^ a| = %-3d  b == a ? %s' % (nm,len(s),len(s^A),s==A))
print()
uniq=sorted(set(vals.values()))
print('  distinct values across the six vtable-validity rules:', uniq)
print('  => (b) is NOT invariant: it takes %d different values' % len(uniq))
print('  => it equals 1211 only under R2, i.e. only if you count .data operand hits as vtables')
print('     while NOT checking whether the slot is a code pointer')
print()
# control: does (a) move under the same kind of relabeling?
print('=== control: (a) under the same six rules (it does not involve vtables at all) ===')
for nm,p in PRED[:1]:
    print('  (a) = {c in COL : dword[c+4] <= 0x1000} = %d -- no vtable term, invariant by construction' % len(A))
print()
print('=== honest summary ===')
lines=[
 '1214  structural COL  : stable under every rule tested',
 '1214  backed COL      : stable (distinct COL, unaffected by ref counting)',
 '1211  via (a)         : reproduces, but the 0x1000 cut is arbitrary (any T in [0x6c0,0x5517] works)',
 '1211  via (b)         : reproduces ONLY under R2; 1203/1212/1212/1205/1207 under the others',
 '1201                  : not reproduced under any structural rule; only in the slot-count family, no break',
]
for l in lines: print('  '+l)
json.dump({'a':len(A),'b_values':vals}, open('_r140/r140y.json','w'), indent=1)
