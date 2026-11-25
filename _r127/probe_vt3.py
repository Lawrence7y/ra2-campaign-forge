import struct
import pefile
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
RD=S['.rdata']; DA=S['.data']; TX=S['.text']
def rd(va,n): return pe.get_data(va-IB,n)
def u32(va):
    try: b=rd(va,4)
    except Exception: return None
    return struct.unpack('<I',b)[0] if len(b)==4 else None
def i32(va):
    b=rd(va,4); return struct.unpack('<i',b)[0] if len(b)==4 else None
def cstr(va,n=120):
    b=rd(va,n); e=b.find(b'\x00'); return (b[:e] if e>=0 else b).decode('latin1')
def in_img(v): return v is not None and 0x400000<=v<0xB80000
def rtti(vt):
    col=u32(vt-4)
    if not in_img(col): return None
    ptd=u32(col+12); chd=u32(col+16)
    if not in_img(ptd) or not in_img(chd): return None
    n,arr=u32(chd+8),u32(chd+12)
    if n is None or n>64 or not in_img(arr): return None
    return {'class':cstr(ptd+8,120)}
# direct: is 0x429270 present in vtable 0x7ea564?
vt=0x7ea564
for k in range(8): print(hex(vt+4*k), hex(u32(vt+4*k) or 0))
print('rtti(0x7ea564)=',rtti(vt))
print('rtti(0x7e36d4)=',rtti(0x7e36d4))
print('rtti(0x7f4108)=',rtti(0x7f4108))
