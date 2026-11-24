"""Q3: cell/occupancy table update complexity.
Scan for references to 0x87F924 (MapClass cell table slot per task), 0x87F7E8 (MapClass singleton),
and count writes to [reg+0xE4]/[reg+0xE8] (CellClass footprint fields per task).
All byte-level capstone skipdata=True."""
from pehelp import *
text=[s for s in PE.sections if s.Name.rstrip(b'\0').decode().lower()=='.text'][0]
code=rd(IMAGE_BASE+text.VirtualAddress,text.SizeOfRawData)
ins_list=list(MD.disasm(code, IMAGE_BASE+text.VirtualAddress))
print('total .text instrs (skipdata)=%d'%len(ins_list))
# refs to globals
for target in [0x87F924,0x87F7E8,0x87E8B8]:
    print('=== refs to global 0x%X ==='%target)
    n=0
    for i in ins_list:
        if i.id==0: continue  # SKIPDATA pseudo-instruction
        disps=[o.mem.disp for o in i.operands if o.type==X86_OP_MEM]
        imms=[o.imm for o in i.operands if o.type==X86_OP_IMM]
        if target in disps or target in imms:
            print('  %08X %s %s'%(i.address,i.mnemonic,i.op_str)); n+=1
            if n>30: break
    if n==0: print('  (none)')
# writes to [reg+0xE4] / [reg+0xE8]
for off in [0xE4,0xE8]:
    hits=[]
    for i in ins_list:
        if i.id==0: continue
        if i.mnemonic in ('mov','inc','dec','add','sub','and','or') and i.operands:
            dst=i.operands[0]
            if dst.type==X86_OP_MEM and dst.mem.disp==off:
                hits.append(i)
    print('writes/ops to [reg+0x%X]: %d'%(off,len(hits)))
    for h in hits[:15]: print('  %08X %s %s'%(h.address,h.mnemonic,h.op_str))
