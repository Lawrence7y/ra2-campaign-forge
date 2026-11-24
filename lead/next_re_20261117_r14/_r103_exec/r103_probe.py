#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R103 independent freetext probe. Runs check_disc.py in a copied TSV sandbox.

Mutates only /tmp/r103_exec/lead/next_re_20261117_r14/DISC_RECHECK.tsv,
always restoring the pristine bytes after each trial. Never writes to the real tree.
"""
import io, os, subprocess, sys, json, hashlib, tempfile

SANDBOX = '/tmp/r103_exec/lead/next_re_20261117_r14'
TSV = os.path.join(SANDBOX, 'DISC_RECHECK.tsv')
GATE = os.path.join(SANDBOX, 'check_disc.py')
PRISTINE = io.open(TSV, 'rb').read()
ROWS = [l.split('\t') for l in PRISTINE.decode('utf-8').split('\n')[1:] if l.strip()]
IDS = [r[0] for r in ROWS]
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')


def write(rows):
    header = PRISTINE.decode('utf-8').split('\n')[0]
    body = '\n'.join([header] + ['\t'.join(r) for r in rows]) + '\n'
    io.open(TSV, 'wb').write(body.encode('utf-8'))


def restore():
    io.open(TSV, 'wb').write(PRISTINE)


def run(rows=None):
    if rows is None:
        restore()
    else:
        write(rows)
    p = subprocess.run([sys.executable, GATE], cwd=SANDBOX, env=ENV,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode('utf-8', 'replace')
    fails = [l.strip() for l in out.splitlines() if l.strip().startswith('FAIL  ')]
    return {'exit': p.returncode, 'fails': [f[6:] for f in fails], 'output': out}


def mutate(col, value, only_id=None):
    rows = [r[:] for r in ROWS]
    for r in rows:
        if only_id is None or (r and r[0] == only_id):
            r[col] = value
    return rows


def baseline():
    return run()


def q1():
    all_x = run(mutate(2, 'x'))
    id3 = run(mutate(2, 'x', '3'))
    all_tbd = run(mutate(2, 'TBD'))
    id3_tbd = run(mutate(2, 'TBD', '3'))
    return {'all_col3_x': all_x, 'id3_col3_x': id3,
            'all_col3_TBD_negctl': all_tbd, 'id3_col3_TBD_negctl': id3_tbd}


def q2():
    a = 'ANCHOR-X'
    all_a = run(mutate(3, a))
    id3 = run(mutate(3, a, '3'))
    all_tbd = run(mutate(3, 'TBD'))
    id3_tbd = run(mutate(3, 'TBD', '3'))
    return {'all_col4_anchorx': all_a, 'id3_col4_anchorx': id3,
            'all_col4_TBD_negctl': all_tbd, 'id3_col4_TBD_negctl': id3_tbd}


def q3():
    ok = run(mutate(1, '§2.14'))
    bad = run(mutate(1, '§2.999'))
    one = run(mutate(1, '§2.999', '4'))
    return {'all_col2_real_2_14': ok, 'all_col2_missing_2_999': bad,
            'id4_col2_2_999_ctl': one}


def q4():
    yes = [r[0] for r in ROWS if r[6].strip().startswith('有')]
    no = [r[0] for r in ROWS if r[6].strip().startswith('无')]
    res = {'a_yes_to_none': [], 'b_no_to_yes': [], 'c_no_to_alt_none': []}
    for i in yes:
        r = run(mutate(6, '无（探针）', i))
        res['a_yes_to_none'].append({'id': i, 'exit': r['exit'], 'first_fail': r['fails'][0] if r['fails'] else ''})
    for i in no:
        r = run(mutate(6, '有（探针）', i))
        res['b_no_to_yes'].append({'id': i, 'exit': r['exit'], 'first_fail': r['fails'][0] if r['fails'] else ''})
    for i in no:
        r = run(mutate(6, '无（探针措辞不同）', i))
        res['c_no_to_alt_none'].append({'id': i, 'exit': r['exit'], 'first_fail': r['fails'][0] if r['fails'] else ''})
    return res


def main():
    restore()
    result = {'baseline_sha256': hashlib.sha256(PRISTINE).hexdigest(),
              'ids': IDS,
              'baseline': baseline(), 'q1': q1(), 'q2': q2(), 'q3': q3(), 'q4': q4()}
    restore()
    assert io.open(TSV, 'rb').read() == PRISTINE
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'r103_results.json')
    io.open(out, 'w', encoding='utf-8').write(json.dumps(result, ensure_ascii=False, indent=2))
    print('wrote', out)
    for k in ('baseline','q1','q2','q3'):
        v = result[k]
        if k == 'baseline':
            print(k, 'exit', v['exit'], 'fails', v['fails'][:3])
        else:
            for sk, sv in v.items():
                print(k, sk, 'exit', sv['exit'], 'n_fail', len(sv['fails']), 'first', sv['fails'][0] if sv['fails'] else '')
    for k, rows in result['q4'].items():
        print(k, 'nonzero', sum(1 for x in rows if x['exit'] != 0))
        for x in rows:
            print(' ', x['id'], x['exit'], x['first_fail'][:110])

if __name__ == '__main__':
    main()
