# -*- coding: utf-8 -*-
"""M83 phase 1 (READ ONLY for coverage/PANEL): record BEFORE state, find the 13 remaining
R_MISSING rows on current disk, do suffix candidate scan + subsystem disambiguation.

The 13 target rows are exactly those still classified R_MISSING by EVID_RESOLVE/resolve.py's
logic on the CURRENT coverage.tsv (M82 fixed 361 unique ones; the 13 ambiguous remain).
Trace-only rows (classification_trace) are R_TRACE_ONLY, not R_MISSING, so excluded.

Writes only to MERGE_M83.
"""
import os, re, json, hashlib, datetime, importlib.util

R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
PAN = os.path.join(R14, 'COVERAGE', 'PANEL.md')
MERGE = os.path.join(R14, 'MERGE_M83')
RESOLVE_PY = os.path.join(R14, 'EVID_RESOLVE', 'resolve.py')
TZ = datetime.timezone(datetime.timedelta(hours=8))

SPLIT_RE = re.compile(r'[;,|]')
SPLIT_KEEP_RE = re.compile(r'([;,|])')
ABS_RE = re.compile(r'^(?:[A-Za-z]:[\\/]|\\\\|/)')
LINESPEC_RE = re.compile(r':(?:\d+[0-9A-Za-z\-]*|0x[0-9A-Fa-f\-]+)$')


def state(path):
    st = os.stat(path)
    b = open(path, 'rb').read()
    return {'mtime': st.st_mtime,
            'mtime_iso': datetime.datetime.fromtimestamp(st.st_mtime, TZ).isoformat(),
            'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest(), 'data': b}


# load resolver functions
spec = importlib.util.spec_from_file_location('resolver', RESOLVE_PY)
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)


def main():
    os.makedirs(MERGE, exist_ok=True)
    before_cov = state(COV)
    before_pan = state(PAN)
    bs = {'coverage.tsv': {k: before_cov[k] for k in ['mtime', 'mtime_iso', 'bytes', 'sha256']},
          'PANEL.md': {k: before_pan[k] for k in ['mtime', 'mtime_iso', 'bytes', 'sha256']},
          'timezone': 'Asia/Shanghai (+08:00)',
          'note': 'collected before any write in this round (re-collected; identical to first sample)'}
    with open(os.path.join(MERGE, '_before_state.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(bs, f, ensure_ascii=False, indent=2); f.write('\n')
    print('BEFORE coverage.tsv:', json.dumps(bs['coverage.tsv'], ensure_ascii=False))
    print('BEFORE PANEL.md    :', json.dumps(bs['PANEL.md'], ensure_ascii=False))

    b = before_cov['data']
    assert b[:3] != b'\xef\xbb\xbf' and b'\r\n' not in b and not b.endswith(b'\n')
    lines = b.decode('utf-8').split('\n')
    header = lines[0].split(',')
    assert header == ['entry', 'subsystem', 'name', 'one_line_semantics', 'grade',
                      'evidence_path', 'n_sources', 'conflict'], header
    rows = [ln.split('\t') for ln in lines[1:]]
    assert len(rows) == 18498, len(rows)
    assert all(len(r) == 8 for r in rows)
    assert sum(1 for r in rows if r[4] == '[已证]') == 1654

    # bases identical to resolve.py
    repo = os.path.dirname(os.path.dirname(R14))
    lead = os.path.join(repo, 'lead')
    bases = [("r14", R14), ("lead", lead), ("repo", repo)]
    bases_present = [(n, p) for n, p in bases if os.path.isdir(p)]

    # index all files under r14 by posix rel path (same as M82)
    file_relpaths = []
    for root, dirs, files in os.walk(R14):
        for fn in files:
            rel = os.path.relpath(os.path.join(root, fn), R14).replace('\\', '/')
            file_relpaths.append(rel)

    def suffix_candidates(relpath):
        rp = relpath.replace('\\', '/').strip('/').lower()
        suffix = '/' + rp
        return sorted(p for p in file_relpaths if p.lower() == rp or p.lower().endswith(suffix))

    # find [已证] rows that are still R_MISSING on current disk
    missing_rows = []
    klass_count = {}
    for i, r in enumerate(rows):
        if r[4] != '[已证]':
            continue
        res = resolver.resolve_row(r[5], bases_present)
        klass_count[res['class']] = klass_count.get(res['class'], 0) + 1
        if res['class'] == 'R_MISSING':
            missing_rows.append((i, r, res))
    print('current [已证] classification:', klass_count)
    print('R_MISSING rows on current disk:', len(missing_rows))

    # for each R_MISSING row, suffix-match each non-trace part and check ambiguity
    ambig = []
    for i, r, res in missing_rows:
        val = r[5]
        assert 'M82 指针修复' not in val, ('fixed row still missing?', r[0])
        toks = [t for t in SPLIT_KEEP_RE.split(val.strip()) if t != '']
        parts = [t for t in toks if not SPLIT_RE.fullmatch(t)]
        cands_by_part = {}
        multi = False
        for p in parts:
            rel = resolver.strip_anchor(p)
            if not rel or resolver.is_trace(p):
                continue
            hits = suffix_candidates(rel)
            cands_by_part[p] = hits
            if len(hits) > 1:
                multi = True
        # every remaining R_MISSING row should be suffix-ambiguous
        assert multi, ('R_MISSING row not suffix-ambiguous?', r[0], val)
        ambig.append({'row_index': i, 'entry': r[0], 'subsystem': r[1], 'name': r[2],
                      'semantics': r[3], 'grade': r[4], 'evidence_path': val,
                      'n_sources': r[6], 'conflict': r[7],
                      'parts': parts, 'parts_candidates': cands_by_part})

    print('\nAMBIGUOUS R_MISSING ROWS FOUND:', len(ambig))
    for a in ambig:
        print('  %s  sub=%-4s  %s' % (a['entry'], a['subsystem'], a['evidence_path']))
        for p, hits in a['parts_candidates'].items():
            if len(hits) > 1:
                print('      candidates(%d): %s' % (len(hits), hits))

    # ---- subsystem disambiguation ----
    def dirs_of(path):
        comps = path.split('/')
        return [c for c in comps[:-1] if c]

    detail = []
    for a in ambig:
        subsys = a['subsystem'].strip().upper()
        old_val = a['evidence_path']
        # rebuild preserving separators; change only ambiguous parts
        toks = [t for t in SPLIT_KEEP_RE.split(old_val.strip()) if t != '']
        out = []
        part_iter = iter(a['parts'])
        per_part = []
        fixable = True
        for tok in toks:
            if SPLIT_RE.fullmatch(tok):
                out.append(tok)
                continue
            p = next(part_iter)
            hits = a['parts_candidates'].get(p)
            if hits is None:  # trace part or empty -> keep verbatim
                out.append(p)
                continue
            if len(hits) <= 1:
                out.append(p)
                per_part.append({'part': p, 'hits': hits, 'kept': hits, 'status': 'unique'})
                continue
            kept = [h for h in hits if any(subsys in d.upper() for d in dirs_of(h))]
            if len(kept) == 1:
                rel = resolver.strip_anchor(p)
                suffix = p[len(rel):]
                newp = kept[0] + suffix
                out.append(newp)
                per_part.append({'part': p, 'hits': hits, 'kept': kept, 'status': 'fixed', 'new_part': newp})
            else:
                out.append(p)
                per_part.append({'part': p, 'hits': hits, 'kept': kept, 'status': 'unresolved'})
                fixable = False
        new_main = ''.join(out)
        detail.append({'entry': a['entry'], 'subsystem': subsys, 'name': a['name'],
                       'grade': a['grade'], 'old_value': old_val, 'fixable': fixable,
                       'new_path': new_main, 'per_part': per_part,
                       'conflict': a['conflict'], 'semantics': a['semantics']})

    fixed = [d for d in detail if d['fixable']]
    unresolved = [d for d in detail if not d['fixable']]
    print('\nDISAMBIGUATION RESULT: fixed=%d unresolved=%d total=%d' % (len(fixed), len(unresolved), len(detail)))
    for d in detail:
        tag = 'FIX' if d['fixable'] else 'UNRESOLVED'
        keeps = [pp['kept'] for pp in d['per_part'] if pp.get('status') in ('fixed', 'unresolved')]
        print('  [%-10s] %s sub=%-4s kept=%s' % (tag, d['entry'], d['subsystem'], keeps))
        print('        new_path=%s' % d['new_path'])

    # cross-check against M82's recorded ambiguous list
    m82_list = set('0040F870 004DF320 004DF3A0 004DFB70 004DFCB0 004DFE00 004E0E80 '
                   '0054E890 0054EA70 006B6EA0 006B6FA0 006CDEF0 006F4960'.split())
    found = set(a['entry'] for a in ambig)
    print('\ncross-check vs M82 13-list: match=%s (missing=%s extra=%s)' % (
        found == m82_list, sorted(m82_list - found), sorted(found - m82_list)))

    out = {'before': bs, 'current_classification': klass_count,
           'ambiguous_count': len(ambig), 'ambiguous_entries': [a['entry'] for a in ambig],
           'detail': detail, 'fixed_entries': [d['entry'] for d in fixed],
           'unresolved_entries': [d['entry'] for d in unresolved],
           'm82_list_match': found == m82_list}
    with open(os.path.join(MERGE, '_analysis.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=2); f.write('\n')

    if len(ambig) != 13 or found != m82_list:
        print('\n!!! STOP: expected 13 ambiguous rows matching M82 list')
    else:
        print('\nOK: exactly 13 ambiguous R_MISSING rows found, matching M82 list.')


if __name__ == '__main__':
    main()
