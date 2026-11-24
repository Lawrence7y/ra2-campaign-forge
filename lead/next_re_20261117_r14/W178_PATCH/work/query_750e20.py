"""Check callee 0x750E20 ret convention for 0x6CD8CD P1 design."""
import capstone, pefile
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe=pefile.PE(EXE,fast_load=True); ib=pe.OPTIONAL_HEADER.ImageBase
s=next(x for x in pe.sections if x.Name.decode().rstrip('\x00')=='.text')
data=pe.__data__[s.PointerToRawData:s.PointerToRawData+s.SizeOfRawData]
m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m.detail=True; m.skipdata=True
for va in (0x750E20,):
    ins=list(m.disasm(data[va-(ib+s.VirtualAddress):va-(ib+s.VirtualAddress)+0x800],va))
    rets=[i for i in ins if i.mnemonic in ('ret','retf')]
    print(f"0x{va:X} first 8:")
    for i in ins[:8]: print(f"  {i.address:08X} {i.bytes.hex(' '):<20} {i.mnemonic} {i.op_str}")
    print("  rets:",[(hex(i.address),i.mnemonic,i.op_str) for i in rets[:5]])
