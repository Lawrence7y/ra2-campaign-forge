from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
d=Path(r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe").read_bytes()
md=Cs(CS_ARCH_X86,CS_MODE_32)
for i in md.disasm(d[0x25D5C0:0x25D700],0x65D5C0):
    print(f"0x{i.address:08X}  {i.bytes.hex(' '):<24}  {i.mnemonic} {i.op_str}")
