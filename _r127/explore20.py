import bisect,struct,collections
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
RD=S['.rdata']; RD_LO=RD.VirtualAddress+IB; RD_HI=RD_LO+RD.Misc_VirtualSize
T=S['.text']; T_LO=T.VirtualAddress+IB
raw=pe.get_data(T.VirtualAddress,T.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
A=[a for a,m,o in ins]
def rd(va,n): return pe.get_data(va-IB,n)
def u32(va):
    b=rd(va,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
def i32(va):
    b=rd(va,4); return struct.unpack('<i',b)[0] if len(b)==4 else None
def cstr(va,n=200):
    b=rd(va,n); e=b.find(b'\x00'); return (b[:e] if e>=0 else b).decode('latin1')
def colname(vt):
    col=u32(vt-4)
    if col is None or not (RD_LO<=col<RD_HI): return None
    chd=u32(col+16)
    if chd is None or not (RD_LO<=chd<RD_HI): return None
    n,arr=u32(chd+8),u32(chd+12)
    out=[]
    for i in range(min(n or 0,64)):
        bcd=u32(arr+4*i)
        td=u32(bcd)
        out.append({'name':cstr(td+8,200),'mdisp':i32(bcd+8),'vdisp':i32(bcd+16),'ncb':u32(bcd+4)})
    return out
for vt in (0x7ea570,0x7ea564):
    print('vt 0x%x slots='%vt, ' '.join('%x'%(u32(vt+4*i) or 0) for i in range(8)))
    print('  rtti', colname(vt))
print()
for va in (0x4102b0,0x4f68c8,0x5125dc,0x55aa2c):
    i=bisect.bisect_left(A,va)
    print('=== mov edi 10C site %x (func %x)'%(va,A[i]))
    for j in range(i-4,i+22): print('   %x: %s %s'%ins[j])
