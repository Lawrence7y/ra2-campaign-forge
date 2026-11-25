# -*- coding: utf-8 -*-
"""r134ds_t3.py -- T3 HOLE B (col6 not pinned past its first token) + vacuity proof.

Measured against BOTH gate states because the on-disk gate changed mid-audit:
  P_R133 = gate b99f20ef (C7 + C7b only -- the gate this card describes)
  N_R134 = gate 7d287890 (C7 + C7b + C7c + C7d -- what is actually on disk now)

Variants appended to the recipe's own always-true alternation:
  V1  |(?m:^)     the card's example
  V2  |(?s:.)     NON-nullable always-true-on-any-non-empty-file variant (C7c probe)
"""
import io, json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r134ds_lib as L

OUT = {}
S = L.SNAP
GATES = {'P_R133': os.path.join(S, 'check_disc.R133_prefix.py'),
         'N_R134': os.path.join(S, 'check_disc.R134_final.py')}
TSVR = os.path.join(S, 'DISC_RECHECK.R134.tsv')
TSVP = os.path.join(S, 'DISC_RECHECK.R133pair.tsv')

hdr, rows0 = L.read_rows(os.path.join(L.ROOT, 'lead', 'next_re_20261117_r14'))
ROW = '5'                                  # same row used in T2
base_expr = [r[5].strip() for r in rows0 if r[0] == ROW][0]
own_path = [r[4].strip().replace('\\', '/') for r in rows0 if r[0] == ROW][0]
assert base_expr.startswith('grep='), base_expr
OUT['row'] = {'id': ROW, 'orig_expr': base_expr, 'product': own_path}

VARIANTS = {'V1_nullable': '|(?m:^)', 'V2_nonnullable': '|(?s:.)'}


def append_and_run(tag, gate_src, tsv_src, suffix):
    r14 = L.build_sandbox('t3_' + tag, gate_src, tsv_src)
    hdr, rows = L.read_rows(r14)
    new = None
    for r in rows:
        if r[0] == ROW:
            assert r[5].strip() == base_expr, r[5]
            r[5] = base_expr + suffix
            new = r[5]
    assert new
    L.write_rows(r14, hdr, rows)
    hdr2, rows2 = L.read_rows(r14)
    got = [r[5].strip() for r in rows2 if r[0] == ROW][0]
    assert got == new and got.endswith(suffix)
    rc, fails, notes, out = L.gate(r14)
    return {'expr_used': got, 'exit': rc, 'fails': fails, 'n_fails': len(fails),
            'c7b_lines': [f for f in fails if 'C7b' in f],
            'c7c_lines': [f for f in fails if 'C7c' in f],
            'c7d_lines': [f for f in fails if 'C7d' in f],
            'c7_note': [n for n in notes if n.startswith('NOTE  C7')],
            'c7line': [l for l in out.split('\n') if l.startswith('C7 live-checks')]}


print('row %s orig: %s' % (ROW, base_expr))
OUT['runs'] = {}
for vname, suffix in VARIANTS.items():
    OUT['runs'][vname] = {}
    for tag, g in GATES.items():
        tsv = TSVP if tag == 'P_R133' else TSVR
        d = append_and_run(tag + '_' + vname, g, tsv, suffix)
        OUT['runs'][vname][tag] = d
        print('\n[%s / %s] expr=%s' % (tag, vname, d['expr_used']))
        print('   measured exit=%s fails=%d' % (d['exit'], d['n_fails']))
        for f in d['fails']:
            print('   ', f[:200])

# ---- vacuity proof on a genuinely empty temp file ----
tf = tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, encoding='utf-8')
tf.close()
empty = tf.name
assert os.path.getsize(empty) == 0
OUT['vacuity'] = {'empty_file': empty, 'size': os.path.getsize(empty), 'rows': {}}
print('\n--- vacuity proof on empty file %s (size=%d B) ---' % (empty, 0))
for vname, suffix in VARIANTS.items():
    o_hits = L.hit_count(empty, base_expr)
    a_hits = L.hit_count(empty, base_expr + suffix)
    # also via the gate's own run_expr so the comparison is on the gate's terms
    o_ok, _ = L.run_expr(empty, base_expr)
    a_ok, _ = L.run_expr(empty, base_expr + suffix)
    OUT['vacuity']['rows'][vname] = {'orig_hits': o_hits, 'aug_hits': a_hits,
                                    'orig_ok': o_ok, 'aug_ok': a_ok}
    print('  %-14s ORIGINAL hits=%s ok=%s   AUGMENTED hits=%s ok=%s'
          % (vname, o_hits, o_ok, a_hits, a_ok))

# same proof against the real product, for reference
for vname, suffix in VARIANTS.items():
    print('  %-14s on real product: orig hits=%s  aug hits=%s'
          % (vname, L.hit_count(own_path, base_expr),
             L.hit_count(own_path, base_expr + suffix)))

os.unlink(empty)
json.dump(OUT, io.open(os.path.join(L.HERE, 'r134ds_t3.json'), 'w'),
          ensure_ascii=False, indent=1)
print('\nwrote r134ds_t3.json')
