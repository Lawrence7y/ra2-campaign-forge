import struct,json,collections
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
RD=S['.rdata']; RD_LO=RD.VirtualAddress+IB; RD_HI=RD_LO+RD.Misc_VirtualSize
DA=S['.data']; DA_LO=DA.VirtualAddress+IB; DA_HI=DA_LO+DA.Misc_VirtualSize
def rd(va,n): return pe.get_data(va-IB,n)
def u32(va):
    b=rd(va,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
def i32(va):
    b=rd(va,4); return struct.unpack('<i',b)[0] if len(b)==4 else None
def cstr(va,n=192):
    b=rd(va,n); e=b.find(b'\x00'); return (b[:e] if e>=0 else b).decode('latin1')
def bcds(vt):
    col=u32(vt-4)
    if col is None or not (RD_LO<=col<RD_HI): return None
    chd=u32(col+16)
    if chd is None or not (RD_LO<=chd<RD_HI): return None
    n,arr=u32(chd+8),u32(chd+12)
    if n is None or n>64 or arr is None or not (RD_LO<=arr<RD_HI): return None
    out=[]
    for i in range(n):
        bcd=u32(arr+4*i)
        if bcd is None or not (IB<=bcd<0xB80000): return None
        td=u32(bcd)
        if td is None or not (IB<=td<0xB80000): return None
        out.append({'name':cstr(td+8,192),'mdisp':i32(bcd+8),'vdisp':i32(bcd+16)})
    return out
sym=json.load(open('out/reverse/symbols.json',encoding='utf-8'))['classes']
def _va(x): return None if x is None else (x if isinstance(x,int) else int(str(x).strip(),16))
# mdisp distributions for IPersist / IPersistStream in the family
dist=collections.Counter(); pairs=collections.Counter(); nfam=0
for k,v in sym.items():
    vt=_va(v.get('vtable_va'))
    if not vt: continue
    b=bcds(vt)
    if b is None: continue
    names={x['name']:x['mdisp'] for x in b}
    if '.?AUIPersistStream@@' in names:
        nfam+=1
        pairs[(names.get('.?AUIPersist@@'), names['.?AUIPersistStream@@'])]+=1
print('family',nfam,'(mdisp_IPersist, mdisp_IPersistStream) dist:',dict(pairs))
# SwizzleManagerClass RTTI
for k,v in sym.items():
    if k=='SwizzleManagerClass':
        vt=_va(v['vtable_va']); print('SwizzleManager vt=0x%x'%vt)
        for x in bcds(vt): print('   ',x)
