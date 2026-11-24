#!/usr/bin/env python3
"""R108-EXEC: build B = set of vtable slot values that land inside .text.

Slot-boundary criterion (explicit, since the card asks us to state it):
  For each of the 954 classes in out/reverse/symbols.json that carries a
  `vtable_va`, read exactly `vfunc_count` little-endian DWORDs starting at
  vtable_va.  symbols.json's vtable_va already points at the FIRST function
  slot (the RTTI CompleteObjectLocator pointer sits immediately before it;
  verified at 0x7e1664 -> 0x7fa4d8 for CDFileClass @0x7e1668).
  We additionally stop early at the first slot that is not a .text pointer,
  which is the vtable terminator / start of the next object.
Cross-check reported: alt-mode "scan until first non-.text slot" count.
"""
import json
import struct
import pefile

EXE = 'ra2bench/gamemd.exe'
OUT = '_r108/_exec/'

pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
sections = []
for s in pe.sections:
    a = s.VirtualAddress + IB
    sections.append((s.Name.rstrip(b'\x00').decode(), a,
                     max(s.Misc_VirtualSize, s.SizeOfRawData),
                     s.PointerToRawData))
with open(EXE, 'rb') as f:
    raw = f.read()

tsec = [x for x in sections if x[0] == '.text'][0]
TEXT_VA, TEXT_END = tsec[1], tsec[1] + tsec[2]


def read_va(va, n):
    for name, a, sz, praw in sections:
        if a <= va < a + sz:
            if va + n > a + sz:
                return None
            o = praw + (va - a)
            if o + n > len(raw):
                return None
            return raw[o:o + n]
    return None


sym = json.load(open('out/reverse/symbols.json'))
classes = sym['classes']

B = {}
bad = []
alt_sizes = {}
total_slots = 0
slots_in_text = 0
slots_not_text = []
nonnull_nontext = 0

for name, c in classes.items():
    v = c.get('vtable_va')
    if not v:
        continue
    vt = int(v, 16)
    cnt = int(c.get('vfunc_count') or 0)
    total_slots += cnt
    # primary: exactly cnt slots
    stopped = 0
    for i in range(cnt):
        chunk = read_va(vt + 4 * i, 4)
        if chunk is None:
            bad.append((name, v, i, 'unreadable'))
            break
        val = struct.unpack('<I', chunk)[0]
        if TEXT_VA <= val < TEXT_END:
            B.setdefault(val, []).append([name, vt, i])
            slots_in_text += 1
            stopped = i + 1
        else:
            slots_not_text.append([name, v, i, hex(val)])
            if val != 0:
                nonnull_nontext += 1
            break  # early stop at terminator / next object
    alt_sizes[name] = stopped

# independent alt-mode: scan until first non-.text slot regardless of vfunc_count
altB = set()
alt_slots = 0
for name, c in classes.items():
    v = c.get('vtable_va')
    if not v:
        continue
    vt = int(v, 16)
    for i in range(512):
        chunk = read_va(vt + 4 * i, 4)
        if chunk is None:
            break
        val = struct.unpack('<I', chunk)[0]
        if TEXT_VA <= val < TEXT_END:
            altB.add(val)
            alt_slots += 1
        else:
            break

print('text', hex(TEXT_VA), hex(TEXT_END))
print('vtables read', len(alt_sizes), '| declared slots', total_slots)
print('slots resolved into .text', slots_in_text, '| distinct B', len(B))
print('first non-.text slot hits', len(slots_not_text), '| of which non-null', nonnull_nontext)
print('unreadable', len(bad), bad[:5])
print('ALT-MODE distinct B', len(altB), 'slots', alt_slots,
      '| symmetric diff vs primary', len(altB ^ set(B)))

json.dump({
    'criterion': ('read exactly vfunc_count DWORDs from each symbols.json vtable_va '
                  '(vtable_va points at first function slot; COL pointer sits at -4); '
                  'stop early at first non-.text slot (terminator / next object)'),
    'text_va': TEXT_VA, 'text_end': TEXT_END,
    'vtables_read': len(alt_sizes), 'declared_slots': total_slots,
    'slots_in_text': slots_in_text, 'B_size': len(B),
    'first_nontext_slot_hits': len(slots_not_text),
    'nontext_nonnull': nonnull_nontext,
    'unreadable': bad,
    'alt_mode_B_size': len(altB), 'alt_mode_slots': alt_slots,
    'alt_mode_symdiff': sorted(hex(x) for x in (altB ^ set(B))),
    'B': {hex(k): sorted(v) for k, v in sorted(B.items())},
}, open(OUT + 'bset.json', 'w'), indent=0)
