# -*- coding: utf-8 -*-
"""r134ds_t7.py -- T7: holes in C7/C7b that the card did NOT name.

Discipline kept from the failed first draft: no product under lead/ is ever written.
The probe product is a file the probe CREATES inside its own sandbox, and col5 of one row
is pointed at it.  On the R134 gate that edit would trip C7d (the col5/col6 fingerprint),
which is a DIFFERENT mechanism from the hole under test, so for the R134 runs the C7d pin
is recomputed in the sandbox ("deliberately re-pinned") to keep the confound out.

Holes probed:
  H1  the rows= counter is coded to SKIP any line whose stripped form starts with
      'DISC_RECHECK '.  Content added under that prefix is invisible to rows=.
  H2  on rows= rows the '✓(rows N vs N)' annotation is never parsed -- only the exists
      branch reads an annotation.  The recorded second opinion is decoration.
  H3  a bare 'grep=' (empty pattern) is unconditionally true and does NOT disturb the
      C7b shape census.
  H4  col5 may name a file that was never in the product set at all (any path under ROOT).
"""
import hashlib, io, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r134ds_lib as L

OUT = {}
S = L.SNAP
GATES = {'P_R133': os.path.join(S, 'check_disc.R133_prefix.py'),
         'N_R134': os.path.join(S, 'check_disc.R134_final.py')}
TSVR = os.path.join(S, 'DISC_RECHECK.R134.tsv')
TSVP = os.path.join(S, 'DISC_RECHECK.R133pair.tsv')
PROBE_REL = 'lead\\next_re_20261117_r14\\r134ds_probe.tsv'


def tsv_for(tag):
    return TSVP if tag == 'P_R133' else TSVR


def repin_c7d(r14):
    """Recompute C7d's constants inside the sandbox (a deliberate re-pin, as FIX-2 intends).
    Only the sandbox copy of check_disc.py is touched."""
    gp = os.path.join(r14, 'check_disc.py')
    src = io.open(gp, encoding='utf-8').read()
    if 'C7_TEXT_SHA256' not in src:
        return False
    hdr, rows = L.read_rows(r14)
    blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip())
                     for r in rows if len(r) == 7)
    new_sha = hashlib.sha256(blob.encode('utf-8')).hexdigest()
    rowsha = {}
    for r in rows:
        if len(r) == 7:
            rowsha[r[0]] = hashlib.sha256(
                ('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip())).encode('utf-8')).hexdigest()
    src = re.sub(r"C7_TEXT_SHA256 = '[0-9a-f]{64}'", "C7_TEXT_SHA256 = '%s'" % new_sha, src)
    src = re.sub(r"C7_ROW_SHA = \{[^}]*\}",
                 'C7_ROW_SHA = ' + repr(rowsha).replace('"', "'"), src, count=1)
    io.open(gp, 'w', encoding='utf-8').write(src)
    return True


def make_probe_sandbox(tag, gate_src, tsv_src, nrows=10, repin=True):
    r14 = L.build_sandbox('t7_' + tag, gate_src, tsv_src)
    abs_p = os.path.join(r14, 'r134ds_probe.tsv')
    assert not os.path.islink(abs_p)
    lines = ['id\tcol_a\tcol_b'] + ['r%d\tv%d\tw%d' % (i, i, i) for i in range(nrows)]
    io.open(abs_p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    hdr, rows = L.read_rows(r14)
    for r in rows:
        if r[0] == '22':
            assert r[5].strip().startswith('rows='), r[5]
            r[4] = PROBE_REL
            r[5] = 'rows=%d' % nrows
    L.write_rows(r14, hdr, rows)
    # verify the gate will find the probe at the path it actually computes (ROOT = sb root)
    sb_root = os.path.dirname(os.path.dirname(r14))
    ap = os.path.join(sb_root, PROBE_REL.replace('\\', '/'))
    assert os.path.isfile(ap) and not os.path.islink(ap), ap
    if repin:
        repin_c7d(r14)
    return r14, abs_p, PROBE_REL


# ---------- setup baseline: probe wiring must be green before any injection ----------
OUT['setup'] = {'runs': {}}
for tag, g in GATES.items():
    r14, abs_p, rel_p = make_probe_sandbox('base_' + tag, g, tsv_for(tag))
    rc, fails, notes, out = L.gate(r14)
    OUT['setup']['runs'][tag] = {'exit': rc, 'fails': fails, 'n_fails': len(fails)}
    print('SETUP [%s] row22 -> own 10-row probe file, nothing injected: exit=%s fails=%d'
          % (tag, rc, len(fails)))
    for f in fails:
        print('    ', f[:170])

# ---------- H1 ----------
OUT['H1'] = {'runs': {}, 'control': {}}
INJECT = 5
for tag, g in GATES.items():
    r14, abs_p, rel_p = make_probe_sandbox('h1a_' + tag, g, tsv_for(tag))
    with io.open(abs_p, 'a', encoding='utf-8', newline='\n') as f:
        for i in range(INJECT):
            f.write('DISC_RECHECK injected %d\n' % i)
    rc, fails, notes, out = L.gate(r14)
    OUT['H1']['runs'][tag] = {'exit': rc, 'fails': fails, 'n_fails': len(fails),
                              'bytes': os.path.getsize(abs_p)}
    print('H1-A [%s] +%d lines prefixed "DISC_RECHECK " : exit=%s fails=%d'
          % (tag, INJECT, rc, len(fails)))
    for f in fails:
        print('    ', f[:170])

    r14, abs_p, rel_p = make_probe_sandbox('h1b_' + tag, g, tsv_for(tag))
    with io.open(abs_p, 'a', encoding='utf-8', newline='\n') as f:
        for i in range(INJECT):
            f.write('ordinary injected %d\n' % i)
    rc, fails, notes, out = L.gate(r14)
    OUT['H1']['control'][tag] = {'exit': rc, 'fails': fails, 'n_fails': len(fails),
                                 'bytes': os.path.getsize(abs_p)}
    print('H1-B [%s] CONTROL +%d plain lines            : exit=%s fails=%d'
          % (tag, INJECT, rc, len(fails)))
    for f in fails:
        print('    ', f[:170])

# ---------- H2 ----------
OUT['H2'] = {'runs': {}}
for tag, g in GATES.items():
    r14, abs_p, rel_p = make_probe_sandbox('h2_' + tag, g, tsv_for(tag), repin=False)
    hdr, rows = L.read_rows(r14)
    for r in rows:
        if r[0] == '22':
            assert r[5].strip() == 'rows=10', r[5]
            r[5] = 'rows=10 ✓(rows 9999 vs 424242) ✓(bytes 7 B)'
    L.write_rows(r14, hdr, rows)
    rc, fails, notes, out = L.gate(r14)
    other = [f for f in fails if 'C7d' not in f]
    OUT['H2']['runs'][tag] = {'exit': rc, 'fails': fails, 'n_fails': len(fails),
                              'fails_excluding_c7d': other}
    print('H2 [%s] rows= annotation now says 9999/424242/7B : exit=%s fails=%d '
          '(excluding C7d fingerprint: %d)' % (tag, rc, len(fails), len(other)))
    for f in other:
        print('    ', f[:170])

# ---------- H3 ----------
OUT['H3'] = {'runs': {}}
for tag, g in GATES.items():
    r14, abs_p, rel_p = make_probe_sandbox('h3_' + tag, g, tsv_for(tag), repin=False)
    hdr, rows = L.read_rows(r14)
    for r in rows:
        if r[0] == '7':
            assert r[5].strip().startswith('grep='), r[5]
            r[5] = 'grep='
    L.write_rows(r14, hdr, rows)
    rc, fails, notes, out = L.gate(r14)
    other = [f for f in fails if 'C7d' not in f]
    OUT['H3']['runs'][tag] = {'exit': rc, 'fails': fails, 'n_fails': len(fails),
                              'fails_excluding_c7d': other,
                              'c7c': [n for n in notes if 'C7c' in n]}
    print('H3 [%s] row 7 col6 = bare "grep=" : exit=%s fails=%d (excluding C7d: %d)'
          % (tag, rc, len(fails), len(other)))
    for f in other:
        print('    ', f[:170])

tf = '/tmp/r134ds_h3_empty.txt'
io.open(tf, 'w').close()
OUT['H3']['empty_file_hits'] = L.hit_count(tf, 'grep=')
OUT['H3']['empty_file_ok'] = L.run_expr(tf, 'grep=')
print('H3 bare "grep=" on a 0-byte file: hits=%s ok=%s (true on ANY file)'
      % (OUT['H3']['empty_file_hits'], OUT['H3']['empty_file_ok']))
os.unlink(tf)

# ---------- H4 ----------
OUT['H4'] = {'runs': {}}
for tag, g in GATES.items():
    r14, abs_p, rel_p = make_probe_sandbox('h4_' + tag, g, tsv_for(tag), repin=True)
    rc, fails, notes, out = L.gate(r14)
    OUT['H4']['runs'][tag] = {'exit': rc, 'fails': fails, 'col5_used': rel_p}
    print('H4 [%s] col5 names a file never in the product set (%s): exit=%s fails=%d'
          % (tag, rel_p, rc, len(fails)))
    for f in fails:
        print('    ', f[:170])

json.dump(OUT, io.open(os.path.join(L.HERE, 'r134ds_t7.json'), 'w'),
          ensure_ascii=False, indent=1)
print('wrote r134ds_t7.json')
