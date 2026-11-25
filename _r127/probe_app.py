import struct
import pefile
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
RD=S['.rdata']; RD_LO=RD.VirtualAddress+IB; RD_HI=RD_LO+RD.Misc_VirtualSize
def rd(va,n): return pe.get_data(va-IB,n)
def u32(va):
    b=rd(va,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
def i32(va):
    b=rd(va,4); return struct.unpack('<i',b)[0] if len(b)==4 else None
def cstr(va,n=200):
    b=rd(va,n); e=b.find(b'\x00'); return (b[:e] if e>=0 else b).decode('latin1')
def rtti(vt):
    col=u32(vt-4)
    if not col or not (RD_LO<=col<RD_HI): return None
    ptd=u32(col+12); pchd=u32(col+16)
    if not ptd or not (RD_LO<=ptd<RD_HI): return None
    n,arr=u32(pchd+8),u32(pchd+12)
    out=[]
    for i in range(min(n or 0,64)):
        bcd=u32(arr+4*i); td=u32(bcd)
        out.append((cstr(td+8,200), i32(bcd+8)))
    return out
def gt(va):
    b=rd(va,16); d1,d2,d3=struct.unpack('<IHH',b[:8])
    return '{%08X-%04X-%04X-%s-%s}'%(d1,d2,d3,b[8:10].hex().upper(),b[10:].hex().upper())
print('0x89a29c content(=vtable):',hex(u32(0x89a29c) or 0))
print('   rtti:',rtti(u32(0x89a29c)))
print('0x87f7e8 content:',hex(u32(0x87f7e8) or 0))
print('   rtti:',rtti(u32(0x87f7e8)) if u32(0x87f7e8) else None)
print('iid 0x7e36c0 =',gt(0x7e36c0))
print('iid 0x7e9b20 =',gt(0x7e9b20))
print('iid 0x7ea6e8 =',gt(0x7ea6e8))
