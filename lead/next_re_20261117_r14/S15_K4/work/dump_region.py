import sys,pathlib,pefile
from capstone import *
root=pathlib.Path(r'D:\Project\ra2-campaign-forge');pe=pefile.PE(str(root/'ra2youli/gamemd.exe'));IB=pe.OPTIONAL_HEADER.ImageBase
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
for spec in sys.argv[1:]:
    a,b=spec.split(':');a=int(a,16);b=int(b,16)
    print('\n=== %08X..%08X ==='%(a,b))
    for i in md.disasm(pe.get_data(a-IB,b-a),a):
        print('%08X  %-20s %-8s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str))
