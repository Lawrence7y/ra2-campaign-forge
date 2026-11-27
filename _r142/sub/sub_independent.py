#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R142 blind independent recomputation.

Reads ONLY:
  - lead/next_re_20261117_r14/R17_R111_FACTINDEX_V539/FACT_INDEX.tsv
  - _ext/f_partial_triage/TRIAGE.tsv
  - the 10 version FACT_INDEX.tsv files matched by glob
Does NOT read or import r142a_tier_audit.py / r142b_version_drift.py.
"""
import csv
import glob
import hashlib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # repo root

V539 = os.path.join('lead', 'next_re_20261117_r14',
                    'R17_R111_FACTINDEX_V539', 'FACT_INDEX.tsv')
TRIAGE = os.path.join('_ext', 'f_partial_triage', 'TRIAGE.tsv')
VERSION_GLOB = os.path.join('lead', 'next_re_20261117_r14',
                            'R17_R1??_FACTINDEX_V5??', 'FACT_INDEX.tsv')


def digest(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return None
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def norm_paths(field):
    """Split by ';', backslash->slash, cut at first '(', strip; skip empties.
    Returns (nonempty_paths, raw_segment_count)."""
    out = []
    raw = 0
    for seg in field.split(';'):
        raw += 1
        p = seg.replace('\\', '/')
        if '(' in p:
            p = p.split('(', 1)[0]
        p = p.strip()
        if p == '':
            continue
        out.append(p)
    return out, raw


def classify(evidence_field):
    paths, raw = norm_paths(evidence_field)
    n = len(paths)
    alive = sum(1 for p in paths if os.path.exists(os.path.join(ROOT, p)))
    if alive == 0:
        kind = 'dead'
    elif alive == n:
        kind = 'alive'
    else:
        kind = 'partial'
    return {'alive': alive, 'n': n, 'raw_segments': raw, 'kind': kind,
            'paths': paths}


def read_tsv(rel):
    p = os.path.join(ROOT, rel)
    with open(p, 'r', encoding='utf-8', newline='') as f:
        rows = list(csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE))
    if not rows:
        return [], []
    return rows[0], rows[1:]


def version_key(d):
    m = re.search(r'_V(\d+)$', os.path.basename(d))
    return int(m.group(1)) if m else 0


def main():
    result = {
        'repo_root': ROOT,
        'input_sha256': {
            'v539': digest(V539),
            'triage': digest(TRIAGE),
        },
        'criteria': {
            'path_rule': "split(';'); '\\'->'/'; cut at first '('; strip; skip empty; os.path.exists(ROOT/p)",
            'class_rule': 'alive==0 -> dead; alive==n -> alive; 0<alive<n -> partial',
        },
    }

    # ---- ledger parsing (v5.39) ----
    hdr, facts = read_tsv(V539)
    idx = {name: i for i, name in enumerate(hdr)}
    fid_col = idx['fact_id']
    ev_col = idx['evidence_paths']
    bad_width = [i + 2 for i, r in enumerate(facts) if len(r) <= ev_col]
    fids = [r[fid_col] for r in facts if len(r) > fid_col]

    result['item1_ledger_rows'] = {
        'header_fields': hdr,
        'physical_newline_count': open(os.path.join(ROOT, V539), 'rb').read().count(b'\n'),
        'data_rows': len(facts),
        'unique_fact_ids': len(set(fids)),
        'min_fid': min(fids) if fids else None,
        'max_fid': max(fids) if fids else None,
        'malformed_rows_1based': bad_width,
    }

    v539_stats = []
    for r in facts:
        c = classify(r[ev_col])
        c['fact_id'] = r[fid_col]
        v539_stats.append(c)

    v539_partial = [c['fact_id'] for c in v539_stats if c['kind'] == 'partial']
    v539_dead = [c['fact_id'] for c in v539_stats if c['kind'] == 'dead']
    v539_alive = [c['fact_id'] for c in v539_stats if c['kind'] == 'alive']

    result['item2_partial_count_v539'] = len(v539_partial)
    result['item3_dead_fact_ids_v539'] = v539_dead
    result['v539_alive_fact_ids'] = v539_alive
    result['v539_kind_histogram'] = {
        'dead': len(v539_dead), 'partial': len(v539_partial), 'alive': len(v539_alive),
    }

    # ---- triage parsing ----
    thdr, trows = read_tsv(TRIAGE)
    tidx = {name: i for i, name in enumerate(thdr)}
    tri_fids = [r[tidx['fid']] for r in trows]
    result['triage_fid_count'] = len(tri_fids)
    result['triage_fids'] = tri_fids

    # item 4: alive_paths declared count / actually missing
    alive_all, alive_raw_all = [], 0
    for r in trows:
        ps, raw = norm_paths(r[tidx['alive_paths']])
        alive_all.extend(ps)
        alive_raw_all += raw
    alive_missing = [p for p in alive_all if not os.path.exists(os.path.join(ROOT, p))]
    result['item4_triage_alive_paths'] = {
        'raw_semicolon_segments_total': alive_raw_all,
        'declared_nonempty_path_count': len(alive_all),
        'actually_not_on_disk_count': len(alive_missing),
        'actually_not_on_disk_paths': alive_missing,
    }

    # item 5: lost_primary declared count / actually still present
    lost_all, lost_raw_all = [], 0
    for r in trows:
        ps, raw = norm_paths(r[tidx['lost_primary']])
        lost_all.extend(ps)
        lost_raw_all += raw
    lost_still = [p for p in lost_all if os.path.exists(os.path.join(ROOT, p))]
    result['item5_triage_lost_primary'] = {
        'raw_semicolon_segments_total': lost_raw_all,
        'declared_nonempty_path_count': len(lost_all),
        'actually_still_on_disk_count': len(lost_still),
        'actually_still_on_disk_paths': lost_still,
    }

    # item 6: fids with empty lost_primary + their verdicts
    empty_lp = []
    for r in trows:
        raw_field = r[tidx['lost_primary']]
        ps, _ = norm_paths(raw_field)
        if len(ps) == 0:
            empty_lp.append({'fid': r[tidx['fid']],
                             'verdict': r[tidx['verdict']],
                             'lost_primary_raw': raw_field})
    result['item6_empty_lost_primary'] = empty_lp

    # ---- item 7 / 8: version sweep ----
    version_files = sorted(glob.glob(os.path.join(ROOT, VERSION_GLOB)))
    version_files.sort(key=version_key)
    tri_set = set(tri_fids)
    seq, diffs = [], []
    for full in version_files:
        rel = os.path.relpath(full, ROOT)
        ver = os.path.basename(os.path.dirname(full))
        _, rows = read_tsv(rel)
        pids = []
        for r in rows:
            c = classify(r[ev_col])
            if c['kind'] == 'partial':
                pids.append(r[fid_col])
        pset = set(pids)
        seq.append({'version_dir': ver, 'data_rows': len(rows),
                    'partial_count': len(pids), 'partial_fids': sorted(pset)})
        tri_only = sorted(tri_set - pset)
        partial_only = sorted(pset - tri_set)
        if tri_only or partial_only:
            diffs.append({'version_dir': ver,
                          'triage_minus_partial': tri_only,
                          'partial_minus_triage': partial_only})
    result['item7_version_partial_counts'] = [
        {'version_dir': x['version_dir'], 'partial_count': x['partial_count']}
        for x in seq
    ]
    result['item7_version_partial_sequence'] = [x['partial_count'] for x in seq]
    result['item7_version_partial_full'] = seq
    result['item8_nonempty_diffs'] = diffs

    out_path = os.path.join(HERE, 'sub_result.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write('\n')

    print(json.dumps(result, ensure_ascii=False, indent=2))
    print('\n===== SELF-CHECK =====')
    print('1. 台账行数: 数据行 %d（物理换行 %d，唯一 fid %d，%s..%s），表头字段 %s'
          % (result['item1_ledger_rows']['data_rows'],
             result['item1_ledger_rows']['physical_newline_count'],
             result['item1_ledger_rows']['unique_fact_ids'],
             result['item1_ledger_rows']['min_fid'],
             result['item1_ledger_rows']['max_fid'],
             ','.join(hdr)))
    print('2. v5.39 partial 个数: %d' % result['item2_partial_count_v539'])
    print('3. dead fact_id 列表: %s' % json.dumps(v539_dead, ensure_ascii=False))
    print('4. TRIAGE alive_paths 声明路径总条数: %d（非空语义；原始分号段 %d）；实际不在盘: %d 条 -> %s'
          % (result['item4_triage_alive_paths']['declared_nonempty_path_count'],
             result['item4_triage_alive_paths']['raw_semicolon_segments_total'],
             result['item4_triage_alive_paths']['actually_not_on_disk_count'],
             json.dumps(alive_missing, ensure_ascii=False)))
    print('5. TRIAGE lost_primary 声明路径总条数: %d（非空语义；原始分号段 %d）；实际仍在盘: %d 条 -> %s'
          % (result['item5_triage_lost_primary']['declared_nonempty_path_count'],
             result['item5_triage_lost_primary']['raw_semicolon_segments_total'],
             result['item5_triage_lost_primary']['actually_still_on_disk_count'],
             json.dumps(lost_still, ensure_ascii=False)))
    print('6. lost_primary 为空的 fid 及 verdict: %s'
          % json.dumps([{'fid': x['fid'], 'verdict': x['verdict']} for x in empty_lp],
                       ensure_ascii=False))
    print('7. 10 版本 partial 计数（版本号升序）: %s ; 序列 %s'
          % (json.dumps(result['item7_version_partial_counts'], ensure_ascii=False),
             json.dumps(result['item7_version_partial_sequence'])))
    print('8. TRIAGE 32 fid 与版本 partial 集合的非空差集: %s'
          % json.dumps(diffs, ensure_ascii=False))
    print('写盘: %s' % out_path)


if __name__ == '__main__':
    main()
