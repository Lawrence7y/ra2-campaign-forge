"""Byte-level scan: find all `mov [reg+0x278], reg32` writes in .text (capstone skipdata=True)."""
from pehelp import *
text=[s for s in PE.sections if s.Name.rstrip(b'\0').decode().lower()=='.text'][0]
code=rd(IMAGE_BASE+text.VirtualAddress,text.SizeOfRawData)
hits=[]
for ins in MD.disasm(code, IMAGE_BASE+text.VirtualAddress):
    if ins.mnemonic=='mov' and len(ins.operands)==2:
        dst,src=ins.operands
        if dst.type==X86_OP_MEM and dst.mem.disp==0x278 and src.type==X86_OP_REG:
            hits.append((ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
print('writes to [reg+0x278] (reg32 src): count=%d'%len(hits))
for h in hits[:100]: print('  %08X  %-20s %s %s'%h)
