# -*- coding: utf-8 -*-
"""r134ds_t5.py -- T5 vacuity of the EXISTING 31 expressions.

(a) for every grep= / grepcount= row, does the pattern match the empty string under re.M?
    claim to check: nullable count == 0.
(b) for every row, how many of the 23 distinct col5 candidate files its expression matches.
    a count of 23 means the expression is insensitive to which file it is pointed at.

re.M is what the gate uses (re.findall(pat, text, re.M)).  For the empty string re.M is
immaterial, but the flag is kept so the comparison is on the gate's terms.
Also probed: re.search(pat, '', re.M) [the C7c criterion] vs re.fullmatch / a leading-anchor
analysis, so a "0 nullable" result can be attributed to the right reason rather than luck.
"""
import io, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r134ds_lib as L

hdr, rows = L.read_rows(os.path.join(L.ROOT, 'lead', 'next_re_20261117_r14'))
paths = L.all_paths(rows)

OUT = {'n_rows': len(rows), 'n_paths': len(paths), 'rows': {}}
nullable, regex_rows = [], 0
by_shape = {}

for r in rows:
    assert len(r) == 7
    rid, path, expr = r[0], r[4].strip().replace('\\', '/'), r[5].strip()
    head = expr.split(' ')[0]
    shape = ('grep=' if head.startswith('grep=') else
             'grepcount=' if head.startswith('grepcount=') else
             'rows=' if head.startswith('rows=') else
             'exists' if head == 'exists' else
             'bytes=' if head.startswith('bytes=') else
             'none' if head == 'none' else 'OTHER')
    by_shape[shape] = by_shape.get(shape, 0) + 1
    rec = {'shape': shape, 'expr': expr, 'path': path}
    if shape in ('grep=', 'grepcount='):
        regex_rows += 1
        if shape == 'grep=':
            pat = expr[len('grep='):].strip()
        else:
            m = re.fullmatch(r'grepcount=(.*)=(\d+)$', expr, re.S)
            assert m, expr
            pat = m.group(1)
        rec['pattern'] = pat
        try:
            rec['nullable_search'] = re.search(pat, '', re.M) is not None
            rec['nullable_findall'] = len(re.findall(pat, '', re.M)) > 0
            # a second, independent criterion: is the pattern anchored at a non-empty literal?
            rec['fullmatch_empty'] = re.fullmatch(pat, '', re.M) is not None
        except re.error as e:
            rec['regex_error'] = str(e)
            rec['nullable_search'] = None
        if rec.get('nullable_search'):
            nullable.append(rid)
        # hit count on its own product (FIX-1's "exactly 1" criterion)
        rec['hits_own'] = L.hit_count(path, expr)
    # (b) match count over the 23 candidate files
    hits, true_set = {}, []
    for p in paths:
        ok, det = L.run_expr(p, expr)
        if ok is True:
            true_set.append(p)
        hits[p] = L.hit_count(p, expr)
    rec['true_set_size'] = len(true_set)
    rec['true_set'] = true_set
    rec['own_true'] = path in true_set
    rec['hits_across_paths'] = hits
    # for regex shapes: how many files have >=1 hit
    if shape in ('grep=', 'grepcount='):
        rec['files_with_hit'] = sum(1 for p in paths if (hits[p] or 0) > 0)
    OUT['rows'][rid] = rec

OUT['nullable_ids'] = nullable
OUT['n_nullable'] = len(nullable)
OUT['n_regex_rows'] = regex_rows
OUT['shape_census'] = by_shape

print('rows=%d distinct_col5=%d regex_rows=%d' % (len(rows), len(paths), regex_rows))
print('shape census:', dict(sorted(by_shape.items())))
print('nullable patterns (match empty under re.M): %d  ids=%s'
      % (len(nullable), nullable))
print()
print('%-4s %-11s %-6s %-6s %-6s %-6s %s'
      % ('id', 'shape', 'own_ok', 'set', 'hits', 'files', 'expr'))
for rid in sorted(OUT['rows'], key=lambda x: int(x)):
    v = OUT['rows'][rid]
    print('%-4s %-11s %-6s %-6d %-6s %-6s %s'
          % (rid, v['shape'], v['own_true'], v['true_set_size'],
             v.get('hits_own', '-'), v.get('files_with_hit', '-'), v['expr'][:46]))
print()
full = [rid for rid, v in OUT['rows'].items() if v['true_set_size'] == len(paths)]
OUT['rows_matching_all_23'] = sorted(full, key=int)
print('rows whose expression matches ALL %d candidate files: %d  ids=%s'
      % (len(paths), len(full), sorted(full, key=int)))
print('rows whose own product is NOT in its own true-set (own check failing):',
      [rid for rid, v in OUT['rows'].items() if not v['own_true']])

json.dump(OUT, io.open(os.path.join(L.HERE, 'r134ds_t5.json'), 'w'),
          ensure_ascii=False, indent=1)
print('wrote r134ds_t5.json')
