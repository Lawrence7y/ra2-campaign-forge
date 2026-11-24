from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
d=Path(r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe").read_bytes()
md=Cs(CS_ARCH_X86,CS_MODE_32)
for i in md.disasm(d[0x125A60:0x125D80],0x525A60):
    s=f"{i.mnemonic} {i.op_str}"
    print(f"0x{i.address:08X}  {i.bytes.hex(' '):<24}  {s}")
