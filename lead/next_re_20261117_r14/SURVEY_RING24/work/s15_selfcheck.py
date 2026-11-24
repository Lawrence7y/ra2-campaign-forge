
import pefile,capstone
from pathlib import Path
ROOT=Path(r'D:\Project\ra2-campaign-forge')
raw=open(ROOT/'ra2youli'/'gamemd.exe','rb').read()
pe=pefile.PE(data=raw,fast_load=True); ib=pe.OPTIONAL_HEADER.ImageBase
s0=pe.sections[0]
code=raw[s0.PointerToRawData:s0.PointerToRawData+s0.Misc_VirtualSize]
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
found=None
for i in md.disasm(code, ib+s0.VirtualAddress):
    if i.address==0x4386AB:
        found=(i.mnemonic,i.op_str,[ (o.type, o.mem.base if o.type==3 else None, o.mem.index if o.type==3 else None, o.mem.disp if o.type==3 else None) for o in i.operands])
        break
    if i.address>0x4386AB: break
print('0x4386AB ->',found)
# also count independent: how many mem ops have op.mem.index != 0
