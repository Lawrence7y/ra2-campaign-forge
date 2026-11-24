from pathlib import Path
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pe_common import read_va
for va in [0x817474,0x817694,0x846574,0x842BF4,0x842BDC,0x842BC4,0x842BAC]:
    b=read_va(va,64)
    s=b.split(b'\x00')[0]
    print(f'{va:08X}: {s!r} first16={b[:16].hex(" ")}')
