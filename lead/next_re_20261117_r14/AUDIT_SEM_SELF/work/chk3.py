
import pefile, capstone
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe=pefile.PE(EXE,fast_load=True); IMAGE=pe.OPTIONAL_HEADER.ImageBase
for s in pe.sections:
    if s.Name.rstrip(b'\x00')==b'.text': text=s
TB=text.VirtualAddress+IMAGE; TS=text.Misc_VirtualSize
RAW=open(EXE,'rb').read(); tdata=RAW[text.PointerToRawData:text.PointerToRawData+text.SizeOfRawData]
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
sites=[0x4063f5,0x469d99,0x48a3ac,0x5663c3,0x566b96,0x6bf9bc,0x6c17bc,0x6e25be,0x702351,0x74a2d5]
CELL_VT=0x7E4EEC
for s in sites:
    off=s-TB
    found=None; ins=[]
    for x in md.disasm(tdata[off:off+16*120], s):
        ins.append(x)
        if x.mnemonic=='mov' and len(x.operands)==2 and x.operands[0].type==capstone.x86.X86_OP_MEM and x.operands[1].type==capstone.x86.X86_OP_IMM:
            if x.operands[1].imm==CELL_VT:
                found=hex(x.address); break
        if x.mnemonic.startswith('ret'): break
    print(hex(s), '-> CellClass vt write:', found, ' (scanned %d insns)'%len(ins))
