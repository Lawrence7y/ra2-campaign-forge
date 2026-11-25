import struct
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
T=[s for s in pe.sections if s.Name.rstrip(b'\x00')==b'.text'][0]
T_LO=T.VirtualAddress+IB
raw=pe.get_data(T.VirtualAddress,T.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
def dump(start,n,back=0):
    lo=start-IB-back
    ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw[lo:lo+ (back+n)*8], start-back)]
    for a,m,o in ins[:n+back]:
        print('   %x: %s %s'%(a,m,o))
for s in (0x4b6560,0x42ca60,0x69ed90):
    print('=== around',hex(s))
    dump(s,40)
