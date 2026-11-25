import bisect
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
T=S['.text']; T_LO=T.VirtualAddress+IB
raw=pe.get_data(T.VirtualAddress,T.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
A=[a for a,m,o in ins]
def show(v,n,back=0):
    i=bisect.bisect_left(A,v)-back
    for j in range(i,i+n): print('   %x: %s %s'%ins[j])
print('=== before 52119e');show(0x52119e,1,8)
print('=== 521e29 before');show(0x521e29,1,8)
print('=== 42ca7a before');show(0x42ca7a,1,8)
print('=== 45aeb5 before');show(0x45aeb5,1,10)
