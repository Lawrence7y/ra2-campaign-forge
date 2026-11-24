#!/usr/bin/env python3
"""R108-EXEC supplement 3: address-taken entries.

The card's A (call target), B (vtable slot), C (direct jmp/jcc target) sets all
miss the 4th entry class: an address materialised as an immediate or stored in a
data pointer (push imm32 / mov reg,imm32 / `mov [mem],imm32` / `.rdata`/`.data`
dword).  We scan every 4-byte-aligned AND unaligned little-endian occurrence of
each post-ret address across .text/.rdata/.data.
"""
import json, struct
import pefile

EXE = 'ra2bench/gamemd.exe'
OUT = '_r108/_exec/'
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
secs = [(s.Name.rstrip(b'\x00').decode(), s.VirtualAddress + IB,
         max(s.Misc_VirtualSize, s.SizeOfRawData), s.PointerToRawData) for s in pe.sections]
raw = open(EXE, 'rb').read()

ac = json.load(open(OUT + 'ac_sets.json'))
bs = json.load(open(OUT + 'bset.json'))
A = {int(k, 16) for k in ac['A']}
C = {int(k, 16) for k in ac['C']}
B = {int(k, 16) for k in bs['B']}
rf = json.load(open(OUT + 'rets_forensic.json'))

TABLES = [(0x46f5a0,0x46de20,0x46e4be),(0x5001e4,0x4ffd90,0x4ffde9),
          (0x58bda4,0x58bc20,0x58bd85),(0x71f2c0,0x71e940,0x71eea2),
          (0x71f328,0x71e940,0x71f092),(0x79f028,0x79da90,0x79ed73)]

# every 4-byte-aligned function-ish start we can hypothesise inside each region:
# (a) post-ret addresses, (b) any region address that is an A/B/C member
targets = set()
for t in rf['tables']:
    for r in t['rets']:
        targets.add(int(r['after'], 16))

def find_refs(va):
    pat = struct.pack('<I', va)
    hits = []
    for name, sva, sz, praw in secs:
        if name not in ('.text', '.rdata', '.data'):
            continue
        blob = raw[praw:praw + sz]
        i = blob.find(pat)
        while i != -1:
            hits.append({'section': name, 'at': hex(sva + i), 'aligned': i % 4 == 0})
            i = blob.find(pat, i + 1)
    return hits

out = {}
for va in sorted(targets):
    h = find_refs(va)
    out[hex(va)] = {
        'refs': h,
        'in_A': va in A, 'in_B': va in B, 'in_C': va in C,
        'addr_taken_only': bool(h) and va not in A and va not in B and va not in C,
    }

n_only = sum(1 for v in out.values() if v['addr_taken_only'])
n_any = sum(1 for v in out.values() if v['refs'])
print('post-ret addrs:', len(out))
print('  with any immediate/data reference:', n_any)
print('  address-taken but NOT in A/B/C (invisible to the card):', n_only)
for k, v in out.items():
    if v['addr_taken_only']:
        print('   ', k, [r['at'] for r in v['refs'][:4]])

json.dump({'note': ('A/B/C miss address-taken entries (push imm32, mov reg,imm32, '
                    'data pointers). addr_taken_only=true means the address is '
                    'referenced by immediate/data but is in none of A, B, C.'),
           'targets': out}, open(OUT + 'addrtaken.json', 'w'), indent=1)
