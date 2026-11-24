"""Exhaustive raw-dword VA occurrence scan for the 47 candidates (channel independent of capstone/atlas).
For each candidate entry, scan every PE section's raw bytes for the 4-byte little-endian VA.
Classify each hit by section and whether it looks like a vtable slot (aligned, neighbors are .text VAs).
This documents that candidate entries ARE vtable-reachable (virtual funcs) but have no live dispatch
(cross-ref survey has4_loose=0 and w2 direct-call=0).
Card S13-KPROVED2.
"""
import json, struct, os
from s13lib import pe, IB, DATA, TEXT_VA, TEXT_END, va2off, section_of

BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_KPROVED2"
pool = json.load(open(BASE + r'\work\pool.json', encoding='utf-8'))
cands = pool['candidates']

def is_text_va(x):
    return TEXT_VA <= x < TEXT_END

def looks_vtable_slot(va, off, section):
    # 4-byte aligned within a data-ish section; at least one neighbor dword is a .text VA
    if va & 3:
        return False
    try:
        before = int.from_bytes(DATA(off-4,4),'little')
        after = int.from_bytes(DATA(off+8,4),'little')
    except Exception:
        before = after = 0
    return is_text_va(before) or is_text_va(after)

result = {}
for r in cands:
    e = int(r['entry'], 16)
    pat = struct.pack('<I', e)
    hits = []
    for s in pe.sections:
        raw = DATA(s.PointerToRawData, s.SizeOfRawData)
        start = 0
        while True:
            k = raw.find(pat, start)
            if k < 0:
                break
            va = IB + s.VirtualAddress + k
            hits.append(dict(section=s.Name.decode().rstrip('\x00'), va=hex(va),
                             vslot=looks_vtable_slot(va, s.PointerToRawData+k, s)))
            start = k + 1
    result[r['entry']] = dict(name=r['name'], n_hits=len(hits),
                              vtable_slot_hits=sum(1 for h in hits if h['vslot']),
                              hits=hits[:12])

n_with_va = sum(1 for v in result.values() if v['n_hits']>0)
n_with_vslot = sum(1 for v in result.values() if v['vtable_slot_hits']>0)
print('candidates total:', len(result))
print('candidate VA appears as dword somewhere:', n_with_va)
print('candidate VA appears in a vtable-looking slot:', n_with_vslot)
for e,v in list(result.items())[:8]:
    print(' ',e, v['name'], 'hits=',v['n_hits'],'vslot=',v['vtable_slot_hits'])

json.dump({'summary': dict(total=len(result), va_appears=n_with_va, vslot_appears=n_with_vslot),
           'per_entry': result},
          open(BASE + r'\work\dword_va_scan.json','w',encoding='utf-8'), indent=2)
print('wrote work/dword_va_scan.json')
