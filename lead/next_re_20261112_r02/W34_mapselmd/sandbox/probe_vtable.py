import struct
from pathlib import Path
d=Path(r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe").read_bytes()
o=0x7E16B0-0x400000
for i in range(0,0x30,4):
    v=struct.unpack_from("<I",d,o+i)[0]
    print(f"+0x{i:02X}: 0x{v:08X}")
