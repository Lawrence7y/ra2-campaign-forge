# -*- coding: utf-8 -*-
"""r134ds_t7b.py -- two stronger T7 probes.

H1R  H1 re-run against a REAL product (rows= row 22, should_exclude.tsv) instead of a
     synthesized file: the product is copied inside the sandbox and the symlink for that
     one path is removed, so nothing under lead/ is written.
H5   The C7b census pins COUNTS, not ASSIGNMENT.  If two rows exchange shapes the census
     is unchanged.  Demo: row 22 (rows=1468) becomes grep=<literal hit in its product>,
     and row 7 (grep=REFUTED-OVERSTRICT) becomes rows=<line count of its product>.
     Both new expressions are TRUE on their own products, so C7 stays green.
"""
import hashlib, io, json, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r134ds_lib as L

OUT = {}
S = L.SNAP
GATES = {'P_R133': os.path.join(S, 'check_disc.R133_prefix.py'),
         'N_R134': os.path.join(S, 'check_disc.R134_final.py')}
TSVR = os.path.join(S, 'DISC_RECHECK.R134.tsv')
TSVP = os.path.join(S, 'DISC_RECHECK.R133pair.tsv')


def tsv_for(tag):
    return TSVP if tag == 'P_R133' else TSVR


def sb_root_of(r14):
    return os.path.dirname(os.path.dirname(r14))


# ---------------- H1R: real product, copied in-sandbox ----------------
REL = 'lead/next_re_20261117_r14/R17_R84_T1_NARRATIVE/should_exclude.tsv'
REAL = os.path.join(L.ROOT, REL)
OUT['H1R'] = {'product': REL, 'real_bytes': os.path.getsize(REAL), 'runs': {}, 'control': {}}

for tag, g in GATES.items():
    sb = sb_root_of(L.build_sandbox('t7b_v_' + tag, g, tsv_for(tag)))
    ap = os.path.join(sb, REL)
    assert os.path.islink(ap), 'expected a symlink at %s' % ap
    os.remove(ap)
    shutil.copy2(REAL, ap)
    assert not os.path.islink(ap) and os.path.isfile(ap)
    for i in range(5):
        with io.open(ap, 'a', encoding='utf-8', newline='\n') as f:
            f.write('DISC_RECHECK appended row %d\tx\ty\n' % i)
    grew = os.path.getsize(ap)
    r14 = os.path.dirname(ap)
    rc, fails, notes, out = L.gate(r14)
    OUT['H1R']['runs'][tag] = {
        'exit': rc, 'fails': fails, 'n_fails': len(fails), 'bytes_after': grew,
        'real_bytes_unchanged': os.path.getsize(REAL) == OUT['H1R']['real_bytes'],
        'c7line': [l for l in out.split('\n') if l.startswith('C7 live-checks')]}
    print('H1R [%s] real product copied in-sandbox, +5 "DISC_RECHECK"-prefixed lines '
          '(%d -> %d B): exit=%s fails=%d'
          % (tag, OUT['H1R']['real_bytes'], grew, rc, len(fails)))
    for f in fails:
        print('    ', f[:170])

    # control: same count of lines, no magic prefix
    sb2 = sb_root_of(L.build_sandbox('t7b_c_' + tag, g, tsv_for(tag)))
    ap2 = os.path.join(sb2, REL)
    os.remove(ap2)
    shutil.copy2(REAL, ap2)
    for i in range(5):
        with io.open(ap2, 'a', encoding='utf-8', newline='\n') as f:
            f.write('ordinary row %d\tx\ty\n' % i)
    rc, fails, notes, out = L.gate(os.path.dirname(ap2))
    OUT['H1R']['control'][tag] = {'exit': rc, 'n_fails': len(fails), 'fails': fails}
    print('H1R [%s] CONTROL, same 5 lines without the prefix: exit=%s fails=%d'
          % (tag, rc, len(fails)))
    for f in fails:
        print('    ', f[:170])

assert os.path.getsize(REAL) == OUT['H1R']['real_bytes'], 'REAL PRODUCT WAS MODIFIED'
print('real product size still %d B -- untouched' % os.path.getsize(REAL))

# ---------------- H5: shape permutation keeps the census ----------------
hdr, rows = L.read_rows(os.path.join(L.ROOT, 'lead', 'next_re_20261117_r14'))
byid = dict((r[0], r) for r in rows)

# row 22: rows=1468 -> grep=<a literal that occurs in its product>
p22 = byid['22'][4].strip().replace('\\', '/')
abs22 = os.path.join(L.ROOT, p22)
first_data_line = None
with io.open(abs22, encoding='utf-8', errors='replace') as f:
    f.readline()
    first_data_line = f.readline().rstrip('\n')
lit = first_data_line.split('\t')[0].strip()
print('\nH5 literal from %s line 2: %r' % (p22, lit))
new22 = 'grep=' + re.escape(lit)
print('  row22 grep hits on its own product:', L.hit_count(p22, new22))

# row 7: grep=REFUTED-OVERSTRICT -> rows=<lines of its product, same skip rules>
p7 = byid['7'][4].strip().replace('\\', '/')
n7 = L.run_expr(p7, 'rows=0')[1]
actual7 = int(n7.split('=')[1])
new7 = 'rows=%d' % actual7
print('  row7 product %s has %d data rows -> %s' % (p7, actual7, new7))

OUT['H5'] = {'row22_from': byid['22'][5].strip(), 'row22_to': new22,
             'row7_from': byid['7'][5].strip(), 'row7_to': new7, 'runs': {}}
for tag, g in GATES.items():
    r14 = L.build_sandbox('t7b_h5_' + tag, g, tsv_for(tag))
    hdr, rs = L.read_rows(r14)
    for r in rs:
        if r[0] == '22':
            r[5] = new22
        elif r[0] == '7':
            r[5] = new7
    L.write_rows(r14, hdr, rs)
    rc, fails, notes, out = L.gate(r14)
    other = [f for f in fails if 'C7d' not in f]
    OUT['H5']['runs'][tag] = {'exit': rc, 'n_fails': len(fails), 'fails': fails,
                              'fails_excluding_c7d': other,
                              'c7line': [l for l in out.split('\n')
                                         if l.startswith('C7 live-checks')],
                              'c7b': [n for n in notes if 'C7b' in n]}
    print('H5 [%s] two rows exchanged shapes (grep<->rows), both true on own product: '
          'exit=%s fails=%d (excluding C7d: %d)' % (tag, rc, len(fails), len(other)))
    for f in other:
        print('    ', f[:180])
    for l in OUT['H5']['runs'][tag]['c7line']:
        print('    ', l)

json.dump(OUT, io.open(os.path.join(L.HERE, 'r134ds_t7b.json'), 'w'),
          ensure_ascii=False, indent=1)
print('\nwrote r134ds_t7b.json')
