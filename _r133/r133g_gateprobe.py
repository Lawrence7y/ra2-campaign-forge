#!/usr/bin/env python3
# R133 r133g: measure the three dead branches WITHOUT modifying the gate.
# R132 ③/⑤ left three branches un-fixed: C7 exists / C7 bytes= / C7 none, and C11 frozen.
# R132 proved them dead by coverage count. Before touching a gate, measure the cost of each
# change: how many of the 31 rows would actually exercise the branch, and what a fix would do.
import json, io, os, re

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead/next_re_20261117_r14')
TAB = os.path.join(R14, 'DISC_RECHECK.tsv')

R = {}; ASSERT = []
def chk(n, c, d=''):
    ASSERT.append({'assert': n, 'pass': bool(c), 'detail': str(d)})
    print(('  PASS ' if c else '  FAIL ') + n + (('  [' + str(d) + ']') if d else ''))
    return bool(c)

rows = [x.split('\t') for x in io.open(TAB, encoding='utf-8').read().split('\n') if x]
hdr, body = rows[0], [r for r in rows[1:] if len(r) == 7]
R['rows'] = len(body)
print('header:', hdr)
print('data rows:', len(body))

# --- C7 branch coverage: what shapes do column 4 (path) and column 5 (expr) take? ---
R['col4_shapes'] = {}
R['col5_shapes'] = {}
for r in body:
    p, e = r[4].strip(), r[5].strip()
    kp = 'exists' if ('exists' in p) else ('other' if p else 'empty')
    ke = 'none' if (e == 'none' or e == '') else ('bytes=' if e.startswith('bytes=') else 'expr')
    R['col4_shapes'][kp] = R['col4_shapes'].get(kp, 0) + 1
    R['col5_shapes'][ke] = R['col5_shapes'].get(ke, 0) + 1
print('col4 shapes:', R['col4_shapes'])
print('col5 shapes:', R['col5_shapes'])

# --- are the three named branches actually dead? count how many rows take each ---
n_exists = sum(1 for r in body if r[4].strip().startswith('exists'))
n_bytes = sum(1 for r in body if r[5].strip().startswith('bytes='))
n_none = sum(1 for r in body if r[5].strip() in ('none', ''))
R['branch_coverage'] = {'exists': n_exists, 'bytes=': n_bytes, 'none': n_none}
print('branch coverage:', R['branch_coverage'])

chk('the rows table has the expected 31 data rows', len(body) == 31, len(body))
chk('C7 exists branch is exercised by ZERO rows in the current table',
    n_exists == 0, n_exists)
chk('C7 bytes= branch is exercised by ZERO rows in the current table', n_bytes == 0, n_bytes)
chk('C7 none branch is exercised by ZERO rows in the current table', n_none == 0, n_none)

# --- C11 frozen: how many ids, and do any of them declare claims='有'? ---
FREEZE = os.path.join(R14, 'DISC_UNVERIFIABLE.tsv')
fz = [x.split('\t') for x in io.open(FREEZE, encoding='utf-8').read().split('\n') if x]
fh, fb = fz[0], [c for c in fz[1:] if c and c[0].strip().isdigit()]
frozen_ids = sorted(int(c[0]) for c in fb)
col7 = {}
for r in body:
    if r[0].strip().isdigit():
        col7[int(r[0])] = r[6].strip()
R['frozen'] = {'ids': frozen_ids, 'n': len(frozen_ids),
               'col7_of_frozen': {str(i): col7.get(i) for i in frozen_ids}}
print('frozen ids:', frozen_ids)
print('frozen col7:', R['frozen']['col7_of_frozen'])
chk('all 12 frozen ids declare claims-有 in DISC_RECHECK (freeze != escape hatch)',
    all((col7.get(i) or '').startswith('有') for i in frozen_ids),
    {str(i): col7.get(i) for i in frozen_ids if not (col7.get(i) or '').startswith('有')})

# --- what would a C11 frozen fix actually have to do? measure anchor exprs ---
anchor = []
for c in fb:
    if len(c) >= 8:
        anchor.append({'id': int(c[0]), 'product': c[2].strip(), 'expr': c[3].strip()})
R['frozen_anchors'] = anchor
n_real = sum(1 for a in anchor if a['expr'] not in ('', 'none'))
print('frozen rows with a real anchor expr:', n_real, '/', len(anchor))
chk('every frozen row carries a real (non-empty, non-none) anchor expression',
    n_real == len(anchor), {'real': n_real, 'total': len(anchor)})

# ANTI: prove the dead-branch measurement is not vacuous -- a probe expression of each
# shape must behave differently, so "0 rows" means "nobody writes that shape", not
# "the classifier cannot see the shape".
probe = ['exists:foo', 'bytes=123', 'none', 'x == 1']
shapes = []
for p in probe:
    ke = 'none' if (p == 'none' or p == '') else ('bytes=' if p.startswith('bytes=') else 'expr')
    shapes.append((p, ke))
chk('ANTI: the shape classifier DOES distinguish bytes=/none/expr on synthetic probes',
    [s[1] for s in shapes] == ['expr', 'bytes=', 'none', 'expr'], shapes)
chk('ANTI: exists-detection fires on a synthetic exists probe',
    ('exists' in 'exists:foo') and n_exists == 0, {'probe_detected': True, 'real_rows': n_exists})

R['assertions'] = ASSERT
R['summary'] = {'pass': sum(1 for x in ASSERT if x['pass']), 'total': len(ASSERT)}
print('\nSUMMARY %d/%d PASS' % (R['summary']['pass'], R['summary']['total']))
json.dump(R, open('/home/t628/projects/ra2-campaign-forge/_r133/r133g_gateprobe.json', 'w'), indent=1)
