import struct, re, json
from collections import Counter
import pefile
data=open('ra2bench/gamemd.exe','rb').read()
N=len(data)
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
pat=re.compile(rb'\.\?A[VU][!-~]{1,200}?@@')
strings=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        for m in pat.finditer(data[raw:raw+rs]): strings.append((IB+va+m.start(), m.group()))
TDs={s-8:g for s,g in strings if dw(s-8) is not None and dw(s-4)==0 and sec_of(dw(s-8)-IB) in ('.data','.rdata')}
tdset=set(TDs)
# record each ref's file offset too
refs=[]   # (col_va, td, ref_fileoff)
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in tdset:
                c=IB+va+i*4-12
                if dw(c)==0 and dw(c+12)==v: refs.append((c,v,raw+i*4))
colset={c for c,_,_ in refs}
vtrefs=[]  # (vt_va, col, vt_fileoff)
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in colset:
                vt=IB+va+i*4+4
                if dw(vt-4)==v: vtrefs.append((vt,v,raw+i*4-4))
print('COL',len(colset),'vt',len(vtrefs),'filelen',N,hex(N))
# truncation sweep: count distinct COL backed by vt refs whose vt fileoff < T
vbyc={}
for vt,c,fo in vtrefs: vbyc.setdefault(c,[]).append(fo)
fo_min={c:min(v) for c,v in vbyc.items()}
# also COL-detection depends on ref fileoff; require both discovery and vt under T
cref={}
for c,v,fo in refs: cref.setdefault(c,[]).append(fo)
cd_min={c:min(v) for c,v in cref.items()}
bres=sorted((fo_min[c],c) for c in vbyc)
def count_at(T):
    backed={c for fo,c in bres if fo<T}
    disc={c for c in colset if cd_min[c]<T}
    return len(backed), len(disc)
print('T sweep (looking for 1201/1211):')
found=[]
Ts=[0x480000,0x481000,0x490000,0x495000,0x498000,0x49A000,N,0x411000,0x410000,0x40F000,0x40E000]
for T in Ts:
    b,d=count_at(T); print('  T=%#x backed=%d disc=%d' % (T,b,d))
# find exact T ranges where backed==1201
prev=None
for idx in range(len(bres)):
    T=bres[idx][0]+1
    b,d=count_at(T)
    if b==1201 and prev!=1201:
        print('  FIRST T with backed==1201: %#x (vt fo %#x)' % (T,T-1))
        prev=1201
# exact T for 1211 too
for idx in range(len(bres)):
    T=bres[idx][0]+1
    b,_=count_at(T)
    if b==1211:
        print('  FIRST T with backed==1211: %#x' % (T,)); break
# which COLs are backed at end
print('backed total', len(vbyc))
last13=sorted(bres)[:14]
print('lowest-fo backed COLs:', [(hex(fo),hex(c)) for fo,c in last13])
print('highest-fo backed COLs:', [(hex(fo),hex(c)) for fo,c in sorted(bres)[-14:]])
json.dump({'col':len(colset),'vt':len(vtrefs),'backed':len(vbyc)},open('_r140/r140f.json','w'))
