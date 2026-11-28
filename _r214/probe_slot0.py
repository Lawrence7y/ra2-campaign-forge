#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot probe: resolve E3 slot0 caliber mismatch (0x4f4240 vs card's 0x6d1770)."""
import sys, json, hashlib, struct, collections
ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

RAW = P.RAW
print('RAW sha256 =', hashlib.sha256(RAW).hexdigest())
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False

def h(v): return 'None' if v is None else '0x%08x' % v
def dis(addr, n=10):
    o = P.r2o(addr)
    if o is None: return ['<unmapped>']
    out = []
    for i in md.disasm(RAW[o:o + 32], addr, count=n):
        out.append('%s %s' % (i.mnemonic, i.op_str))
    return out

# rebuild COL + predecessor exactly as ex1.py
cols = []
for sn in ('.rdata', '.data'):
    s = P.B[sn]
    for va in range(s['lo'], s['hi_file'] & ~3, 4):
        if P.dw(va) not in (0, 1, 2): continue
        if P.dw(va+8) != 0: continue
        ptd, pchd = P.dw(va+12), P.dw(va+16)
        if P.where(ptd) != '.data' or P.where(pchd) != '.rdata': continue
        nb = P.cstr(ptd+8)
        if nb is None or not (nb.startswith(b'.?A') and nb.endswith(b'@@')): continue
        cols.append({'C': va, 'mdisp': P.dw(va+4), 'pTD': ptd, 'pCHD': pchd,
                     'name': nb[1:].decode('latin1')})
colset = set(c['C'] for c in cols)
pred = {}
for sn in ('.rdata', '.data'):
    s = P.B[sn]
    for va in range(s['lo'], s['hi_file'] & ~3, 4):
        d = P.dw(va)
        if d in colset and P.where(P.dw(va+4)) == '.text': pred[d] = va

def slots(base, cap=4096):
    out = []
    va = base
    while len(out) < cap:
        d = P.dw(va)
        if d is None or P.where(d) != '.text': break
        out.append(d); va += 4
    return out

print('\n=== CLASS COL DETAIL (all COLs per name) ===')
for cls in ('MouseClass', 'TabClass', 'ScrollClass', 'HouseClass'):
    want = '?AV%s@@' % cls
    for c in [x for x in cols if x['name'] == want]:
        V = pred.get(c['C'])
        print('%s  C=%s mdisp=%d pCHD=%s pTD=%s  predV=%s base(V+4)=%s'
              % (c['name'], h(c['C']), c['mdisp'], h(c['pCHD']), h(c['pTD']), h(V),
                 h(V+4 if V else None)))
        if V:
            for off in (-8, -4, 0, 4, 8, 12):
                print('    V%+d = %s : dw=%s where=%s' % (off, h(V+off), h(P.dw(V+off)), P.where(P.dw(V+off))))
            sl = slots(V+4)
            print('    n=%d  slots[0:6]=%s' % (len(sl), [h(x) for x in sl[:6]]))
            print('    0x6d1770 at indices = %s' % [i for i,x in enumerate(sl) if x == 0x6d1770])
            print('    slot18 = %s' % (h(sl[18]) if len(sl) > 18 else None))

print('\n=== GLOBAL SEARCH for dword 0x6d1770 (aligned words, all sections) ===')
occ = []
for s in P.SECS:
    for va in range(s['lo'], s['hi_file'] & ~3, 4):
        if P.dw(va) == 0x6d1770:
            occ.append((s['name'], va))
print('count = %d ; first 30 = %s' % (len(occ), [(n, h(v)) for n,v in occ[:30]]))
print('which vftable slots hold 0x6d1770:')
hits = []
for c in cols:
    V = pred.get(c['C'])
    if not V: continue
    sl = slots(V+4)
    for i, x in enumerate(sl):
        if x == 0x6d1770:
            hits.append((c['name'], h(c['C']), h(V+4), i, c['mdisp']))
print('  count=%d  sample=%s' % (len(hits), hits[:40]))

print('\n=== SMALL-WINDOW DISASSEMBLY ===')
for a in (0x4f4240, 0x6d1770, 0x5bda80, 0x4c9150, 0x723ea0, 0x723eb0, 0x4104c0):
    print('  %s : %s' % (h(a), ' | '.join(dis(a, 8))))

print('\n=== vftable base candidates around Mouse predV ===')
mc = [x for x in cols if x['name'] == '?AVMouseClass@@' and x['mdisp'] == 0][0]
V = pred[mc['C']]
print('  Mouse predV=%s ; bytes V-16..V+24:' % h(V))
for va in range(V-16, V+24, 4):
    print('    %s : %s (%s)' % (h(va), h(P.dw(va)), P.where(P.dw(va))))
print('\nprobe complete')
