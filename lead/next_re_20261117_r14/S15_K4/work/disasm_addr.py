import sys,pathlib,pefile
from capstone import *
root=pathlib.Path(r'D:\Project\ra2-campaign-forge');exe=root/'ra2youli/gamemd.exe'
pe=pefile.PE(str(exe)); IB=pe.OPTIONAL_HEADER.ImageBase
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
addrs=[int(x,16) for x in sys.argv[1:]]
for a in addrs:
    # guess 256 bytes
    b=pe.get_data(a-IB,256)
    print('\n=== %08X ==='%a)
    for i in md.disasm(b,a):
        print('%08X  %-20s %-8s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str))
        if i.mnemonic=='ret': break
