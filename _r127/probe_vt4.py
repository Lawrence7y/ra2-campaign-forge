import struct
import pefile
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
RD=S['.rdata']; DA=S['.data']; TX=S['.text']
RD_LO=RD.VirtualAddress+IB; RD_HI=RD_LO+RD.Misc_VirtualSize
T_LO=TX.VirtualAddress+IB; T_HI=T_LO+TX.Misc_VirtualSize
def rd(va,n): return pe.get_data(va-IB,n)
def u32(va):
    try: b=rd(va,4)
    except Exception: return None
    return struct.unpack('<I',b)[0] if len(b)==4 else None
def i32(va):
    b=rd(va,4); return struct.unpack('<i',b)[0] if len(b)==4 else None
def cstr(va,n=200):
    b=rd(va,n); e=b.find(b'\x00'); return (b[:e] if e>=0 else b).decode('latin1')
def in_img(v): return v is not None and 0x400000<=v<0xB80000
def rtti(vt):
    col=u32(vt-4)
    if not in_img(col): return None
    ptd=u32(col+12); chd=u32(col+16)
    if not in_img(ptd) or not in_img(chd): return None
    n,arr=u32(chd+8),u32(chd+12)
    if n is None or n>64 or not in_img(arr): return None
    bases=[]
    for i in range(n):
        bcd=u32(arr+4*i)
        if not in_img(bcd): return None
        td=u32(bcd)
        if not in_img(td): return None
        bases.append({'name':cstr(td+8,200),'mdisp':i32(bcd+8)})
    return {'class':cstr(ptd+8,200),'bases':bases}
VT={}
for p in range(RD_LO,RD_HI-4,4):
    r=rtti(p)
    if not r: continue
    if not (r['class'].startswith('.?AV') or r['class'].startswith('.?AU')): continue
    f=u32(p)
    if f is None or not (T_LO<=f<T_HI): continue
    VT[p]=r
print('VT size',len(VT))
print('0x7e36d4 in VT?',0x7e36d4 in VT, VT.get(0x7e36d4))
print('0x7ea564 in VT?',0x7ea564 in VT)
print('0x7f4108 in VT?',0x7f4108 in VT)
