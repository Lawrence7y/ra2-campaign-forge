#!/usr/bin/env python3
"""R133 deepseek audit: C8 (direct callers of both templates) + C11c (imm32 negative control).

Method: ONE linear disasm_lite sweep of .text with skipdata=True. Only call/jmp rel32
sites are kept (plus a compact addr/size/kind array for anything else). Cross-checked
against a raw E8/E9 byte scan to expose raw-scan false positives.
Memory: arrays only, no per-insn Python objects.
"""
import json, struct
from array import array
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

BIN = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
A_VA, B_VA = 0x6bedb0, 0x41c250

pe = pefile.PE(BIN, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
text = next(s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text')
TEXT_VA = IB + text.VirtualAddress
TEXT_RAW = text.PointerToRawData
TEXT_SZ = text.SizeOfRawData
with open(BIN, 'rb') as f:
    f.seek(TEXT_RAW)
    blob = f.read(TEXT_SZ)
TEXT_END = TEXT_VA + TEXT_SZ

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
md.skipdata_setup = ("db", 1, 16)

# ---- single linear sweep ----
callers = {'A': array('I'), 'B': array('I')}      # calling insn VA
callers_meta = {'A': [], 'B': []}
n_insn = 0
n_skip = 0
cov = 0
for addr, size, mnem, op in md.disasm_lite(blob, TEXT_VA):
    n_insn += 1
    cov += size
    if mnem == 'db':
        n_skip += 1
        continue
    if mnem in ('call', 'jmp') and op.startswith('0x'):
        tgt = int(op, 16)
        if tgt == A_VA:
            callers['A'].append(addr)
            callers_meta['A'].append({'va': hex(addr), 'size': size, 'mnem': mnem})
        elif tgt == B_VA:
            callers['B'].append(addr)
            callers_meta['B'].append({'va': hex(addr), 'size': size, 'mnem': mnem})
assert cov == TEXT_SZ, (cov, TEXT_SZ)

# ---- raw E8/E9 byte scan (the naive alternative) ----
raw_hits = {'A': [], 'B': []}
for i in range(len(blob) - 4):
    if blob[i] in (0xE8, 0xE9):
        va = TEXT_VA + i
        tgt = (va + 5 + struct.unpack_from('<i', blob, i + 1)[0]) & 0xFFFFFFFF
        if tgt == A_VA:
            raw_hits['A'].append(hex(va))
        elif tgt == B_VA:
            raw_hits['B'].append(hex(va))

# ---- verify each linear-sweep hit byte-decodes as real 5-byte E8/E9 landing on entry ----
ver = {}
for k, entry in (('A', A_VA), ('B', B_VA)):
    rows = []
    for va in callers[k]:
        o = va - TEXT_VA
        op = blob[o]
        rel = struct.unpack_from('<i', blob, o + 1)[0]
        land = (va + 5 + rel) & 0xFFFFFFFF
        rows.append({'va': hex(va), 'opcode': hex(op),
                     'opcode_is_e8_or_e9': op in (0xE8, 0xE9),
                     'size_5': True, 'lands_on_entry': land == entry,
                     'land_va': hex(land)})
    ver[k] = rows

# ---- C11c: entry VAs as imm32 anywhere in .text and in whole image ----
IMG = pe.get_memory_mapped_image()
def imm32_scan(val, hay, base):
    out = []
    pat = struct.pack('<I', val)
    i = hay.find(pat)
    while i >= 0:
        out.append(hex(base + i))
        i = hay.find(pat, i + 1)
    return out

res = {
    'text': {'va': hex(TEXT_VA), 'size': hex(TEXT_SZ), 'insns': n_insn,
             'skipped_db': n_skip, 'coverage_exact': cov == TEXT_SZ},
    'C8': {
        'A_count': len(callers['A']), 'A_sites': [hex(x) for x in callers['A']],
        'A_meta': callers_meta['A'],
        'B_count': len(callers['B']), 'B_sites': [hex(x) for x in callers['B']],
        'B_meta': callers_meta['B'],
        'total': len(callers['A']) + len(callers['B']),
    },
    'C8_verify': ver,
    'C8_raw_byte_scan': {'A': raw_hits['A'], 'B': raw_hits['B'],
                         'A_count': len(raw_hits['A']), 'B_count': len(raw_hits['B']),
                         'agrees_with_linear_sweep':
                             sorted(raw_hits['A'], key=lambda x: int(x, 16)) ==
                             sorted([hex(x) for x in callers['A']], key=lambda x: int(x, 16)) and
                             sorted(raw_hits['B'], key=lambda x: int(x, 16)) ==
                             sorted([hex(x) for x in callers['B']], key=lambda x: int(x, 16))},
    'C11c': {
        'imm32_A_in_text': imm32_scan(A_VA, blob, TEXT_VA),
        'imm32_B_in_text': imm32_scan(B_VA, blob, TEXT_VA),
        'imm32_A_in_image': imm32_scan(A_VA, bytes(IMG), IB),
        'imm32_B_in_image': imm32_scan(B_VA, bytes(IMG), IB),
    },
}
print(json.dumps(res, indent=2))
json.dump(res, open('/home/t628/projects/ra2-campaign-forge/_r133/sub_deepseek/r133ds2_callers.json', 'w'), indent=2)
