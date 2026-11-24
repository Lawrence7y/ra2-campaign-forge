# -*- coding: utf-8 -*-
"""M83 phase 2 (WRITE): apply 4 subsystem-disambiguated pointer fixes to coverage.tsv col6
and append M83 note (2 lines) to PANEL.md after the M82 note.

Discipline:
  - only writes COVERAGE/coverage.tsv, COVERAGE/PANEL.md, and MERGE_M83/*
  - no git commit; no touching R14_COMMON / STATUS_BOARD / 台账 / BOARD_ARCHIVE / EVID_RESOLVE / any card dir
  - changes ONLY column 6 (evidence_path) of the 4 fixable rows
  - col 1/2/3/4/5/7/8 byte-identical for every row; all other rows byte-identical
"""
import os, re, json, hashlib, datetime

R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
PAN = os.path.join(R14, 'COVERAGE', 'PANEL.md')
MERGE = os.path.join(R14, 'MERGE_M83')
ATLAS = os.path.join(os.path.dirname(R14), 'next_re_20261112_r10', 'W130_atlas', 'function_atlas.tsv')
TZ = datetime.timezone(datetime.timedelta(hours=8))


def state(path):
    st = os.stat(path)
    b = open(path, 'rb').read()
    return {'mtime': st.st_mtime,
            'mtime_iso': datetime.datetime.fromtimestamp(st.st_mtime, TZ).isoformat(),
            'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest(), 'data': b}


def norm(e):
    return ('%08X' % int(e.strip(), 16)).upper()


def load_atlas_set():
    s = set()
    for i, raw in enumerate(open(ATLAS, 'r', encoding='utf-8').read().split('\n')):
        if i == 0 or not raw.strip():
            continue
        f = raw.replace('\r', '').split('\t')
        if f and re.match(r'^[0-9A-Fa-f]{8}$', f[0].strip()):
            s.add(norm(f[0]))
    return s


def main():
    analysis = json.load(open(os.path.join(MERGE, '_analysis.json'), 'r', encoding='utf-8'))
    detail = analysis['detail']
    fixed = [d for d in detail if d['fixable']]
    assert len(analysis['ambiguous_entries']) == 13 and analysis['m82_list_match']
    assert len(fixed) == 4 and len(analysis['unresolved_entries']) == 9

    before_cov = state(COV)
    before_pan = state(PAN)
    bs = analysis['before']
    assert before_cov['sha256'] == bs['coverage.tsv']['sha256'] == 'a5f4439ff7879f51a133c1cbdd24091d2e08abb0a80d04afdf2351fa753594ec'
    assert before_pan['sha256'] == bs['PANEL.md']['sha256'] == 'c78de479c4589d11c57452992a40fdcbf0295604e62c3dd2475e44f3da35b816'

    lines = before_cov['data'].decode('utf-8').split('\n')
    header = lines[0].split(',')
    assert header == ['entry', 'subsystem', 'name', 'one_line_semantics', 'grade',
                      'evidence_path', 'n_sources', 'conflict']
    rows = [ln.split('\t') for ln in lines[1:]]
    assert len(rows) == 18498
    assert sum(1 for r in rows if r[4] == '[已证]') == 1654
    atlas = load_atlas_set()
    assert sum(1 for r in rows if r[4] == '[已证]' and norm(r[0]) in atlas) == 1648
    entries = [r[0] for r in rows]
    assert len(set(entries)) == len(entries)

    idx_of = {r[0]: i for i, r in enumerate(rows)}
    new_lines = list(lines)
    changes = []
    for d in fixed:
        e = d['entry']
        i = idx_of[e]
        oldrow = rows[i]
        assert oldrow[4] == '[已证]' == d['grade']
        assert oldrow[5] == d['old_value'], (e, repr(oldrow[5]), repr(d['old_value']))
        assert oldrow[1] == d['subsystem']
        assert 'M82 指针修复' not in oldrow[5]
        new_main = d['new_path']
        # verify new_main resolves on disk (r14-relative)
        rp = new_main.split('#', 1)[0].strip()
        assert os.path.isfile(os.path.join(R14, rp.replace('/', os.sep))), (e, rp)
        # annotation
        mark = ';M83 歧义消解：原记 ' + oldrow[5] + '，按 subsystem=' + d['subsystem'] + ' 锁定为 ' + new_main
        new_val = new_main + mark
        data_line_no = i + 1   # lines index: 0 header, i+1 = row i
        raw = lines[data_line_no].rstrip('\r')
        f = raw.split('\t')
        assert len(f) == 8 and f[0] == e
        f[5] = new_val
        new_lines[data_line_no] = '\t'.join(f)
        changes.append({'entry': e, 'subsystem': d['subsystem'], 'grade': oldrow[4],
                        'old_value': oldrow[5], 'new_main': new_main, 'new_value': new_val,
                        'candidates': [h for pp in d['per_part'] if pp.get('status') == 'fixed' for h in pp['kept']],
                        'line_index': i + 1})

    assert len(changes) == 4

    # byte-level diff check: only col6 of 4 rows changed
    changed_idx = set(c['line_index'] for c in changes)
    for i, (a, b) in enumerate(zip(lines, new_lines)):
        if i in changed_idx:
            fa, fb = a.split('\t'), b.split('\t')
            assert len(fa) == len(fb) == 8
            assert all(fa[k] == fb[k] for k in [0, 1, 2, 3, 4, 6, 7]), ('non-col6 change at line', i)
        else:
            assert a == b, ('unexpected change at untouched line', i)

    # write coverage.tsv
    new_cov_data = '\n'.join(new_lines).encode('utf-8')
    assert not new_cov_data.endswith(b'\n') and b'\r\n' not in new_cov_data and new_cov_data[:3] != b'\xef\xbb\xbf'
    with open(COV, 'wb') as fh:
        fh.write(new_cov_data)
    after_cov = state(COV)

    # PANEL.md: insert 2 lines after M82 note
    before_pan_text = before_pan['data'].decode('utf-8')
    plines = before_pan_text.split('\n')
    m82_start = next(i for i, x in enumerate(plines) if 'M82 补记' in x)
    m82_end = next(i for i in range(m82_start, len(plines)) if 'R_OK' in plines[i] and '判定与计数均未变' in plines[i])
    assert m82_end - m82_start == 2, (m82_start, m82_end)
    assert '839 / 1,654' in plines[m82_end]

    new_rok = 839 + len(changes)  # 843
    pct = 100.0 * new_rok / 1654  # 50.97
    m83_lines_text = (
        '> ✅ **M83 补记：歧义指针消解（按 subsystem 锁定卡目录）**\n'
        '> M82 后剩 13 行因同名文件跨卡目录而歧义；已按「目录名含该行 subsystem 编号」消歧，'
        '修复 %d 行、%d 行仍未修（原因逐条列入 `MERGE_M83`）。'
        '证据可解析率（R_OK）现为 **%d / 1,654（%.2f%%）**。判定与计数未变。'
        % (len(changes), len(analysis['unresolved_entries']), new_rok, pct)
    )
    m83_lines = m83_lines_text.split('\n')
    assert len(m83_lines) == 2 and all(x.startswith('> ') for x in m83_lines)
    plines[m82_end + 1:m82_end + 1] = m83_lines
    new_pan_data = '\n'.join(plines).encode('utf-8')
    # ensure only insertion
    assert new_pan_data.replace(('\n'.join(m83_lines) + '\n').encode('utf-8'), b'', 1) == before_pan['data']
    with open(PAN, 'wb') as fh:
        fh.write(new_pan_data)
    after_pan = state(PAN)
    m83_start_line = m82_end + 2   # 1-based
    m83_end_line = m83_start_line + 1

    result = {
        'before': {k: bs[k] for k in ['coverage.tsv', 'PANEL.md']},
        'after': {
            'coverage.tsv': {k: after_cov[k] for k in ['mtime', 'mtime_iso', 'bytes', 'sha256']},
            'PANEL.md': {k: after_pan[k] for k in ['mtime', 'mtime_iso', 'bytes', 'sha256']},
        },
        'fix_count': len(changes),
        'unresolved_count': len(analysis['unresolved_entries']),
        'ambiguous_count': len(analysis['ambiguous_entries']),
        'ambiguous_entries': analysis['ambiguous_entries'],
        'new_rok': new_rok, 'new_pct': pct,
        'm83_lines': [m83_start_line, m83_end_line],
        'changes': changes,
        'unresolved_detail': [d for d in detail if not d['fixable']],
    }
    with open(os.path.join(MERGE, '_apply_result.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
        fh.write('\n')

    print('WROTE coverage.tsv: %d changes (%s)' % (len(changes), ', '.join(c['entry'] for c in changes)))
    print('WROTE PANEL.md M83 note at lines L%d-L%d' % (m83_start_line, m83_end_line))
    print('coverage before %s -> after %s' % (before_cov['sha256'][:8], after_cov['sha256'][:8]))
    print('PANEL   before %s -> after %s' % (before_pan['sha256'][:8], after_pan['sha256'][:8]))
    print('expected new R_OK = %d (%.2f%%)' % (new_rok, pct))


if __name__ == '__main__':
    main()
