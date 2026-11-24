from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
d=Path(r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe").read_bytes()
md=Cs(CS_ARCH_X86,CS_MODE_32)
print("=== 0x7CAFF4 strupr ===")
for i in md.disasm(d[0x3CAFF4:0x3CB050],0x7CAFF4):
    print(f"0x{i.address:08X}  {i.bytes.hex(' '):<24}  {i.mnemonic} {i.op_str}")
print("=== 0x7B5B30 ===")
for i in md.disasm(d[0x3B5B30:0x3B5B80],0x7B5B30):
    print(f"0x{i.address:08X}  {i.bytes.hex(' '):<24}  {i.mnemonic} {i.op_str}")
