#!/usr/bin/env python3
"""R133 deepseek audit: final cross-checks.
 C10  arithmetic 7 & 0x14
 C11a reader-not-aliased (16 bytes at 0x817bd0)
 C11b formatter order-sensitivity (LE vs BE) on BOTH constants
 C11c entry VA as imm32 -> expect ZERO although rel32 callers exist
 X1   capstone re-decode of each arg3 tail, anchored on the tail's first byte boundary,
      with fresh Cs per site (works around the capstone 5.0.7 skipdata segfault)
"""
import json, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

BIN = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
pe = pefile.PE(BIN, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
IMG = pe.get_memory_mapped_image()
text = next(s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text')
TEXT_VA = IB + text.VirtualAddress
TEXT_SZ = text.SizeOfRawData
blob = bytes(IMG[TEXT_VA - IB: TEXT_VA - IB + TEXT_SZ])
rd = lambda va, n: bytes(IMG[va - IB: va - IB + n])

out = {}

# ---------------- C10 ----------------
s = 7 & 0x14
out['C10'] = {'arg3': 7, 'mask': hex(0x14), 'and': s, 'and_hex': hex(s),
              'zf': s == 0, 'je_taken': s == 0,
              'conclusion': 'je NOT taken -> falls through into if arm at +0x18'}

# ---------------- C11a ----------------
g_c0 = rd(0x817bc0, 16)
g_b0 = rd(0x817bb0, 16)
g_d0 = rd(0x817bd0, 16)

def le(b):
    return '{%08X-%04X-%04X-%s-%s}' % (struct.unpack_from('<I', b, 0)[0],
                                      struct.unpack_from('<H', b, 4)[0],
                                      struct.unpack_from('<H', b, 6)[0],
                                      b[8:10].hex().upper(), b[10:].hex().upper())

def be(b):
    return '{%08X-%04X-%04X-%s-%s}' % (struct.unpack_from('>I', b, 0)[0],
                                      struct.unpack_from('>H', b, 4)[0],
                                      struct.unpack_from('>H', b, 6)[0],
                                      b[8:10].hex().upper(), b[10:].hex().upper())

out['C11a'] = {'0x817bc0': le(g_c0), '0x817bd0': le(g_d0),
               'differ': g_c0 != g_d0, 'pass': g_c0 != g_d0}
out['C11b'] = {}
for nm, g in (('0x817bc0', g_c0), ('0x817bb0', g_b0)):
    out['C11b'][nm] = {'le': le(g), 'be': be(g), 'differ': le(g) != be(g)}

# ---------------- C11c ----------------
def imm32s(val, hay, base):
    pat = struct.pack('<I', val); r = []; i = hay.find(pat)
    while i >= 0:
        r.append(hex(base + i)); i = hay.find(pat, i + 1)
    return r

whole = bytes(IMG)
out['C11c'] = {
    'imm32_0x6bedb0_in_text': imm32s(0x6bedb0, blob, TEXT_VA),
    'imm32_0x6bedb0_in_image': imm32s(0x6bedb0, whole, IB),
    'imm32_0x41c250_in_text': imm32s(0x41c250, blob, TEXT_VA),
    'imm32_0x41c250_in_image': imm32s(0x41c250, whole, IB),
    'note': 'rel32 callers exist (2 and 13) yet imm32 hits are empty -> imm32 scan wrong for callers',
}
# sanity: the IID pointers ARE found by imm32 scan (right tool for pointer tables)
out['C11c_positive'] = {
    'imm32_0x817bc0_in_image': imm32s(0x817bc0, whole, IB),
    'imm32_0x817bb0_in_image': imm32s(0x817bb0, whole, IB),
}

# ---------------- X1: capstone re-decode of each arg3 tail ----------------
obj = json.load(open('/home/t628/projects/ra2-campaign-forge/_r133/sub_deepseek/r133ds2_objdump.json'))
X1 = []
for rec in obj['C9']:
    site = int(rec['site'], 16)
    first = int(rec['tail_first_va'], 16)
    n = site - first
    code = blob[first - TEXT_VA: site - TEXT_VA + 16]     # over-extend to dodge truncation
    md = Cs(CS_ARCH_X86, CS_MODE_32)                       # fresh object: no reuse crash
    dec = [(a, s, m, o) for a, s, m, o in md.disasm(code, first) if a < site]
    contiguous = all(dec[i][0] + dec[i][1] == dec[i + 1][0] for i in range(len(dec) - 1))
    covers = bool(dec) and dec[-1][0] + dec[-1][1] == site
    pushes = [o for a, s, m, o in reversed(dec) if m == 'push'][:3]
    X1.append({'site': hex(site), 'tail_first': hex(first),
               'objdump_n3': [p['op'] for p in rec['nearest_three']],
               'capstone_n3': pushes,
               'contiguous': contiguous, 'reaches_site': covers,
               'agree': pushes == [p['op'] for p in rec['nearest_three']],
               'arg3': pushes[2] if len(pushes) > 2 else None})
out['X1'] = X1
out['X1_summary'] = {'sites': len(X1),
                     'all_contiguous': all(x['contiguous'] for x in X1),
                     'all_reach_site': all(x['reaches_site'] for x in X1),
                     'all_agree_with_objdump': all(x['agree'] for x in X1),
                     'arg3_values': sorted({x['arg3'] for x in X1})}

print(json.dumps(out, indent=2))
json.dump(out, open('/home/t628/projects/ra2-campaign-forge/_r133/sub_deepseek/r133ds2_final.json', 'w'), indent=2)
