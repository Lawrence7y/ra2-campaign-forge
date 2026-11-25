import struct,collections
import pefile
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
RD=S['.rdata']; RD_LO=RD.VirtualAddress+IB
def rd(va,n): return pe.get_data(va-IB,n)
def u32(va):
    b=rd(va,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
def i32(va):
    b=rd(va,4); return struct.unpack('<i',b)[0] if len(b)==4 else None
def cstr(va,n=200):
    b=rd(va,n); e=b.find(b'\x00'); return (b[:e] if e>=0 else b).decode('latin1')
def gt(b):
    d1,d2,d3=struct.unpack('<IHH',b[:8])
    return '{%08X-%04X-%04X-%s-%s}'%(d1,d2,d3,b[8:10].hex().upper(),b[10:].hex().upper())
def bases(col):
    pchd=u32(col+16)
    n,arr=u32(pchd+8),u32(pchd+12)
    out=[]
    for i in range(min(n,64)):
        bcd=u32(arr+4*i); td=u32(bcd)
        out.append((cstr(td+8,200), i32(bcd+8)))
    return out
for col in (0x80b730,0x7fbc18,0x8023b8):
    vt=u32(col+4)
    print('col 0x%x vt=0x%x classname=%s'%(col,vt,cstr(u32(col+12)+8)))
    print('  bases:',bases(col))
    for k in range(-0x20,0x10,4):
        print('    vt%+d: %08x'%(k,u32(vt+k) or 0))
