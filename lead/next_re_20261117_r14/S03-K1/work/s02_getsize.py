"""S03-K1 step2: dump vtable slot targets + find B8 imm32 C3 (GetSize) functions.
Channel B = raw byte pattern scan over .text (skipdata=True), independent of atlas.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from re_lib import *

b = Bin()
out = []

def head(va, n=16):
    return b.read(va, n).hex()

def is_getsize(va):
    raw = b.read(va, 6)
    if raw[0] == 0xB8 and raw[5] == 0xC3:
        return int.from_bytes(raw[1:5], 'little')
    return None

vts = {
    'FileClass': (0x7F08BC, 41),
    'RawFileClass': (0x7F0904, 23),
    'BufferIOFileClass': (0x7E3A2C, 17),
    'CDFileClass': (0x7E1668, 35),
    'CCFileClass': (0x7E16B0, 17),
    'MixFileClass': (0x7EDF50, 1),
}
for name, (vft, n) in vts.items():
    out.append(f"\n=== {name} vft={vft:08X} ===")
    for k in range(n):
        val = b.u32(vft+4*k)
        gs = is_getsize(val)
        tag = f"  GETSIZE imm={gs:08X}" if gs is not None else ""
        out.append(f"  v[{k:2d}] +0x{4*k:02X} = {val:08X}  bytes={head(val,8)}{tag}")

out.append("\n=== all B8 imm32 C3 in .text (byte scan) ===")
t = b.sec('.text')
buf = b.data[t['raw']:t['raw']+t['rawsize']]
imm_map = {}
for i in range(len(buf)-5):
    if buf[i] == 0xB8 and buf[i+5] == 0xC3:
        va = t['va'] + i
        imm = int.from_bytes(buf[i+1:i+5], 'little')
        imm_map.setdefault(imm, []).append(va)
out.append(f"total B8 imm32 C3 sequences: {sum(len(v) for v in imm_map.values())} across {len(imm_map)} distinct imm")
for imm in sorted(imm_map):
    if 0x10 <= imm <= 0x1000 and (imm & (imm-1)) == 0:
        out.append(f"  imm={imm:08X} count={len(imm_map[imm])} sites=" + " ".join(f"{v:08X}" for v in imm_map[imm][:40]))

text = "\n".join(out)
open(os.path.join(os.path.dirname(__file__), '..', 'EVIDENCE', 'E02_vtables_getsize.txt'), 'w', encoding='utf-8').write(text)
print(text)
