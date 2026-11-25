import struct,json,collections,bisect
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
T=S['.text']; T_LO=T.VirtualAddress+IB
raw=pe.get_data(T.VirtualAddress,T.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
addrs=[a for a,m,o in ins]; idx={a:i for i,(a,m,o) in enumerate(ins)}
def dump(start,n):
    i=idx.get(start)
    if i is None:
        p=bisect.bisect_right(addrs,start)-1
        print('  %x not insn boundary; nearest prev %x'%(start,addrs[p]))
        i=p+1
    for j in range(i,min(len(ins),i+n)): print('   %x: %s %s'%ins[j])
for s in (0x4af6a5,0x4b6575,0x52119e,0x73a456,0x4af856,0x4b6313,0x4db76a,0x42ca7a):
    print('=== site',hex(s)); dump(s,26)
