# -*- coding: utf-8 -*-
"""M82 phase 2 (WRITE): apply pure pointer fixes to coverage.tsv col6 + append M82 note to PANEL.md.

Discipline:
  - only writes COVERAGE/coverage.tsv, COVERAGE/PANEL.md, and MERGE_M82/*
  - no git commit; no touching R14_COMMON / STATUS_BOARD / 台账 / BOARD_ARCHIVE / EVID_RESOLVE / any card dir
  - changes ONLY column 6 (evidence_path) of the 361 uniquely-restorable R_MISSING rows
  - col 1/2/3/4/5/7/8 byte-identical for every row; all other rows byte-identical
"""
import os, re, json, hashlib, datetime, sys

R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
PAN = os.path.join(R14, 'COVERAGE', 'PANEL.md')
RESOLVE = os.path.join(R14, 'EVID_RESOLVE', 'resolve.tsv')
MERGE = os.path.join(R14, 'MERGE_M82')
ATLAS = os.path.join(os.path.dirname(R14), 'next_re_20261112_r10', 'W130_atlas', 'function_atlas.tsv')
TZ = datetime.timezone(datetime.timedelta(hours=8))

SPLIT_RE = re.compile(r'[;,|]')
SPLIT_KEEP_RE = re.compile(r'([;,|])')
ABS_RE = re.compile(r'^(?:[A-Za-z]:[\\/]|\\\\|/)')
LINESPEC_RE = re.compile(r':(?:\d+[0-9A-Za-z\-]*|0x[0-9A-Fa-f\-]+)$')


def strip_anchor(part):
    p = part.split('#', 1)[0].strip()
    if not ABS_RE.match(p):
        p = LINESPEC_RE.sub('', p).strip()
    return p


def state(path):
    st = os.stat(path)
    b = open(path, 'rb').read()
    return {'mtime': st.st_mtime,
            'mtime_iso': datetime.datetime.fromtimestamp(st.st_mtime, TZ).isoformat(),
            'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest(), 'data': b}


def read_cov_raw(path):
    b = open(path, 'rb').read()
    assert b[:3] != b'\xef\xbb\xbf', 'BOM unexpected'
    assert b'\r\n' not in b, 'CRLF unexpected'
    # coverage.tsv has NO trailing newline (last data row ends without \n)
    assert not b.endswith(b'\n'), 'unexpected trailing newline'
    text = b.decode('utf-8')
    lines = text.split('\n')   # no trailing '' because no trailing \n
    header = lines[0].rstrip('\r').split(',')
    assert header == ['entry','subsystem','name','one_line_semantics','grade',
                      'evidence_path','n_sources','conflict'], header
    rows = []
    for i, raw in enumerate(lines[1:], start=2):
        f = raw.rstrip('\r').split('\t')
        assert len(f) == 8, ('bad col count', i, len(f), raw[:100])
        rows.append(f)
    return lines, header, rows


def load_resolve():
    rows = []
    with open(RESOLVE, 'r', encoding='utf-8', newline='') as fh:
        lines = fh.read().split('\n')
    header = lines[0].rstrip('\r').split('\t')
    for raw in lines[1:]:
        raw = raw.rstrip('\r')
        if not raw.strip():
            continue
        f = raw.split('\t')
        assert len(f) == 8
        rows.append(dict(zip(header, f)))
    return rows


def norm_entry(e):
    return ('%08X' % int(e.strip(), 16)).upper()


def load_atlas_set():
    s = set()
    with open(ATLAS, 'r', encoding='utf-8', newline='') as fh:
        lines = fh.read().split('\n')
    for i, raw in enumerate(lines):
        if i == 0 or not raw.strip():
            continue
        f = raw.replace('\r','').split('\t')
        if f and re.match(r'^[0-9A-Fa-f]{8}$', f[0].strip()):
            s.add(norm_entry(f[0]))
    return s


def main():
    before_cov = state(COV)
    before_pan = state(PAN)
    bstate = json.load(open(os.path.join(MERGE, '_before_state.json'), 'r', encoding='utf-8'))
    assert before_cov['sha256'] == bstate['coverage.tsv']['sha256']
    assert before_pan['sha256'] == bstate['PANEL.md']['sha256']

    lines, header, rows = read_cov_raw(COV)
    assert len(rows) == 18498, len(rows)
    n_proved_before = sum(1 for r in rows if r[4] == '[已证]')
    assert n_proved_before == 1654, n_proved_before

    atlas = load_atlas_set()
    n_proved_atlas_before = sum(1 for r in rows if r[4] == '[已证]' and norm_entry(r[0]) in atlas)
    assert n_proved_atlas_before == 1648, n_proved_atlas_before

    # unique-entry check in coverage
    entries = [r[0] for r in rows]
    assert len(set(entries)) == len(entries), 'duplicate entries in coverage.tsv'

    # index files under r14 (case-insensitive suffix matching)
    file_relpaths = []
    for root, dirs, files in os.walk(R14):
        # skip MERGE_M82 and EVID_RESOLVE? No --- they are under r14 too.
        # EVID_RESOLVE REPORT says search under r14; include everything to reproduce counts.
        for fn in files:
            rel = os.path.relpath(os.path.join(root, fn), R14).replace('\\', '/')
            file_relpaths.append(rel)

    def suffix_candidates(relpath):
        relpath = relpath.replace('\\', '/').strip('/').lower()
        suffix = '/' + relpath
        return sorted(p for p in file_relpaths if p.lower() == relpath or p.lower().endswith(suffix))

    resolve_rows = load_resolve()
    missing = [r for r in resolve_rows if r['class'] == 'R_MISSING']
    assert len(missing) == 374

    # classify rows (same as _analyze.py)
    path_hits = {}
    row_candidates = {}   # entry -> list of (part, rel, candidate) for unique rows
    row_class = {}
    for r in missing:
        e = r['entry']
        val = r['evidence_path']
        toks = [t for t in SPLIT_KEEP_RE.split(val) if t != '']
        parts = [t for t in toks if not SPLIT_RE.fullmatch(t)]
        rels = []
        for p in parts:
            rp = strip_anchor(p)
            if rp:
                rels.append(rp)
        assert rels, (e, val)
        cands = []
        ambiguous = False
        for rp in rels:
            if rp not in path_hits:
                path_hits[rp] = suffix_candidates(rp)
            hits = path_hits[rp]
            if len(hits) == 1:
                cands.append(hits[0])
            elif len(hits) > 1:
                ambiguous = True
            else:
                ambiguous = True   # lost -> treat as not-fixable
        if ambiguous:
            row_class[e] = 'ambiguous'
        else:
            row_class[e] = 'unique'
            row_candidates[e] = list(zip(parts, rels, cands))

    rc = {}
    for r in missing:
        rc[r['entry']] = row_class[r['entry']]
    from collections import Counter
    cnt = Counter(rc.values())
    print('row classes:', dict(cnt))
    assert cnt['unique'] == 361 and cnt['ambiguous'] == 13, cnt

    # map entry -> coverage row index
    idx_of = {r[0]: i for i, r in enumerate(rows)}
    for e in rc:
        assert e in idx_of, ('entry missing in coverage', e)

    # cross-check original evidence_path in coverage == resolve.tsv value
    for r in missing:
        e = r['entry']
        cov_val = rows[idx_of[e]][5]
        assert cov_val == r['evidence_path'], ('evidence_path mismatch', e, repr(cov_val), repr(r['evidence_path']))

    # ---- build modifications ----
    new_lines = list(lines)
    changes = []   # list of dicts
    for e in sorted(row_candidates.keys()):
        i = idx_of[e]
        oldrow = rows[i]
        old_val = oldrow[5]
        triples = row_candidates[e]

        # rebuild evidence_path, preserving separators and anchors
        out = []
        ti = 0
        for tok in SPLIT_KEEP_RE.split(old_val):
            if tok == '':
                continue
            if SPLIT_RE.fullmatch(tok):
                out.append(tok)
                continue
            part, rel, cand = triples[ti]
            assert tok == part, ('part mismatch', e, repr(tok), repr(part))
            assert strip_anchor(part) == rel
            assert part.startswith(rel), ('rel not prefix of part', e, part, rel)
            suffix = part[len(rel):]
            new_part = cand + suffix
            out.append(new_part)
            ti += 1
        assert ti == len(triples), (e, ti, len(triples))
        new_main = ''.join(out)

        annotation = ';M82 指针修复：原记 %s（缺卡目录），实为 %s' % (old_val, new_main)
        new_val = new_main + annotation

        # verify each part of new_main resolves on disk (r14-relative)
        for tok in SPLIT_RE.split(new_main):
            rp = strip_anchor(tok)
            if not rp:
                continue
            ap = os.path.join(R14, rp.replace('/', os.sep))
            assert os.path.isfile(ap), ('new path not file', e, rp, ap)

        changes.append({'entry': e, 'subsystem': oldrow[1], 'grade': oldrow[4],
                        'old_value': old_val, 'new_main': new_main, 'new_value': new_val,
                        'candidates': [c for _,_,c in triples],
                        'line_index': i + 1})  # data_lines index (0=header) -> 1-based in data_lines
        # replace col6 only in the corresponding data line (lines[0]=header, lines[1]=first data)
        data_line_no = i + 1   # lines index: 0 header, i+1 = row i
        raw = lines[data_line_no].rstrip('\r')
        f = raw.split('\t')
        assert len(f) == 8 and f[0] == e
        f[5] = new_val
        new_lines[data_line_no] = '\t'.join(f)

    assert len(changes) == 361, len(changes)

    # ---- byte-level diff check: only col6 of 361 rows changed ----
    old_text = '\n'.join(lines)
    new_text = '\n'.join(new_lines)
    assert old_text != new_text
    changed_idx = set(c['line_index'] for c in changes)
    for i, (a, b) in enumerate(zip(lines, new_lines)):
        if i in changed_idx:
            fa, fb = a.split('\t'), b.split('\t')
            assert len(fa) == len(fb) == 8
            assert all(fa[k] == fb[k] for k in [0,1,2,3,4,6,7]), ('non-col6 change at line', i)
        else:
            assert a == b, ('unexpected change at untouched line', i)

    # ---- write coverage.tsv ----
    new_cov_data = new_text.encode('utf-8')
    assert not new_cov_data.endswith(b'\n') and b'\r\n' not in new_cov_data
    with open(COV, 'wb') as fh:
        fh.write(new_cov_data)
    after_cov = state(COV)

    # ---- PANEL.md append M82 note after M81 disclosure ----
    before_pan_text = before_pan['data'].decode('utf-8')
    plines = before_pan_text.split('\n')
    m81_start = next(i for i, x in enumerate(plines) if 'M81 披露' in x)
    m81_end = next(i for i, x in enumerate(plines) if x.startswith('> ⇒ **引用 `[已证]` = 1,654 时必须带此限定'))
    assert m81_end - m81_start == 4, (m81_start, m81_end)
    assert 'classification_trace` 是分类追踪' in plines[m81_end]

    new_rok = 478 + len(changes)
    pct = 100.0 * new_rok / 1654
    m82_lines_text = (
        '> ✅ **M82 补记：`evidence_path` 卡目录前缀已修复（纯指针修复，判定未变）**\n'
        '> `EVID_RESOLVE` 查出 `R_MISSING` 374 行的根因是 `evidence_path` **丢了卡目录层**（`EVIDENCE/x.txt` 实为 `S10-K2/EVIDENCE/x.txt`）。已修复其中**唯一可还原**的行；歧义行未动并在 `MERGE_M82` 列出。\n'
        + '> ⇒ 证据可解析率（`R_OK`）由 478 / 1,654（28.90%）升至 **' + str(new_rok) + ' / 1,654（' + ('%.2f' % pct) + '%）**。**判定与计数均未变**，本次只让证据指针重新可用。'
    )
    m82_lines = m82_lines_text.split('\n')
    assert len(m82_lines) == 3 and all(x.startswith('> ') for x in m82_lines)

    plines[m81_end+1:m81_end+1] = m82_lines
    new_pan_text = '\n'.join(plines)
    new_pan_data = new_pan_text.encode('utf-8')
    assert new_pan_data.endswith(b'\n') and b'\r\n' not in new_pan_data
    # ensure only insertion
    assert new_pan_data.replace(('\n'.join(m82_lines) + '\n').encode('utf-8'), b'', 1) == before_pan['data']
    with open(PAN, 'wb') as fh:
        fh.write(new_pan_data)
    after_pan = state(PAN)
    m82_start_line = m81_end + 2   # 1-based line number in new PANEL
    m82_end_line = m82_start_line + 2

    # ---- save result payload for report writing / verification ----
    result = {
        'before': {
            'coverage.tsv': {k: before_cov[k] for k in ['mtime','mtime_iso','bytes','sha256']},
            'PANEL.md': {k: before_pan[k] for k in ['mtime','mtime_iso','bytes','sha256']},
        },
        'after': {
            'coverage.tsv': {k: after_cov[k] for k in ['mtime','mtime_iso','bytes','sha256']},
            'PANEL.md': {k: after_pan[k] for k in ['mtime','mtime_iso','bytes','sha256']},
        },
        'fix_count': len(changes),
        'ambiguous_count': cnt['ambiguous'],
        'new_rok': new_rok,
        'new_pct': pct,
        'm82_lines': [m82_start_line, m82_end_line],
        'changes': changes,
        'ambiguous_entries': sorted(e for e in rc if rc[e] == 'ambiguous'),
    }
    with open(os.path.join(MERGE, '_apply_result.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
        fh.write('\n')

    print('WROTE coverage.tsv: %d changes' % len(changes))
    print('WROTE PANEL.md M82 note at lines L%d-L%d' % (m82_start_line, m82_end_line))
    print('coverage before %s -> after %s' % (before_cov['sha256'][:8], after_cov['sha256'][:8]))
    print('PANEL   before %s -> after %s' % (before_pan['sha256'][:8], after_pan['sha256'][:8]))


if __name__ == '__main__':
    main()
