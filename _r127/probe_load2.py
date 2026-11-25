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
for c in (0x4af7eb,0x504063):
    print('=== OleLoadFromStream at',hex(c)); show(c,2,4)
