from pathlib import Path
import re
d=Path(r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe").read_bytes()
base=0x831240
o=base-0x400000
chunk=d[o:o+0x80]
print(chunk.hex(" "))
for m in re.finditer(rb"[ -~]{3,}",chunk):
    print(hex(base+m.start()), m.group())
