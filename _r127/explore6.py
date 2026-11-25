import struct
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
T=S['.text']; T_LO=T.VirtualAddress+IB
raw=pe.get_data(T.VirtualAddress,T.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
idx={a:i for i,(a,m,o) in enumerate(ins)}
def dump(start,n=60):
    i=idx.get(start)
    if i is None:
        print('  %x not aligned'%start); return
    for j in range(i,min(len(ins),i+n)):
        print('   %x: %s %s'%ins[j])
print('=== 0x429200');dump(0x429200,90)
print('=== 0x4293f0');dump(0x4293f0,60)
print('=== 0x429520');dump(0x429520,50)
print('=== 0x4f6900');dump(0x4f6900,40)
print('=== 0x6cf420');dump(0x6cf420,50)
