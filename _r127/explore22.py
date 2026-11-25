import struct,bisect
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
    print(' vt 0x%x col=0x%x'%(vt,col if col else 0))
    if not col or not (RD_LO<=col<RD_HI): return None
    sig,off,cd,ptd,pchd=struct.unpack('<IIIII',rd(col,20))
    print('   col: sig=%d off=%d cd=0x%x ptd=0x%x pchd=0x%x'%(sig,off,cd,ptd,pchd))
    print('   class name:', cstr(ptd+8,200))
    n,arr=u32(pchd+8),u32(pchd+12)
    print('   nbase=%d arr=0x%x'%(n,arr))
    out=[]
    for i in range(min(n,64)):
        bcd=u32(arr+4*i); td=u32(bcd)
        out.append((cstr(td+8,200), i32(bcd+8), i32(bcd+16), u32(bcd+4)))
    for o in out: print('    ',o)
    return out
print('== vtable 0x7e36d4 (static singleton @0x89a29c)'); rtti(0x7e36d4)
print('== vtable 0x7ea564 (TiberianSunClassFactory)'); rtti(0x7ea564)
print('== vtable 0x7f4108 (SwizzleManagerClass)'); rtti(0x7f4108)
