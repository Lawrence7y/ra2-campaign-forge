# -*- coding: utf-8 -*-
"""r134ds_t6b.py -- does FIX-1 close HOLE A?  Measured, not argued.

FIX-1 has two clauses: (1) reject a pattern that matches the empty string;
(2) reject a grep= whose hit count on its OWN product is not exactly 1.
Clause (2) is a property of the pattern/product pair.  If an ALTERNATE product also gives
exactly 1 hit, clause (2) cannot tell the two apart -- HOLE A survives.

Also measures: with C7d deliberately re-pinned (which FIX-2 says must be done by hand for
any deliberate table edit), does the redirected row go green again?  That is the honest
statement of what FIX-2 buys.
"""
import hashlib, io, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r134ds_lib as L

OUT = {}
S = L.SNAP
N = os.path.join(S, 'check_disc.R134_final.py')
TN = os.path.join(S, 'DISC_RECHECK.R134.tsv')

hdr, rows = L.read_rows(os.path.join(L.ROOT, 'lead', 'next_re_20261117_r14'))
paths = L.all_paths(rows)

# ---- for every row with a >=2 true-set, does the alternative keep "exactly 1 hit"? ----
OUT['rows'] = {}
survivors = []
for r in rows:
    rid, own, expr = r[0], r[4].strip().replace('\\', '/'), r[5].strip()
    ok, _ = L.run_expr(own, expr)
    true_set = [p for p in paths if L.run_expr(p, expr)[0] is True]
    if len(true_set) < 2:
        continue
    hits = dict((p, L.hit_count(p, expr)) for p in true_set)
    pat = None
    if expr.startswith('grep='):
        pat = expr[len('grep='):].strip()
    else:
        m = re.fullmatch(r'grepcount=(.*)=(\d+)$', expr, re.S)
        pat = m.group(1) if m else None
    nullable = None
    if pat is not None:
        try:
            nullable = re.search(pat, '', re.M) is not None
        except re.error:
            nullable = None
    alts_one_hit = [p for p in true_set if p != own and hits.get(p) == 1]
    rec = {'shape': expr.split(' ')[0], 'expr': expr, 'own': own,
           'own_hits': hits.get(own),
           'hits': hits, 'nullable': nullable,
           'alts_with_exactly_1_hit': alts_one_hit,
           'survives_fix1_both_clauses': bool(nullable is False and alts_one_hit)}
    OUT['rows'][rid] = rec
    if rec['survives_fix1_both_clauses']:
        survivors.append(rid)
    print('id=%-3s nullable=%-5s own_hits=%-3s alts_with_exactly_1_hit=%d  survives FIX-1: %s'
          % (rid, nullable, hits.get(own), len(alts_one_hit),
             rec['survives_fix1_both_clauses']))
    for p in alts_one_hit:
        print('        alt %s hits=1' % p)

OUT['survivors_of_fix1'] = sorted(survivors, key=int)
OUT['n_survivors'] = len(survivors)
print('\nHOLE A rows that survive BOTH FIX-1 clauses: %d  ids=%s'
      % (len(survivors), sorted(survivors, key=int)))

# ---- concrete: redirect the first survivor while C7d is deliberately re-pinned ----
if survivors:
    rid = sorted(survivors, key=int)[0]
    alt = OUT['rows'][rid]['alts_with_exactly_1_hit'][0]
    own = OUT['rows'][rid]['own']
    r14 = L.build_sandbox('t6b_repin', N, TN)
    hdr, rowsx = L.read_rows(r14)
    for r in rowsx:
        if r[0] == rid:
            r[4] = alt.replace('/', '\\')
    L.write_rows(r14, hdr, rowsx)
    # deliberate re-pin of C7d, exactly as FIX-2 requires for a deliberate edit
    src = io.open(os.path.join(r14, 'check_disc.py'), encoding='utf-8').read()
    blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip())
                     for r in rowsx if len(r) == 7)
    newsha = hashlib.sha256(blob.encode('utf-8')).hexdigest()
    rowsha = dict((r[0], hashlib.sha256(('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()))
                                       .encode('utf-8')).hexdigest()) for r in rowsx if len(r) == 7)
    src = re.sub(r"C7_TEXT_SHA256 = '[0-9a-f]{64}'", "C7_TEXT_SHA256 = '%s'" % newsha, src)
    src = re.sub(r"C7_ROW_SHA = \{[^}]*\}",
                 'C7_ROW_SHA = ' + repr(rowsha).replace('"', "'"), src, count=1)
    io.open(os.path.join(r14, 'check_disc.py'), 'w', encoding='utf-8').write(src)
    rc, fails, notes, out = L.gate(r14)
    OUT['repin_demo'] = {'id': rid, 'from': own, 'to': alt, 'exit': rc,
                         'fails': fails, 'n_fails': len(fails),
                         'c7line': [l for l in out.split('\n')
                                    if l.startswith('C7 live-checks')],
                         'c7d_note': [n for n in notes if 'C7d' in n],
                         'c7c_note': [n for n in notes if 'C7c' in n]}
    print('\nREDIRECT id=%s %s -> %s with C7d re-pinned: measured exit=%s fails=%d'
          % (rid, own, alt, rc, len(fails)))
    for f in fails:
        print('   ', f[:180])
    for l in OUT['repin_demo']['c7line']:
        print('   ', l)
    for l in OUT['repin_demo']['c7d_note']:
        print('   ', l)

json.dump(OUT, io.open(os.path.join(L.HERE, 'r134ds_t6b.json'), 'w'),
          ensure_ascii=False, indent=1)
print('\nwrote r134ds_t6b.json')
