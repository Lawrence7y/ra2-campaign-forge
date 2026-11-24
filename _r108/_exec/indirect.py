#!/usr/bin/env python3
"""R108-EXEC supplement 4: whole-.text scan of indirect jump sites.

The card's C set only holds *direct* jmp/jcc targets, so switch dispatch
(`jmp dword ptr [reg*4+table]`) contributes no entry points to A/B/C at all.
Here we enumerate every indirect jmp, recover its table base, and report which
dispatch sites and slot values fall inside each of the six intervals.
"""
import json, re, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = 'ra2bench/gamemd.exe'
OUT = '_r108/_exec/'
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
secs = [(s.Name.rstrip(b'\x00').decode(), s.VirtualAddress + IB,
         max(s.Misc_VirtualSize, s.SizeOfRawData), s.PointerToRawData) for s in pe.sections]
raw = open(EXE, 'rb').read()
tsec = [x for x in secs if x[0] == '.text'][0]
TEXT_VA, TEXT_END = tsec[1], tsec[1] + tsec[2]
TEXT_SIZE = TEXT_END - TEXT_VA

def rd(va, n):
    for name, a, sz, p in secs:
        if a <= va < a + sz and va + n <= a + sz:
            return raw[p + (va - a):p + (va - a) + n]
    return None

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False

re_tbl = re.compile(r'\[[^\]]*\+\s*(0x[0-9a-f]+)\]')
sites = []
mv = memoryview(raw[tsec[3]:tsec[3] + TEXT_SIZE])
off = 0
while off < TEXT_SIZE:
    c = 0
    for (addr, size, mn, ops) in md.disasm_lite(mv[off:], TEXT_VA + off):
        c += size
        if mn == 'jmp' and ops.startswith('dword ptr ['):
            m = re_tbl.search(ops)
            sites.append({'at': addr, 'text': mn + ' ' + ops,
                          'table': int(m.group(1), 16) if m else None})
    if c == 0:
        off += 1
    else:
        off += c

print('indirect jmp sites in .text:', len(sites))
tbls = sorted({s['table'] for s in sites if s['table'] is not None})
print('distinct table bases:', len(tbls))

TABLES = [(0x46f5a0,0x46de20,0x46e4be),(0x5001e4,0x4ffd90,0x4ffde9),
          (0x58bda4,0x58bc20,0x58bd85),(0x71f2c0,0x71e940,0x71eea2),
          (0x71f328,0x71e940,0x71f092),(0x79f028,0x79da90,0x79ed73)]

def slots(base, maxslots=1024):
    vals = []
    for i in range(maxslots):
        ch = rd(base + 4 * i, 4)
        if ch is None:
            break
        v = struct.unpack('<I', ch)[0]
        if TEXT_VA <= v < TEXT_END:
            vals.append(v)
        else:
            break
    return vals

INTERVALS = {}
for tbl, S, H in TABLES:
    key = '%s|%s|%s' % (hex(tbl), hex(S), hex(H))
    site_in = [s for s in sites if s['table'] is not None and S <= s['at'] < H + 8]
    entry = []
    for s in sites:
        if s['table'] is None:
            continue
        tvals = slots(s['table'])
        for v in tvals:
            if S < v <= H:
                entry.append({'target': hex(v), 'via_table': hex(s['table']),
                              'dispatcher': hex(s['at']),
                              'dispatcher_inside': S <= s['at'] < H})
    INTERVALS[key] = {
        'table': hex(tbl), 'S': hex(S), 'H': hex(H),
        'dispatch_sites_inside': [{'at': hex(s['at']), 'text': s['text'],
                                   'table': hex(s['table'])} for s in site_in],
        'indirect_entries_inside': entry,
        'indirect_entry_count': len({e['target'] for e in entry}),
    }
    print('---', key)
    print('   dispatch sites inside:', [(hex(s['at']), hex(s['table'])) for s in site_in])
    print('   indirect entries inside (S,H]:', sorted({e['target'] for e in entry}))

json.dump({'indirect_jmp_sites': len(sites),
           'intervals': INTERVALS}, open(OUT + 'indirect.json', 'w'), indent=1)
