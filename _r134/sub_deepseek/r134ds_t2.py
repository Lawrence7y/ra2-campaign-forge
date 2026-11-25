# -*- coding: utf-8 -*-
"""r134ds_t2.py -- T2 HOLE A: column 5 is not pinned.

For each of the 31 rows, evaluate that row's column-6 expression against EVERY one of the
23 distinct column-5 paths in the table (not just its own).  Report every row whose TRUE-set
has size >= 2 -- those rows can be redirected to a different file with the gate staying green.

Then take one such row, redirect it in a sandbox, and MEASURE the gate exit code.
Measured against both gate states (see r134ds_t1.py for why there are two).
"""
import io, json, os, sys, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r134ds_lib as L

OUT = {}
S = L.SNAP
GATES = {'P_R133': os.path.join(S, 'check_disc.R133_prefix.py'),
         'N_R134': os.path.join(S, 'check_disc.R134_final.py')}
TSV = os.path.join(S, 'DISC_RECHECK.R134.tsv')
TSV_R133 = os.path.join(S, 'DISC_RECHECK.R133pair.tsv')

hdr, rows0 = L.read_rows(os.path.join(L.ROOT, 'lead', 'next_re_20261117_r14'))
paths = L.all_paths(rows0)

# ---- 31 x 23 truth matrix ----
matrix = {}
for r in rows0:
    assert len(r) == 7, r[0]
    expr = r[5].strip()
    own = r[4].strip().replace('\\', '/')
    ts = []
    for p in paths:
        ok, det = L.run_expr(p, expr)
        if ok is True:
            ts.append(p)
    matrix[r[0]] = {'own': own, 'expr': expr, 'true_set': ts, 'size': len(ts),
                    'own_in_set': own in ts}

multi = {k: v for k, v in matrix.items() if v['size'] >= 2}
OUT['matrix'] = matrix
OUT['multi_rows'] = sorted(multi, key=lambda x: int(x))
OUT['n_rows'] = len(matrix)
OUT['n_paths'] = len(paths)

print('rows=%d paths=%d' % (len(matrix), len(paths)))
print('--- rows whose TRUE-set has size >= 2 (redirectable while green) ---')
for k in sorted(multi, key=lambda x: int(x)):
    v = matrix[k]
    print('id=%-3s size=%-2d own=%s' % (k, v['size'], v['own'].split('/')[-1]))
    for p in v['true_set']:
        mark = ' <== own' if p == v['own'] else ''
        print('        %s%s' % (p, mark))
print('n_multi = %d / %d' % (len(multi), len(matrix)))

# size histogram
hist = {}
for v in matrix.values():
    hist[v['size']] = hist.get(v['size'], 0) + 1
OUT['size_hist'] = hist
print('TRUE-set size histogram (size: rowcount):', dict(sorted(hist.items())))

# ---- pick one multi row, redirect it, measure ----
pick = None
for k in sorted(multi, key=lambda x: int(x)):
    alts = [p for p in multi[k]['true_set'] if p != multi[k]['own']]
    if alts:
        pick = (k, multi[k]['own'], alts[0])
        break
assert pick, 'no redirectable row'
print('\nPICK id=%s  %s  ->  %s' % (pick[0], pick[1], pick[2]))
print('expression:', matrix[pick[0]]['expr'])

OUT['pick'] = {'id': pick[0], 'from': pick[1], 'to': pick[2],
               'expr': matrix[pick[0]]['expr'], 'runs': {}}


def redirect(tag, gate_src, tsv_src, from_p, to_p, rowid):
    r14 = L.build_sandbox('t2_' + tag, gate_src, tsv_src)
    hdr, rows = L.read_rows(r14)
    done = False
    for r in rows:
        if r[0] == rowid:
            assert r[4].strip().replace('\\', '/') == from_p, (r[4], from_p)
            r[4] = to_p.replace('/', '\\')
            done = True
    assert done
    L.write_rows(r14, hdr, rows)
    # prove the table really changed on disk before running
    hdr2, rows2 = L.read_rows(r14)
    got = [r[4].strip().replace('\\', '/') for r in rows2 if r[0] == rowid][0]
    assert got == to_p, (got, to_p)
    rc, fails, notes, out = L.gate(r14)
    return {'exit': rc, 'fails': fails, 'n_fails': len(fails),
            'table_now': got, 'c7line': [l for l in out.split('\n')
                                         if l.startswith('C7 live-checks')]}


for tag, g in GATES.items():
    tsv = TSV_R133 if tag == 'P_R133' else TSV
    d = redirect(tag + '_holeA', g, tsv, pick[1], pick[2], pick[0])
    OUT['pick']['runs'][tag] = d
    print('\n[%s] redirected id=%s col5 -> %s' % (tag, pick[0], pick[2]))
    print('   measured exit=%s fails=%d' % (d['exit'], d['n_fails']))
    for f in d['fails'][:6]:
        print('   ', f)
    for l in d['c7line']:
        print('   ', l)

json.dump(OUT, io.open(os.path.join(L.HERE, 'r134ds_t2.json'), 'w'),
          ensure_ascii=False, indent=1)
print('\nwrote r134ds_t2.json')
