"""
S11-K1: dump CLSID candidate region around 0x7E9A30 and find code xrefs.
Also scan for GUIDs by a generic '16-byte aligned GUID followed by data pointers' pattern.
Byte-level, no atlas dependency.
"""
import struct
from pehelp import (EXE, PE, IMAGE_BASE, rd, u32, sections, section_of, in_section,
                    is_code, va2off, disasm, fmt)

OUT = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K1\EVIDENCE\clsid_scan.txt'
lines = []
def P(s=''):
    lines.append(str(s))
    print(s)

def guid_str(raw16):
    a,b,c = struct.unpack('<IHH', raw16[:8])
    rest = raw16[8:16]
    return '%08X-%04X-%04X-%s' % (a,b,c,rest.hex().upper())

# ---- 1. dump the clue region as 16-byte GUIDs ----
P('===== region 0x7E9A00 .. 0x7E9B40 as dwords/GUIDs =====')
base = 0x7E9A00
blob = rd(base, 0x140)
for off in range(0, 0x140, 4):
    va = base + off
    v = struct.unpack_from('<I', blob, off)[0]
    P('%08X: %08X  %s' % (va, v, 'code' if is_code(v) else section_of(v) if v>=IMAGE_BASE else 'imm'))

P('')
P('===== GUID interpretation at each 0x10 boundary =====')
for va in range(0x7E9A20, 0x7E9B00, 0x10):
    raw = rd(va, 16)
    P('%08X: %s' % (va, guid_str(raw)))

# ---- 2. scan .text for absolute references to any address in 0x7E9A20..0x7E9B00 ----
P('')
P('===== .text absolute refs to 0x7E9A20..0x7E9B00 (imm32 in instructions) =====')
txt_lo = IMAGE_BASE + 0x1000
# collect all addresses in region (dword-aligned)
region = list(range(0x7E9A20, 0x7E9B00, 4))
blob_text = rd(txt_lo, 0x3DF38D)
# search raw 4-byte little-endian occurrences
for va_target in region:
    pat = struct.pack('<I', va_target)
    hits = []
    idx = 0
    while True:
        j = blob_text.find(pat, idx)
        if j < 0: break
        hits.append(txt_lo + j)
        idx = j + 1
    if hits:
        P('%08X: hits=%s' % (va_target, ' '.join('%08X'%h for h in hits[:12])))

with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')
print('\nWROTE', OUT)
