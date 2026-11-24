import re
from pathlib import Path
d=Path(r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe").read_bytes()
for pat in [rb"(?<![A-Za-z0-9_])GDI\x00", rb"(?<![A-Za-z0-9_])Nod\x00", rb"(?<![A-Za-z0-9_])NOD\x00", rb"(?<![A-Za-z0-9_])Yuri\x00", rb"(?<![A-Za-z0-9_])YURI\x00", rb"(?<![A-Za-z0-9_])Allied\x00", rb"(?<![A-Za-z0-9_])Soviet\x00"]:
    hits=[m.start() for m in re.finditer(pat,d)]
    print(pat, len(hits), [hex(0x400000+h) for h in hits[:20]])
