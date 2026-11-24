from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
d=Path(r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe").read_bytes()
md=Cs(CS_ARCH_X86,CS_MODE_32)
for i in md.disasm(d[0xA1E5B:0xA1F60],0x4A1E5B):
    print(f"0x{i.address:08X}  {i.bytes.hex(' '):<24}  {i.mnemonic} {i.op_str}")
print("--- 0x4A1FB0 ---")
for i in md.disasm(d[0xA1FB0:0xA2010],0x4A1FB0):
    print(f"0x{i.address:08X}  {i.bytes.hex(' '):<24}  {i.mnemonic} {i.op_str}")
