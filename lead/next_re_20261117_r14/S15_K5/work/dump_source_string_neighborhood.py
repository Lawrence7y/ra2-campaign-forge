from pathlib import Path
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pe_common import read_va
for va in [0x842BF8,0x820E44]:
    b=read_va(va-0x80,0x100)
    s=''.join(chr(c) if 32<=c<127 else '.' for c in b)
    print(f'===== around {va:08X} =====')
    for i in range(0,len(b),16):
        print(f'{va-0x80+i:08X}  {b[i:i+16].hex(" ")}  {s[i:i+16]}')
