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
vt=0x7E2A50
col=u32(vt-4); pchd=u32(col+16); n,arr=u32(pchd+8),u32(pchd+12)
print('AITriggerTypeClass vt=0x%x nbase=%d'%(vt,n))
for i in range(n):
    bcd=u32(arr+4*i); td=u32(bcd)
    print('  [%d] mdisp=%4d pdisp=%3d vdisp=%3d ncb=%d  %s'%(
        i,i32(bcd+8),i32(bcd+12),i32(bcd+16),u32(bcd+4),cstr(td+8,200)))
