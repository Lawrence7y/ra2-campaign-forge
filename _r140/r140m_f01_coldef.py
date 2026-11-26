import struct, re, json, collections, itertools
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
lowset=set(low.values())
print('COL=%d backed=%d' % (len(colset),len(backed)))

print()
print('=== A. structural unique-ness of the 2 suspects ===')
pcd0=[c for c in colset if dw(c+16)==0]
print('COL with dword[+16]==0 (no pClassDescriptor): %d -> %s' % (len(pcd0),[(hex(c),TDs[col2td[c]].decode()) for c in sorted(pcd0)]))
selfrel=[c for c in colset if dw(c+4)==c-0x18]
print('COL with dword[+4]==COL-0x18 (self-relative ptr): %d -> %s' % (len(selfrel),[(hex(c),TDs[col2td[c]].decode()) for c in sorted(selfrel)]))
notback=colset-backed
print('COL not pointed back by any vtable: %d' % len(notback))
print('THREE-WAY identity of the suspect set: pcd0==selfrel==notback ?', set(pcd0)==set(selfrel)==set(notback))
COLREAL=colset-set(pcd0)
print('=> COL (structural definition, requires pCD!=0 AND |backed|>0): %d' % len(COLREAL))
print('   backed within COLREAL: %d' % len(set(backed)&COLREAL))
print('   distinct TD in COLREAL: %d' % len({col2td[c] for c in COLREAL}))
print('   mdisp==0 within COLREAL: %d' % sum(1 for c in COLREAL if dw(c+4)==0))

print()
print('=== B. verify the two 1211 mechanisms exactly ===')
A={c for c in backed if dw(c+4)<=0x1000}
print('(a) backed & mdisp<=0x1000 : %d' % len(A))
notAU={c for c in colset if not TDs[col2td[c]].startswith(b'.?AU')}
onevt={c for c in colset if len(vt_by.get(c,[]))==1}
B2=notAU&onevt
print('(b) not_AU & one_vt (no numeric threshold) : %d' % len(B2))
print('    A and B2 same set?', A==B2, ' |A-B2|=',len(A-B2),' |B2-A|=',len(B2-A))
if A!=B2:
    print('    A-B2:', [(hex(c),TDs[col2td[c]].decode()) for c in sorted(A-B2)])
    print('    B2-A:', [(hex(c),TDs[col2td[c]].decode()) for c in sorted(B2-A)])

print()
print('=== C. hunt 1201 = 1214 - 13 : enumerate natural size-13 subsets ===')
def show(n,s): print('   %-52s %d %s' % (n,len(s),'<<<< 13!' if len(s)==13 else ''))
show('COL whose TD has >=2 COLs', {c for c in colset if mult[col2td[c]]>=2})
show('COL not lowest-VA for its TD', colset-lowset)
show('COL with 2 vtables', {c for c in colset if len(vt_by.get(c,[]))>=2})
show('TD with 2 COLs', {c for c in colset if mult[col2td[c]]==2})
show('AU side', {c for c in colset if TDs[col2td[c]].startswith(b'.?AU')})
show('COL +4 in {0x4,0x8,0xc}', {c for c in colset if dw(c+4) in (4,8,12)})
show('COL +4==0x5518', {c for c in colset if dw(c+4)==0x5518})
show('COL whose vt slot0 == that of MouseClass vt', set())
# what pair-count reproduces 1201 exactly and is threshold-free?
starts=set()
for line in open('_r140/obj_starts.txt'): starts.add(int(line.strip(),16))
def nslot(c):
    return max([sum(1 for j in range(64) if dw(vt+4*j) in starts) for vt in vt_by.get(c,[])] or [0])
for k in range(0,14):
    s={c for c in colset if nslot(c)>=k}
    print('   nslot(objdump-start)>=%2d : %d %s' % (k,len(s),'  <<< 1201' if len(s)==1201 else ''))
json.dump({'col':len(colset),'colreal':len(COLREAL),'backed':len(backed)},open('_r140/r140m.json','w'))
