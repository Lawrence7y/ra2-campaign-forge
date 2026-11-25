# -*- coding: utf-8 -*-
"""r134ds_t6.py -- T6 evaluation of FIX-1 and FIX-2.  Nothing under lead/ is touched.

What is measured, not assumed:
  (ii) breakage: the two halves of FIX-1 applied to the 31 existing rows as a DATA test
       (nullability, and hits-on-own-product == 1), plus whether the shipped C7c block
       actually contains both halves.
  (iii) cost: wall time of the C7+C7b gate vs the C7+C7b+C7c+C7d gate (N=5 each),
       plus isolated cost of the C7c and C7d operations.
  (iv) what FIX-1 still misses: a NON-NULLABLE, exactly-one-hit pattern that is true on
       every one of the 23 candidate files -- i.e. it defeats both halves of FIX-1.
       Measured against all 23 files, not argued.
"""
import io, json, os, re, statistics, sys, time, timeit
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r134ds_lib as L

OUT = {}
S = L.SNAP
P = os.path.join(S, 'check_disc.R133_prefix.py')
N = os.path.join(S, 'check_disc.R134_final.py')
TP = os.path.join(S, 'DISC_RECHECK.R133pair.tsv')
TN = os.path.join(S, 'DISC_RECHECK.R134.tsv')

hdr, rows = L.read_rows(os.path.join(L.ROOT, 'lead', 'next_re_20261117_r14'))
paths = L.all_paths(rows)

# ---------- (ii-a) does the shipped C7c implement FIX-1 fully? ----------
src_n = io.open(N, encoding='utf-8').read()
OUT['shipped'] = {
    'C7c_present': 'C7c' in src_n,
    'C7c_has_nullability_clause': 're.search(pat, \'\', re.M)' in src_n,
    'C7c_has_exactly_one_clause': bool(re.search(r'hit.{0,20}==\s*1|!=\s*1\b', src_n)),
    'C7d_present': 'C7d' in src_n,
    'C7d_sha_pinned': 'C7_TEXT_SHA256' in src_n,
    'C7c_note': 'C7c vacuity pre-filter' in src_n,
}
print('shipped gate: C7c=%s  nullability-clause=%s  exactly-one-clause=%s  C7d=%s'
      % (OUT['shipped']['C7c_present'], OUT['shipped']['C7c_has_nullability_clause'],
         OUT['shipped']['C7c_has_exactly_one_clause'], OUT['shipped']['C7d_present']))

# ---------- (ii-b) FIX-1 half 1: nullability over the 31 rows ----------
null_ids = []
for r in rows:
    e = r[5].strip()
    if e.startswith('grep='):
        pat = e[len('grep='):].strip()
    else:
        m = re.fullmatch(r'grepcount=(.*)=(\d+)$', e, re.S)
        if not m:
            continue
        pat = m.group(1)
    try:
        if re.search(pat, '', re.M):
            null_ids.append(r[0])
    except re.error:
        pass
OUT['fix1_nullable_breaks'] = null_ids
print('FIX-1 half1 (reject nullable) breaks ids:', null_ids or 'NONE (0 of 31)')

# ---------- (ii-c) FIX-1 half 2: grep= hits on own product must be exactly 1 ----------
h_break, h_all = [], {}
for r in rows:
    e = r[5].strip()
    p = r[4].strip().replace('\\', '/')
    if e.startswith('grep='):
        n = L.hit_count(p, e)
        h_all[r[0]] = n
        if n != 1:
            h_break.append((r[0], n))
OUT['fix1_exactly1_breaks_grep'] = h_break
print('FIX-1 half2 (grep= hits==1) breaks ids:', h_break or 'NONE')
gcb = []
for r in rows:
    e = r[5].strip()
    if e.startswith('grepcount='):
        p = r[4].strip().replace('\\', '/')
        n = L.hit_count(p, e)
        if n != 1:
            gcb.append((r[0], n, e))
OUT['fix1_exactly1_breaks_grepcount_if_applied'] = gcb
print('FIX-1 half2 if ALSO applied to grepcount rows, breaks:', gcb)

# ---------- (iv) FIX-1 is defeatable: non-nullable, exactly-1-hit, true on all 23 ----------
PROBE = r'(?s)\A.'
probe = {'pattern': PROBE}
try:
    probe['nullable'] = re.search(PROBE, '', re.M) is not None
except re.error as e:
    probe['nullable'] = 'ERR %s' % e
hits = {}
for p in paths:
    hits[p] = L.hit_count(p, 'grep=' + PROBE)
probe['hits_per_file'] = hits
probe['files_with_hit'] = sum(1 for v in hits.values() if (v or 0) > 0)
probe['n_files'] = len(paths)
probe['distinct_hit_counts'] = sorted(set(v for v in hits.values()))
probe['survives_fix1'] = (probe['nullable'] is False and
                          probe['distinct_hit_counts'] == [1] and
                          probe['files_with_hit'] == len(paths))
OUT['fix1_defeat_probe'] = probe
print('FIX-1 defeat probe %r: nullable=%s hits/file distinct=%s files_with_hit=%d/%d '
      '=> survives both FIX-1 clauses: %s'
      % (PROBE, probe['nullable'], probe['distinct_hit_counts'], probe['files_with_hit'],
         len(paths), probe['survives_fix1']))

# ---------- (iii) cost: wall time, N runs each ----------
def time_gate(tag, gate_src, tsv_src, runs=5):
    r14 = L.build_sandbox('t6_' + tag, gate_src, tsv_src)
    ts, rcs = [], []
    for _ in range(runs):
        t0 = time.perf_counter()
        rc, fails, notes, out = L.gate(r14)
        ts.append(time.perf_counter() - t0)
        rcs.append(rc)
    return {'runs': runs, 'exit_codes': rcs, 'times_s': [round(x, 4) for x in ts],
            'min_s': round(min(ts), 4), 'median_s': round(statistics.median(ts), 4),
            'max_s': round(max(ts), 4)}


OUT['cost'] = {'P_C7_C7b': time_gate('P', P, TP), 'N_C7_C7b_C7c_C7d': time_gate('N', N, TN)}
print('\ncost P (C7+C7b)        : min=%.3fs median=%.3fs  exits=%s'
      % (OUT['cost']['P_C7_C7b']['min_s'], OUT['cost']['P_C7_C7b']['median_s'],
         OUT['cost']['P_C7_C7b']['exit_codes']))
print('cost N (C7+C7b+C7c+C7d): min=%.3fs median=%.3fs  exits=%s'
      % (OUT['cost']['N_C7_C7b_C7c_C7d']['min_s'], OUT['cost']['N_C7_C7b_C7c_C7d']['median_s'],
         OUT['cost']['N_C7_C7b_C7c_C7d']['exit_codes']))
delta = OUT['cost']['N_C7_C7b_C7c_C7d']['median_s'] - OUT['cost']['P_C7_C7b']['median_s']
OUT['cost']['delta_median_s'] = round(delta, 4)
print('delta median = %+.4fs' % delta)

# isolated cost of the two new blocks
pats = []
for r in rows:
    e = r[5].strip()
    if e.startswith('grep='):
        pats.append(e[len('grep='):].strip())
    else:
        m = re.fullmatch(r'grepcount=(.*)=(\d+)$', e, re.S)
        if m:
            pats.append(m.group(1))
t_c7c = timeit.timeit(lambda: [re.search(p, '', re.M) for p in pats], number=100) / 100
blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in rows if len(r) == 7)


def c7d_work():
    import hashlib
    h = hashlib.sha256(blob.encode('utf-8')).hexdigest()
    return h


t_c7d = timeit.timeit(c7d_work, number=100) / 100
OUT['cost']['isolated'] = {'c7c_nullability_s': t_c7c, 'c7d_fingerprint_s': t_c7d,
                           'c7c_patterns': len(pats)}
print('isolated: C7c nullability over %d patterns = %.6fs ; C7d sha256 over 31 rows = %.6fs'
      % (len(pats), t_c7c, t_c7d))

# ---------- (ii-d) FIX-2 on the 31 existing rows: does the pin match today's table? ----------
blob_now = blob
OUT['fix2'] = {'computed_sha256': c7d_work()}
rc, fails, notes, out = L.gate(L.build_sandbox('t6_fix2check', N, TN))
OUT['fix2']['gate_exit_on_current_pair'] = rc
OUT['fix2']['c7d_note'] = [n for n in notes if 'C7d' in n]
print('\nFIX-2 (C7d as shipped) on the current pair: exit=%s ; %s'
      % (rc, OUT['fix2']['c7d_note']))

json.dump(OUT, io.open(os.path.join(L.HERE, 'r134ds_t6.json'), 'w'),
          ensure_ascii=False, indent=1)
print('wrote r134ds_t6.json')
