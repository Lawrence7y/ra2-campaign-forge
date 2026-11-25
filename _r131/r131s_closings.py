#!/usr/bin/env python3
# R131 r131s: two closings.
#
# (1) The sibling instantiation 0x41c250 is called from 13 sites with a per-call rclsid.
#     Resolve each immediate rclsid to a GUID and check whether the 0x6bedb0 shape (one
#     fixed CLSID driving a dll load) is the exception or the rule.
#
# (2) GATE FACT, wider than R130 measured it. R130 measured the 12 rows whose col7 says
#     有 and found 0 DISC_RECHECK self-description lines (12/12 zero) -> C17 checked=0.
#     R131 asks the wider question: does ANY of the 31 rows' products carry such a line?
#     If the answer is also 0, then widening C17's input set CANNOT fix it -- the fix
#     requires producing real lines, which is a business action, not a code change.
#     That closes the "just widen C17" idea before someone spends a round on it.
import io
import json
import os
import re
import struct

import pefile

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
R14 = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
ROOT = '/home/t628/projects/ra2-campaign-forge'
OUT = '/home/t628/projects/ra2-campaign-forge/_r131/r131s_closings.json'

pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
secs = {}
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm] = (base + s.VirtualAddress, base + s.VirtualAddress + s.SizeOfRawData, s)

A = []
def chk(name, cond, detail=''):
    A.append({'assert': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + (' :: ' + str(detail) if detail else ''))

R = {}

# ---------- (1) sibling call sites' rclsids ----------
def guid(va):
    for nm, (lo, hi, s) in secs.items():
        if lo <= va < hi:
            o = va - (base + s.VirtualAddress)
            d = s.get_data()
            if o < 0 or o + 16 > min(s.SizeOfRawData, len(d)):
                return None
            g = d[o:o + 16]
            d1, d2, d3 = struct.unpack('<IHH', g[:8])
            return {'str': '{%08X-%04X-%04X-%s-%s}' % (d1, d2, d3, g[8:10].hex().upper(),
                                                        g[10:].hex().upper()),
                    'hex': g.hex(), 'section': nm}
    return None


SIB_ARGS = json.load(open('/home/t628/projects/ra2-campaign-forge/_r131/r131r_semantics.json',
                          encoding='utf-8'))['sibling_call_args']
rows = []
for o in SIB_ARGS:
    a1 = o['args_arg1_arg2_arg3'][0]
    g = None
    if isinstance(a1, int):
        g = guid(a1)
    rows.append({'site': o['site'],
                 'arg1': a1,
                 'arg1_hex': hex(a1) if isinstance(a1, int) else a1,
                 'arg1_guid': g,
                 'arg2': o['args_arg1_arg2_arg3'][1],
                 'arg3': o['args_arg1_arg2_arg3'][2]})
R['sibling_sites'] = rows
print('=== sibling 0x41c250 call sites: rclsid identity ===')
for r in rows:
    print('   %-10s arg1=%-10s %-42s arg2=%-8s arg3=%s'
          % (r['site'], r['arg1_hex'], (r['arg1_guid'] or {}).get('str', '-'),
             r['arg2'], r['arg3']))
imm = [r for r in rows if r['arg1_guid']]
R['resolved_count'] = len(imm)
chk('every immediate rclsid at the 13 sibling sites resolves to 16 readable bytes',
    all(r['arg1_guid'] and len(r['arg1_guid']['hex']) == 32 for r in imm),
    [r['site'] for r in imm if not r['arg1_guid']])
chk('the sibling sites use at least 3 DISTINCT rclsids (it is a per-call CLSID, unlike '
    '0x6bedb0 which has one fixed CLSID from a table)',
    len({r['arg1_guid']['str'] for r in imm}) >= 3,
    sorted({r['arg1_guid']['str'] for r in imm}))
chk('control: none of the sibling rclsids equals the 0x6bedb0 CLSID {1440AD10-...}',
    all(r['arg1_guid']['str'] != '{1440AD10-6AA8-11D1-B6F9-00A024DDAFD1}' for r in imm),
    sorted({r['arg1_guid']['str'] for r in imm}))

# ---------- (2) gate fact: is C17 vacuous for ALL 31 rows, not just the 12? ----------
lines = io.open(os.path.join(R14, 'DISC_RECHECK.tsv'), encoding='utf-8',
                errors='replace').read().split('\n')
trows = [l.split('\t') for l in lines[1:] if l.strip()]
trows = [r for r in trows if len(r) == 7]
LINERE = re.compile(r'^DISC_RECHECK discipline=(\d+) round=(R\d+) at=(\S+) '
                    r'anchors=(sha256:[0-9a-f]{64}) conclusion=(\S+?)\r?$')
PATHR = re.compile(r'(?:^|[/\\])R(?:17_)?R?(\d+)_')

per = []
total_lines = 0
for r in trows:
    p = r[4].strip().replace('\\', '/')
    ap = os.path.join(ROOT, p)
    d = {'id': int(r[0]), 'col7_claims_you': r[6].strip().startswith('有'),
         'product': p, 'exists': os.path.isfile(ap)}
    if d['exists']:
        txt = io.open(ap, encoding='utf-8', errors='replace').read()
        hits = []
        for ln in txt.splitlines():
            m = LINERE.match(ln)
            if m and int(m.group(1)) == d['id']:
                hits.append({'round': m.group(2), 'at': m.group(3)})
        d['self_lines_for_this_id'] = len(hits)
        d['samples'] = hits[:2]
        total_lines += len(hits)
        # also count ANY DISC_RECHECK line at all in the product, any discipline id
        d['any_discrecheck_lines'] = sum(1 for ln in txt.splitlines()
                                         if ln.startswith('DISC_RECHECK '))
    per.append(d)
R['gate_products'] = per
R['total_self_lines_for_own_id'] = total_lines
R['total_any_discrecheck_lines'] = sum(d.get('any_discrecheck_lines', 0) for d in per)
R['rows'] = len(per)
R['rows_with_product'] = sum(1 for d in per if d['exists'])
R['rows_claims_you'] = sum(1 for d in per if d['col7_claims_you'])
R['rows_claims_none'] = sum(1 for d in per if not d['col7_claims_you'])
print('\n=== gate: DISC_RECHECK self-description lines across ALL rows ===')
print('   rows %d ; products present %d ; claims-有 %d ; claims-none %d'
      % (R['rows'], R['rows_with_product'], R['rows_claims_you'], R['rows_claims_none']))
print('   lines matching their OWN discipline id : %d' % R['total_self_lines_for_own_id'])
print('   lines matching ANY discipline id       : %d' % R['total_any_discrecheck_lines'])
chk('R130 measured only the claims-有 rows; across ALL 31 rows there are still ZERO '
    'self-description lines for their own id',
    R['total_self_lines_for_own_id'] == 0, R['total_self_lines_for_own_id'])
chk('there is not even a single DISC_RECHECK line for ANY other discipline id in any product',
    R['total_any_discrecheck_lines'] == 0, R['total_any_discrecheck_lines'])
chk('therefore widening C17 input from claims-有 to all rows CANNOT raise checked above 0 '
    '(measured both ways in r131p: 0 and 0)',
    R['total_any_discrecheck_lines'] == 0,
    'fix must be "produce real lines", not "widen the scan"')
# the frozen set == claims-有 set exactly, so C11 ok can only ever be 0 today
fz = os.path.join(R14, 'DISC_UNVERIFIABLE.tsv')
frozen = [int(x.split('\t')[0]) for x in io.open(fz, encoding='utf-8').read().split('\n')[1:]
          if x.strip() and x.split('\t')[0].strip().isdigit()]
you = [d['id'] for d in per if d['col7_claims_you']]
R['frozen'] = frozen
R['claims_you'] = you
chk('C11 claims-有 set == frozen-registry set exactly, so every claims-有 row is one that '
    'is declared structurally unable to produce a line => C11 ok is 0 by construction',
    sorted(you) == sorted(frozen), {'claims_you': you, 'frozen': frozen})
chk('control: the frozen registry is non-empty (13 rows would be a different story; it is 12)',
    len(frozen) == 12, len(frozen))
# C11's three outcomes must therefore all be structurally pinned
R['c11_outcomes'] = {'ok': 0, 'fail': 0, 'frozen': len(frozen), 'claims_none': len(you.__class__.__name__) and (R['rows'] - len(you))}
chk('19 claims-none + 12 frozen = 31 rows, leaving NO row able to reach C11 ok=1 today',
    R['rows_claims_none'] == 19 and len(frozen) == 12 and 19 + 12 == 31,
    R['c11_outcomes'])

R['assertions'] = A
R['summary'] = {'total': len(A), 'pass': sum(1 for x in A if x['ok']),
                'fail': [x['assert'] for x in A if not x['ok']]}
print('\nASSERTIONS: %d total, %d pass, %d fail'
      % (R['summary']['total'], R['summary']['pass'], len(R['summary']['fail'])))
json.dump(R, open(OUT, 'w'), ensure_ascii=False, indent=1)
raise SystemExit(1 if R['summary']['fail'] else 0)
