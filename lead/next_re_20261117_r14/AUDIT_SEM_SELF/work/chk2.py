
import pefile, capstone
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe=pefile.PE(EXE,fast_load=True); IMAGE=pe.OPTIONAL_HEADER.ImageBase
for s in pe.sections:
    if s.Name.rstrip(b'\x00')==b'.text': text=s
TB=text.VirtualAddress+IMAGE; TS=text.Misc_VirtualSize
RAW=open(EXE,'rb').read(); tdata=RAW[text.PointerToRawData:text.PointerToRawData+text.SizeOfRawData]
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
def dis(va,n=12):
    off=va-TB
    for x in md.disasm(tdata[off:off+n*8],va):
        print('  %08X  %-20s %s %s'%(x.address,x.bytes.hex(),x.mnemonic,x.op_str))
print('--- around push 0x1c2 @0x4f6334 ---'); dis(0x4f6320,14)
print('--- 0x5b2e10..0x5b2e40 (slot129 & slot130?) ---'); dis(0x5b2e10,12)
