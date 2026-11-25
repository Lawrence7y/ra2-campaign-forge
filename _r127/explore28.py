import bisect,struct
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
T=S['.text']; T_LO=T.VirtualAddress+IB
raw=pe.get_data(T.VirtualAddress,T.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
A=[a for a,m,o in ins]
def show(v,n):
    i=bisect.bisect_left(A,v)
    for j in range(i,i+n): print('   %x: %s %s'%ins[j])
print('=== 0x67fe31 cluster');show(0x67fe20,40)
def gt(va):
    b=pe.get_data(va-IB,16)
    d1,d2,d3=struct.unpack('<IHH',b[:8])
    return '{%08X-%04X-%04X-%s-%s}'%(d1,d2,d3,b[8:10].hex().upper(),b[10:].hex().upper())
for va in (0x7ea6e8,0x7e9ac0,0x7e9ae0,0x7e9b10):
    print(hex(va),gt(va))
