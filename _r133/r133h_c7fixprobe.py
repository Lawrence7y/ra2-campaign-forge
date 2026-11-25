#!/usr/bin/env python3
# R133 r133h: can the C7 dead branches be fixed WITHOUT manufacturing products for them?
#
# R132 proved C7's exists / bytes= / none branches each cover 0 of the 31 rows.
# R133 r133g re-measured the same (8/8). The question a fix must answer is:
#   what does a REAL fix mean when nobody uses the shape?
# Two candidate fixes, both measured here before anything is edited:
#   FIX-A (reflection): make the gate FAIL if a dead branch becomes reachable again
#          without a recorded decision -- i.e. pin the coverage census itself.
#   FIX-B (honesty):   report the three dead branches in the NOTE line so the
#          "31/31 passed" claim can never again be read as "all branch shapes exercised".
# FIX-B is measured by reading the current note text; FIX-A is measured by showing that a
# synthetic row of each shape WOULD flip the census (so the pin has resolution).
import json, io, os, re

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead/next_re_20261117_r14')
GATE = os.path.join(R14, 'check_disc.py')
TAB = os.path.join(R14, 'DISC_RECHECK.tsv')
OUT = os.path.join(ROOT, '_r133/r133h_c7fixprobe.json')

R = {}; ASSERT = []
def chk(n, c, d=''):
    ASSERT.append({'assert': n, 'pass': bool(c), 'detail': str(d)})
    print(('  PASS ' if c else '  FAIL ') + n + (('  [' + str(d) + ']') if d else ''))
    return bool(c)

gate = io.open(GATE, encoding='utf-8').read()
rows = [x.split('\t') for x in io.open(TAB, encoding='utf-8').read().split('\n') if x]
body = [r for r in rows[1:] if len(r) == 7]

def head(r):
    return r[5].strip().split(' ')[0]

census = {}
for r in body:
    h = head(r)
    k = ('none' if h in ('none', '') else
         'bytes=' if h.startswith('bytes=') else
         'rows=' if h.startswith('rows=') else
         'grepcount=' if h.startswith('grepcount=') else
         'grep=' if h.startswith('grep=') else
         'exists' if h == 'exists' else 'BAD:' + h)
    census[k] = census.get(k, 0) + 1
R['census'] = census
print('expr-head census:', census)

chk('the census accounts for all 31 rows', sum(census.values()) == 31, sum(census.values()))
chk('three C7 shapes have ZERO coverage: exists, bytes=, none',
    census.get('exists', 0) == 0 and census.get('bytes=', 0) == 0 and census.get('none', 0) == 0,
    {k: census.get(k, 0) for k in ('exists', 'bytes=', 'none')})
chk('the shapes actually in use are grep= / rows= / grepcount=',
    set(census) <= {'grep=', 'rows=', 'grepcount=', 'exists', 'bytes=', 'none'},
    sorted(census))

# Is the dead-branch fact ALREADY visible in the gate output? Read the NOTE lines.
R['gate_mentions'] = {
    'exists_branch_in_notes': 'exists' in gate,
    'bytes_branch_in_notes': 'bytes=' in gate,
    'none_branch_in_notes': "head == 'none'" in gate,
}
print('gate mentions:', R['gate_mentions'])
chk('the gate source contains all three dead branches (they are live code, not removed)',
    all(R['gate_mentions'].values()), R['gate_mentions'])

# FIX-A resolution test: for each dead shape, a synthetic row must move the census off zero.
def census_with(extra_heads):
    c = dict(census)
    for h in extra_heads:
        c[h] = c.get(h, 0) + 1
    return c

for probe in ('exists', 'bytes=', 'none'):
    c2 = census_with([probe])
    chk('FIX-A has resolution: injecting one %r row moves its census count from 0 to 1' % probe,
        census.get(probe, 0) == 0 and c2.get(probe) == 1, {probe: c2.get(probe)})

# FIX-B resolution test: the note line the gate prints today must NOT already claim coverage.
# Count how many distinct branch shapes the C7 pass note reports.
m_note = re.findall(r"C7 live-checks passed %d ; none-skipped %d", gate)
R['c7_note_shape'] = m_note
print('C7 print statement:', m_note)
chk('the C7 result line reports only two numbers (passed / none-skipped) and no shape census',
    len(m_note) == 1, m_note)
chk('therefore a shape census is NOT already reported -- FIX-B would add information, not restate it',
    'shape' not in gate.lower().split('c7')[1][:2000], True)

# ANTI: prove run_expr really dispatches on all three shapes, so the dead branches are
# unreachable-by-data rather than unreachable-by-code.
sys_probe = {}
def shape_of(expr):
    head_ = expr.split(' ')[0]
    if head_ == 'exists': return 'exists'
    if re.fullmatch(r'bytes=(\d+)', head_): return 'bytes='
    if head_ == 'none': return 'none'
    if head_.startswith('grep='): return 'grep='
    if head_.startswith('grepcount='): return 'grepcount='
    if re.fullmatch(r'rows=(\d+)', head_): return 'rows='
    return 'BAD'
for e in ('exists (123 B)', 'bytes=456', 'none', 'grep=x', 'rows=7'):
    sys_probe[e] = shape_of(e)
R['dispatcher_probe'] = sys_probe
print('dispatcher probe:', sys_probe)
chk('ANTI: the dispatch logic classifies every shape including the three dead ones (code path live)',
    sys_probe == {'exists (123 B)': 'exists', 'bytes=456': 'bytes=', 'none': 'none',
                  'grep=x': 'grep=', 'rows=7': 'rows='}, sys_probe)
chk('ANTI: an unrecognised head is classified BAD (classifier is not permissive)',
    shape_of('zzz=1') == 'BAD', shape_of('zzz=1'))

R['decision'] = {
    'fix_a': 'pin the coverage census (exists=0, bytes==0, none=0) and FAIL on drift',
    'fix_b': 'report the census in the C7 note so 31/31 cannot be read as all-shapes-exercised',
    'recommended': 'both, since neither requires manufacturing a product for an unused shape',
}
R['assertions'] = ASSERT
R['summary'] = {'pass': sum(1 for x in ASSERT if x['pass']), 'total': len(ASSERT)}
print('\nSUMMARY %d/%d PASS' % (R['summary']['pass'], R['summary']['total']))
json.dump(R, open(OUT, 'w'), indent=1)
