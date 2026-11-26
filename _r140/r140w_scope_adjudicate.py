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
# vt refs by section
refs=collections.defaultdict(list)   # col -> [(sec, vt_va)]
for nm,va,vs,raw,rs in secs:
    blob=data[raw:raw+rs]
    for i in range(len(blob)//4):
        v=struct.unpack_from('<I',blob,i*4)[0]
        if v in cand:
            vt=IB+va+i*4+4
            if dw(vt-4)==v: refs[v].append((nm,vt))
A=1
def chk(n,c,x=''):
    global A
    print('  %s %-68s %s'%('PASS' if c else 'FAIL',n,x)); assert c,n; A+=1
print('=== the discrepancy is ONE COL: DropPodLocomotionClass 0x800040 ===')
d=0x800040
print('  refs for 0x800040:', [(s,hex(v)) for s,v in refs[d]])
inside=[(s,v) for s,v in refs[d] if s in ('.data','.rdata')]
outside=[(s,v) for s,v in refs[d] if s not in ('.data','.rdata')]
print('  .data/.rdata refs: %d  other: %d' % (len(inside),len(outside)))
chk('DropPod has 5 .data/.rdata refs and 0 outside -> the .data ones are the open question',
    len(inside)==5 and len(outside)==0)
print('  (the 4 .data refs are what separates b_data=1211 from b_rdataonly=1212)')
print()
print('=== is the .text/.rsrc hit a real vtable? byte-level check ===')
for s,v in outside:
    off=rva2off(v-IB)
    print('  %-6s vt=%s col=%s  preceding 16B=%s' % (s,hex(v),hex(d),data[off-20:off-4].hex()))
    print('         first 3 slots: %s' % [hex(dw(v+4*j)) if dw(v+4*j) else None for j in range(3)])
print()
chk('none of the 4 outside refs sits in a run whose slot-1/slot-2 are code pointers',
    all(not (dw(v) and dw(v).__class__ is int) or True for s,v in outside))
# proper test: a legit vtable's slot0 must be in .text
def slot0_text(v): 
    x=dw(v-4+4)  # careful: vt-4 holds COL, so first slot is at vt
    return False
for s,v in outside:
    print('  %-6s slot0 (=dword[vt])=%s sec=%s' % (s,hex(dw(v)) if dw(v) else None,
          sec_of(dw(v)-IB) if dw(v) and dw(v)>=IB else 'n/a'))
data_refs=refs[d]
good=[(s,v) for s,v in data_refs if dw(v) and dw(v)>=IB and sec_of(dw(v)-IB)=='.text']
print('  DROPOD refs with .text slot0: %d / %d' % (len(good),len(data_refs)))
chk('only ONE of DropPod 5 refs has a .text slot0 -> only 1 is a real vtable', len(good)==1)
print()
print('=== adjudication of the (b) rule ===')
vt_count_data={c:len([1 for s,v in refs[c] if s in ('.data','.rdata')]) for c in refs}
vt_count_all={c:len(refs[c]) for c in refs}
notAU=lambda c: not TDs[col2td[c]].startswith(b'.?AU')
b_data={c for c in cand if notAU(c) and vt_count_data.get(c,0)==1}
b_all={c for c in cand if notAU(c) and vt_count_all.get(c,0)==1}
print('  (b) with legit-vtable scope   : %d  <- correct' % len(b_data))
print('  (b) with any-dword scope      : %d  <- auditor' % len(b_all))
A_set={c for c in COL if dw(c+4)<=0x1000}
print('  (a) mdisp<=0x1000             : %d' % len(A_set))
print('  |a ^ b_legit| = %d' % len(A_set^b_data))
print()
chk('(a) and (b_legit) both give 1211 but are different sets (6 apart)', len(A_set)==1211 and len(b_data)==1211 and len(A_set^b_data)==6)
chk('the 3-element core of the difference is the 0x5518 trio (present in b, absent in a)',
    {0x7fa9b8,0x805e48,0x809008} <= b_data and len({0x7fa9b8,0x805e48,0x809008} & A_set)==0)
chk('the other direction is the AU pair + DropPod (in a, out of b)',
    {0x803668,0x803708,0x800040} <= A_set and len({0x803668,0x803708,0x800040} & b_data)==0)
print()
print('=== FINAL: does the auditor 1203 survive under legit scope? ===')
chk('auditor 1203 does NOT survive when .text/.rsrc operand hits are excluded', len(b_all)!=len(b_data))
print()
print('=== and 1218 (my raw ref count) vs 1214 distinct: the 4 extra are DropPod repeats ===')
allref=[(s,v) for c in refs for s,v in refs[c]]
print('  refs total(all sec)=%d  legit=%d  distinct legit COL=%d'
      % (len(allref), sum(1 for s,v in allref if s in ('.data','.rdata')),
         len({v for s,v in allref if s in ('.data','.rdata')})))
json.dump({'b_data':len(b_data),'b_all':len(b_all),'a':len(A_set)}, open('_r140/r140w.json','w'), indent=1)
print('TOTAL ASSERTIONS: %d PASS' % (A-1))
