import struct,bisect
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
RD=S['.rdata']; RD_LO=RD.VirtualAddress+IB
def rd(va,n): return pe.get_data(va-IB,n)
def u32(va):
    b=rd(va,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
def cstr(va,n=120):
    b=rd(va,n); e=b.find(b'\x00'); return (b[:e] if e>=0 else b).decode('latin1')
print('rdata around 0x7e36a0..0x7e3720')
for va in range(0x7e36a0,0x7e3720,4):
    v=u32(va); tail=rd(va,4)
    print('  %x: %08x  %s'%(va,v, tail if all(32<=c<127 or c==0 for c in tail) else ''))
T=S['.text']; T_LO=T.VirtualAddress+IB
raw=pe.get_data(T.VirtualAddress,T.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
A=[a for a,m,o in ins]
def show(v,n):
    i=bisect.bisect_left(A,v)
    for j in range(i,i+n): print('   %x: %s %s'%ins[j])
print('=== 0x429370 (second 0x7e36c0 site)'); show(0x429360,60)
print('=== 0x4f6920 (third)'); show(0x4f6900,30)
print('=== refs to 0x89a29c'); 
for a,m,o in ins:
    if '0x89a29c' in o: print('   %x: %s %s'%(a,m,o))
