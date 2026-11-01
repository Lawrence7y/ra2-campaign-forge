"""Scan .text for absolute-address references to key globals (direct encodings only)."""
import sys
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\x_ingame_close_20261026')
from common import IMG
import struct, re

d = IMG.read(0x401000, 0x3DF38D)
base = 0x401000

GLOBALS = {
    0xA8EDD8: 'exitstate',
    0xB73550: 'hwnd_global',
    0x887368: 'singleton',
    0x887628: 'unk887628',
    0x887640: 'unk887640',
    0x89F978: 'flag89F978',
    0xA8ED5C: 'flagA8ED5C',
    0xA8EDA0: 'dwordA8EDA0',
}

for ga, name in GLOBALS.items():
    pat = struct.pack('<I', ga)
    hits = [m.start() + base for m in re.finditer(re.escape(pat), d)]
    code_hits = [h for h in hits if base <= h < base + 0x3DF38D]
    print(f'== [{ga:08X}] {name}: {len(code_hits)} direct refs in .text ==')
    for h in code_hits:
        # show 2 bytes before as context and surrounding bytes
        ctx = d[h - base - 3:h - base + 8].hex().upper()
        print(f'  0x{h-3:08X}: ...{ctx}')
    print()
