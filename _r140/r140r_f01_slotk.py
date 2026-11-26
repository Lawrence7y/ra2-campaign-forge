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
vts=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in COL:
                vt=IB+va+i*4+4
                if dw(vt-4)==v: vts.append((vt,v))
vt_by=collections.defaultdict(list)
for vt,c in vts: vt_by[c].append(vt)
A=1
def chk(n,c):
    global A
    print('  %s %-64s' % ('PASS' if c else 'FAIL', n)); assert c, n; A+=1
print('=== 1201 family: #COL whose vtable has >= k slots in .text (cap 64) ===')
seq={}
for k in range(0,15):
    s={c for c in COL if any(sum(1 for j in range(64) if intext(dw(vt+4*j)))>=k for vt in vt_by.get(c,[]))}
    seq[k]=len(s)
    print('   k>=%2d : %d %s' % (k,len(s),'  <<< 1201' if len(s)==1201 else ''))
print()
print('  full sequence k=0..14:', [seq[k] for k in range(15)])
diffs=[seq[k]-seq[k+1] for k in range(14)]
print('  per-step drops        :', diffs)
print()
chk('there is NO gap in the neighbourhood of the 1201 hits (no jump>40)',
    max(abs(d) for d in diffs)<=40)
chk('1201 is reached at k=8 and k=9 only (a 2-wide plateau, not a structural edge)',
    seq[8]==1201 and seq[9]==1201 and seq[7]!=1201 and seq[10]!=1201)
print()
print('=== the same family computed against the objdump start set (finer) ===')
starts=set()
for line in open('_r140/obj_starts.txt'): starts.add(int(line.strip(),16))
seq2={}
for k in range(0,10):
    s={c for c in COL if any(sum(1 for j in range(64) if dw(vt+4*j) in starts)>=k for vt in vt_by.get(c,[]))}
    seq2[k]=len(s)
print('   k=0..9:', [seq2[k] for k in range(10)])
chk('with the objdump start set the 1201 point MOVES to 1200 (ruler-dependent, not structural)',
    [seq2[k] for k in range(10)]==[1214,1214,1213,1212,1209,1208,1206,1206,1200,1200])
print()
print('=== R89 says 1211 came from a mdisp<=0x1000 threshold: confirm the threshold is arbitrary ===')
mds=sorted(dw(c+4) for c in COL)
print('  sorted distinct mdisp values:', sorted(set(mds)))
print('  counts beyond 0x2c:', collections.Counter(v for v in mds if v>0x2c))
chk('the <=0x1000 cut removes exactly 3 (three 0x5518) and no value lies between 0x6c0 and 0x5518',
    len([v for v in mds if 0x6c0<v<0x5518])==0)
print('  => any threshold T with 0x5518>T>=0x6c0 gives 1213; T>=0x5518 & T<0x5518 no;')
for T in (0x6c0,0x6c1,0x2000,0x5517,0x5518,0x5519,0x1000,0xffffff):
    print('     T=%#08x -> %d' % (T,len([v for v in mds if v<=T])))
print('TOTAL ASSERTIONS: %d PASS' % (A-1))
json.dump({'seq':seq,'seq2':seq2,'diffs':diffs}, open('_r140/r140r.json','w'), indent=1)
