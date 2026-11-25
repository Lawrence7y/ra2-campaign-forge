# -*- coding: utf-8 -*-
"""r134ds_t4.py -- T4 negative controls: prove the gate is not simply broken.

(a) row col6 first token grep= -> EXISTS   => expect C7b shape-census FAIL
(b) row col5 -> a file for which its expression is FALSE  => expect C7 FAIL
Measured on both gate states.  If any control stays green, the gate is broader than claimed.
"""
import io, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r134ds_lib as L

OUT = {}
S = L.SNAP
GATES = {'P_R133': os.path.join(S, 'check_disc.R133_prefix.py'),
         'N_R134': os.path.join(S, 'check_disc.R134_final.py')}
TSVR = os.path.join(S, 'DISC_RECHECK.R134.tsv')
TSVP = os.path.join(S, 'DISC_RECHECK.R133pair.tsv')

hdr, rows0 = L.read_rows(os.path.join(L.ROOT, 'lead', 'next_re_20261117_r14'))
paths = L.all_paths(rows0)
TARGET = '5'
orig = [r for r in rows0 if r[0] == TARGET][0]
expr = orig[5].strip()
own = orig[4].strip().replace('\\', '/')
assert expr.startswith('grep=')

# find a file on which this expression is FALSE (for control b)
false_paths = [p for p in paths if p != own and L.run_expr(p, expr)[0] is False]
assert false_paths, 'no false path found'
FALSE_TARGET = false_paths[0]
print('control(b) will point col5 at %s (expression FALSE there)' % FALSE_TARGET)

OUT['setup'] = {'id': TARGET, 'expr': expr, 'own': own, 'false_target': FALSE_TARGET,
                'n_false_candidates': len(false_paths)}


def mutate(tag, gate_src, tsv_src, mutate_fn):
    r14 = L.build_sandbox('t4_' + tag, gate_src, tsv_src)
    hdr, rows = L.read_rows(r14)
    mutate_fn(rows)
    L.write_rows(r14, hdr, rows)
    rc, fails, notes, out = L.gate(r14)
    return {'exit': rc, 'fails': fails, 'n_fails': len(fails),
            'c7_lines': [f for f in fails if f.split()[1:2] == ['C7'] or ' C7 id ' in f],
            'c7b_lines': [f for f in fails if 'C7b' in f],
            'c10_lines': [f for f in fails if 'C10' in f]}


def mut_a(rows):
    """grep= -> EXISTS  (keeps the rest of the expression text; only first token changes)"""
    for r in rows:
        if r[0] == TARGET:
            assert r[5].strip() == expr
            r[5] = 'EXISTS ' + expr[len('grep='):]


def mut_b(rows):
    for r in rows:
        if r[0] == TARGET:
            assert r[4].strip().replace('\\', '/') == own
            r[4] = FALSE_TARGET.replace('/', '\\')


OUT['a'] = {}
OUT['b'] = {}
for tag, g in GATES.items():
    tsv = TSVP if tag == 'P_R133' else TSVR
    da = mutate(tag + '_a', g, tsv, mut_a)
    OUT['a'][tag] = da
    print('\n[%s] (a) col6 grep= -> EXISTS' % tag)
    print('   measured exit=%s fails=%d' % (da['exit'], da['n_fails']))
    for f in da['fails']:
        print('   ', f[:190])
    print('   C7b line present: %s' % bool(da['c7b_lines']))

    db = mutate(tag + '_b', g, tsv, mut_b)
    OUT['b'][tag] = db
    print('\n[%s] (b) col5 -> %s (expression FALSE there)' % (tag, FALSE_TARGET.split('/')[-1]))
    print('   measured exit=%s fails=%d' % (db['exit'], db['n_fails']))
    for f in db['fails']:
        print('   ', f[:190])
    print('   C7 (id) line present: %s' % any('C7 id' in f for f in db['fails']))

json.dump(OUT, io.open(os.path.join(L.HERE, 'r134ds_t4.json'), 'w'),
          ensure_ascii=False, indent=1)
print('\nwrote r134ds_t4.json')
