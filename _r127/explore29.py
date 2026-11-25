import struct
import pefile
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
def rd(va,n): return pe.get_data(va-IB,n)
def u32(va):
    b=rd(va,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
def i32(va):
    b=rd(va,4); return struct.unpack('<i',b)[0] if len(b)==4 else None
def cstr(va,n=200):
    b=rd(va,n); e=b.find(b'\x00'); return (b[:e] if e>=0 else b).decode('latin1')
RDATA=[s for s in pe.sections if s.Name.rstrip(b'\x00')==b'.rdata'][0]
RD_LO=RDATA.VirtualAddress+IB
for vt in (0x7e2a50,0x7ea8a0,0x7eab58):
    col=u32(vt-4); pchd=u32(col+16); n,arr=u32(pchd+8),u32(pchd+12)
    print('vt=0x%x class=%s nbase=%d'%(vt,cstr(u32(col+12)+8),n))
    for i in range(n):
        bcd=u32(arr+4*i); td=u32(bcd)
        print('  [%d] mdisp=%4d ncb=%d %s'%(i,i32(bcd+8),u32(bcd+4),cstr(td+8,200)))
    print()
