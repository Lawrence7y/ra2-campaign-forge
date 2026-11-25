import bisect
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
TX=S['.text']; T_LO=TX.VirtualAddress+IB
raw=pe.get_data(TX.VirtualAddress,TX.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
A=[a for a,m,o in ins]
def show(v,n,back=0):
    i=bisect.bisect_left(A,v)-back
    for j in range(i,i+n): print('   %x: %s %s'%ins[j])
print('=== 0x4af6f3..4af720 (010C slot3 call)'); show(0x4af6f3,16)
print('=== 0x73a49a..0x73a510'); show(0x73a49a,26)
