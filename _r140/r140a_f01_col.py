import sys, struct, json, hashlib, re
import pefile

EXE='ra2bench/gamemd.exe'
data=open(EXE,'rb').read()
pe=pefile.PE(EXE, fast_load=True)
IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    nm=s.Name.decode().rstrip('\x00')
    secs.append((nm, s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))

def sec_of_rva(rva):
    for nm,va,vs,raw,rs in secs:
        end=va+max(vs,rs)
        if va<=rva<end: return nm
    return None

def rva2off(rva):
    for nm,va,vs,raw,rs in secs:
        if va<=rva<va+max(vs,rs):
            d=rva-va
            if d<rs: return raw+d
            return None
    return None

def va2off(va): return rva2off(va-IB)

# readable (on-disk) byte image map: only raw-backed bytes are available
def dword_at_va(va):
    off=va2off(va)
    if off is None or off+4>len(data): return None
    return struct.unpack_from('<I',data,off)[0]

# 1) enumerate .?AV / .?AU name strings in raw-backed data, restricted to .data/.rdata
pat=re.compile(rb'\.\?A[VU][!-~]{1,200}?@@')
strings=[]
for nm,va,vs,raw,rs in secs:
    if nm not in ('.data','.rdata'): continue
    blob=data[raw:raw+rs]
    for m in pat.finditer(blob):
        s=m.group()
        rva=va+m.start()
        strings.append((rva, s))
print('strings raw .?AV/.?AU:', len(strings),
      'AV:', sum(1 for r,s in strings if s.startswith(b'.?AV')), 'AU:', sum(1 for r,s in strings if s.startswith(b'.?AU')))

# TypeDescriptor = string start - 8 ; require +0 dword -> .data/.rdata, +4 == 0
TDs=[]
for rva,s in strings:
    td_va=IB+rva-8
    p0=dword_at_va(td_va)
    p1=dword_at_va(td_va+4)
    if p0 is None or p1 is None: continue
    if p1!=0: continue
    if sec_of_rva(p0-IB) not in ('.data','.rdata'): continue
    TDs.append((td_va, s))
print('TDs:', len(TDs), 'AV:', sum(1 for v,s in TDs if s.startswith(b'.?AV')), 'AU:', sum(1 for v,s in TDs if s.startswith(b'.?AU')))

tdset={v for v,s in TDs}

# 2) scan all readable dwords for TD pointer refs -> COL = ref-12
def scan_dwords(sections):
    refs=[]
    for nm,va,vs,raw,rs in secs:
        if nm not in sections: continue
        blob=data[raw:raw+rs]
        n=len(blob)//4
        for i in range(n):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in tdset:
                refs.append((va+i*4, v))
    return refs

refs=scan_dwords(('.data','.rdata'))
print('TD pointer refs in .data/.rdata:', len(refs))
print('ref sec distribution:', {s:sum(1 for r,v in refs if sec_of_rva(r)==s) for s in ('.data','.rdata')})

cands=[]
for r,td in refs:
    col_va=IB+r-12
    sig=dword_at_va(col_va)
    ptd=dword_at_va(col_va+12)
    if sig==0 and ptd==td:
        cands.append((col_va, td))
print('COL candidates (sig==0 and +12==td):', len(cands))

# also: refs where sig!=0 (rejected)
rej=[1 for r,td in refs if dword_at_va(IB+r-12)!=0]
print('refs rejected by sig!=0:', len(rej))
# refs where sig==0 but +12 != td (should be impossible)
bad=[1 for r,td in refs if dword_at_va(IB+r-12)==0 and dword_at_va(IB+r-12+12)!=td]
print('refs with sig==0 but +12!=td:', len(bad))

# full 5-dword consistency checks
def col_tuple(c):
    return tuple(dword_at_va(c+4*i) for i in range(5))
tups=[col_tuple(c) for c,_ in cands]

# vtable: dword refs to COL VA, vt = ref+4, vt-4==col
colset={c for c,_ in cands}
vts=[]
for nm,va,vs,raw,rs in secs:
    if nm not in ('.data','.rdata'): continue
    blob=data[raw:raw+rs]
    for i in range(len(blob)//4):
        v=struct.unpack_from('<I',blob,i*4)[0]
        if v in colset:
            vt=IB+va+i*4+4
            if dword_at_va(vt-4)==v:
                vts.append((vt,v))
print('vtable refs (vt-4==col):', len(vts), 'distinct vt:', len({v for v,t in vts}), 'distinct col:', len({t for v,t in vts}))

# COL pointed back by some vtable
backed=colset & {t for v,t in vts}
print('distinct COL pointed back:', len(backed), ' COL not pointed back:', len(colset-backed))

# mdisp: MSVC RTTI CompleteObjectLocator layout: sig(0), offset(4), cdOffset(8), pTypeDescriptor(12), pClassDescriptor(16)
mdisp_zero=[c for c,_ in cands if dword_at_va(c+4)==0]
print('COL with dword[+4]==0 (mdisp==0):', len(mdisp_zero))
mdisp_dist={}
for c,_ in cands:
    d=dword_at_va(c+4); mdisp_dist[d]=mdisp_dist.get(d,0)+1
print('mdisp value histogram (top):', sorted(mdisp_dist.items(), key=lambda x:-x[1])[:8])

# TD not referenced by any COL
td_backed={td for c,td in cands}
print('TD with no COL ref:', len(tdset-td_backed))

json.dump({'n_strings':len(strings),'n_td':len(TDs),'n_refs':len(refs),'n_col':len(cands),
           'n_vt':len(vts),'n_col_backed':len(backed),'n_mdisp0':len(mdisp_zero),
           'n_td_unref':len(tdset-td_backed)}, open('_r140/r140a_f01_col.json','w'), indent=1)
