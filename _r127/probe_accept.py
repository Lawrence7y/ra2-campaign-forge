import struct,bisect
import pefile,capstone
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
        out.append({'name':cstr(td+8,200),'mdisp':i32(bcd+8)})
    return out
TX=S['.text']; T_LO=TX.VirtualAddress+IB
raw=pe.get_data(TX.VirtualAddress,TX.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
A=[a for a,m,o in ins]
def body(v,n):
    i=bisect.bisect_left(A,v)
    for j in range(i,i+n): print('   %x: %s %s'%ins[j])
for vt,label in ((0x7e36d4,'ApplicationClass mdisp0 vtable'),(0x7f4108,'SwizzleManagerClass mdisp0 vtable'),(0x7ea564,'TiberianSunClassFactory')):
    print('===',label,'vt=0x%x rtti=%s'%(vt,rtti(vt)))
print('=== 0x429360 (Application QI) tail'); body(0x4293bc,22)
print('=== 0x87f7e8 content:',hex(u32(0x87f7e8) or 0))
print('    0x87f7e8 rtti:',rtti(u32(0x87f7e8)) if u32(0x87f7e8) and RD_LO<=u32(0x87f7e8)<RD_HI else None)
