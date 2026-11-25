import bisect
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
T=S['.text']; T_LO=T.VirtualAddress+IB
raw=pe.get_data(T.VirtualAddress,T.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
A=[a for a,m,o in ins]
for lo,hi in ((0x521160,0x5211b0),(0x521de0,0x521e40),(0x42ca40,0x42ca80)):
    print('=== %x..%x'%(lo,hi))
    i=bisect.bisect_left(A,lo)
    while i<len(ins) and ins[i][0]<hi:
        print('   %x: %s %s'%ins[i]); i+=1
