"""Find writes to global 0x8871E0 and 0xA8ED84 frame counter (byte-level capstone)."""
from pehelp import *
text=[s for s in PE.sections if s.Name.rstrip(b'\0').decode().lower()=='.text'][0]
code=rd(IMAGE_BASE+text.VirtualAddress,text.SizeOfRawData)
for target in [0x8871E0, 0xA8ED84]:
    print('=== references to global 0x%X ==='%target)
    pat=struct.pack('<I',target)
    n=0
    for i in MD.disasm(code, IMAGE_BASE+text.VirtualAddress):
        # refs appear as memory operands [0x8871E0] (mem.disp) or direct imm
        imms=[o.imm for o in i.operands if o.type==X86_OP_IMM]
        disps=[o.mem.disp for o in i.operands if o.type==X86_OP_MEM]
        if target in imms or target in disps:
            print('  %08X %s %s'%(i.address,i.mnemonic,i.op_str)); n+=1
            if n>25: break
