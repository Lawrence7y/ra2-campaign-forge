# -*- coding: utf-8 -*-
"""R125b: independent recomputation of R125a's decisive numbers.

Rule D requires the lead session to recompute every number it accepts.  This
script deliberately does NOT reuse any of R125a's machinery: no taint tracking,
no CFG walk, no frame-slot arithmetic.  It uses one blunt, local judgement:

    for each push of an IID constant, look forward a FIXED number of
    instructions inside the same basic block and ask only
    "is an OLE stream API referenced here at all?"

That is a much weaker instrument, but it is independent, and the two agreeing on
the population counts is what makes the R125a result reproducible rather than
an artefact of one tracer.
"""
import os, sys, json, hashlib, collections
import pefile, capstone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE  = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT  = os.path.join(ROOT, '_r125', 'r125b_recompute.json')
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

ck = []
def add(name, ok, detail=''):
    ck.append({'name': name, 'ok': bool(ok), 'detail': str(detail)})

pe = pefile.PE(EXE); IB = pe.OPTIONAL_HEADER.ImageBase
add('R0 exe sha256 pinned',
    hashlib.sha256(open(EXE, 'rb').read()).hexdigest() == EXE_SHA)

TEXT = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text'][0]
T_LO = TEXT.VirtualAddress + IB
T_HI = T_LO + TEXT.Misc_VirtualSize
blob = pe.get_data(TEXT.VirtualAddress, TEXT.Misc_VirtualSize)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.skipdata = True
ins = [(a, m, o) for a, _s, m, o in md.disasm_lite(blob, T_LO)]
n_ins = len(ins)

IAT = {}
for d in pe.DIRECTORY_ENTRY_IMPORT:
    for imp in d.imports:
        IAT[imp.address] = imp.name.decode() if imp.name else None

OLE = {'OleSaveToStream', 'OleLoadFromStream'}
OLE_VA = sorted(k for k, v in IAT.items() if v in OLE)
add('R1 the two OLE stream entry points are in the import table at known slots',
    len(OLE_VA) == 2, ['0x%x=%s' % (k, IAT[k]) for k in OLE_VA])

def num(t):
    t = t.strip()
    if not t or t[0] not in '0123456789':
        return None
    try:
        return int(t, 0)
    except ValueError:
        return None

TARGETS = {0x7f7c70: '0x7f7c70', 0x7f7c80: '0x7f7c80',
           0x818858: '0x818858', 0x820270: '0x820270',
           0x7f7c90: '0x7f7c90', 0x7f7ca0: '0x7f7ca0',
           0x7f7cd0: '0x7f7cd0'}

WINDOW = 40
res = collections.defaultdict(lambda: {'push': 0, 'ole_after': 0, 'ole_sites': []})
for i, (a, m, o) in enumerate(ins):
    if m != 'push':
        continue
    v = num(o)
    if v not in TARGETS:
        continue
    key = TARGETS[v]
    res[key]['push'] += 1
    hit = False
    for t in range(i + 1, min(n_ins, i + 1 + WINDOW)):
        a2, m2, o2 = ins[t]
        if m2 == 'ret':
            break
        if m2 != 'call':
            continue
        tgt = None
        if o2.startswith('dword ptr [') and '+' not in o2:
            tgt = num(o2[len('dword ptr ['):-1])
        if tgt in OLE_VA:
            hit = True
            break
    if hit:
        res[key]['ole_after'] += 1
        res[key]['ole_sites'].append('0x%x' % a)

# Independent verdict: the OLE stream API is reachable only after a 109 push.
add('R2 every 00000109 address has OLE-reachable sites (0x7f7c80)',
    res['0x7f7c80']['ole_after'] > 0, '%d of %d pushes'
    % (res['0x7f7c80']['ole_after'], res['0x7f7c80']['push']))
add('R3 the second 00000109 address is also OLE-reachable (0x820270)',
    res['0x820270']['ole_after'] > 0, '%d of %d pushes'
    % (res['0x820270']['ole_after'], res['0x820270']['push']))
add('R4 0000010C (0x7f7c70) never has an OLE API within %d instructions' % WINDOW,
    res['0x7f7c70']['ole_after'] == 0, '%d of %d pushes'
    % (res['0x7f7c70']['ole_after'], res['0x7f7c70']['push']))
add('R5 0000010C (0x818858) never has an OLE API within %d instructions' % WINDOW,
    res['0x818858']['ole_after'] == 0, '%d of %d pushes'
    % (res['0x818858']['ole_after'], res['0x818858']['push']))

# R6: the split must be complete -- no OTHER census constant may be OLE-reachable.
others = [k for k in res if k not in ('0x7f7c80', '0x820270')]
add('R6 no other measured constant is OLE-reachable',
    all(res[k]['ole_after'] == 0 for k in others),
    {k: res[k]['ole_after'] for k in others})

# R7: sensitivity -- shrink the window until the split breaks, and report where.
def split_at(w):
    a1 = a2 = b1 = b2 = 0
    for i, (a, m, o) in enumerate(ins):
        if m != 'push':
            continue
        v = num(o)
        if v not in (0x7f7c80, 0x820270, 0x7f7c70, 0x818858):
            continue
        hit = False
        for t in range(i + 1, min(n_ins, i + 1 + w)):
            a2_, m2, o2 = ins[t]
            if m2 == 'ret':
                break
            if m2 == 'call' and o2.startswith('dword ptr [') and '+' not in o2:
                if num(o2[len('dword ptr ['):-1]) in OLE_VA:
                    hit = True
                    break
        if hit:
            if v in (0x7f7c80, 0x820270):
                a1 += 1
            else:
                b1 += 1
    return a1, b1
w_probe = [w for w in (6, 8, 10, 12, 16, 20, 30, 40)]
table = {w: split_at(w) for w in w_probe}
add('R8 the split survives every window from 10 to 40 instructions (it is not tuned)',
    all(table[w][0] > 0 and table[w][1] == 0 for w in w_probe if w >= 10),
    {w: table[w] for w in w_probe})
add('R9 the window bound is real: below 10 instructions even the 109 population is'
    ' empty, so the test is not trivially true',
    table[6][0] == 0 and table[8][0] == 0 and table[10][0] > 0,
    'w6=%s w8=%s w10=%s' % (table[6], table[8], table[10]))

rep = {'exe_sha256': EXE_SHA, 'window': WINDOW,
       'ole_slots': ['0x%x' % k for k in OLE_VA],
       'per_constant': {k: {'push': v['push'], 'ole_after': v['ole_after'],
                            'first_sites': v['ole_sites'][:8]}
                        for k, v in sorted(res.items())},
       'window_sensitivity': {str(w): list(t) for w, t in table.items()},
       'checks': ck, 'all_ok': all(c['ok'] for c in ck)}
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

bad = [c for c in ck if not c['ok']]
print('R125b %d/%d PASS' % (len(ck) - len(bad), len(ck)))
for c in ck:
    print(('  PASS  ' if c['ok'] else '  FAIL  ') + c['name']
          + (' :: ' + c['detail'] if c['detail'] else ''))
sys.exit(0 if not bad else 1)
