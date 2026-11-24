# -*- coding: utf-8 -*-
"""
R16_F1_B5 — 独立复核 delta.tsv / fields.tsv（只读产物 + coverage.tsv + 四批 fields）。
不写任何文件；只打印校验结果。
"""
import os
import sys
import re
import hashlib

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
DELTA = os.path.join(HERE, 'delta.tsv')
FIELDS = os.path.join(HERE, 'fields.tsv')
DERIVED = os.path.join(HERE, 'derived_set.tsv')
BATCH_FIELDS = [os.path.join(R14, 'R16_F1_B%d' % k, 'fields.tsv') for k in (1, 2, 3, 4)]

WITNESS = '④ 活表槽位见证'
PRE4_MARK = '【改前第4列已含④='


def sha256p(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def load_cov_bytes():
    with open(COV, 'rb') as f:
        raw = f.read()
    d = {}
    for ln in raw.split(b'\n'):
        if not ln:
            continue
        c = ln.split(b'\t')
        if len(c) != 8:
            continue
        e = c[0].decode('ascii', 'ignore').strip().upper()
        if e:
            d.setdefault(e, c)
    return d


def batch_entries(path):
    out = set()
    with open(path, encoding='utf-8') as f:
        lines = f.read().splitlines()
    for ln in lines[1:]:
        if ln.strip():
            e = ln.split('\t')[0].strip().upper()
            if e:
                out.add(e)
    return out


def main():
    ok = True
    cov_sha = sha256p(COV)
    cov_bytes = os.path.getsize(COV)
    print('coverage.tsv sha256 (verify time):', cov_sha, 'bytes:', cov_bytes)
    cov = load_cov_bytes()
    with open(DELTA, 'rb') as f:
        dlines = f.read().split(b'\n')
    hdr = dlines[0].decode('utf-8')
    rows = [ln for ln in dlines[1:] if ln]
    print('delta header:', hdr)
    print('delta data rows:', len(rows))
    assert hdr == ('entry\tsubsystem\tname\tone_line_semantics\tgrade\t'
                   'evidence_path\tn_sources\tconflict')

    texts = []
    for ln in rows:
        c = ln.split(b'\t')
        assert len(c) == 8, 'not 8 cols'
        e = c[0].decode('ascii').strip().upper()
        orig = cov.get(e)
        if orig is None:
            print('  !! entry not in coverage', e); ok = False; continue
        for i in (0, 1, 2, 4, 5, 6, 7):
            if c[i] != orig[i]:
                print('  !! col%d differs for %s' % (i + 1, e)); ok = False
        # grade 必须逐字节 == [已证]
        if c[4] != '[已证]'.encode('utf-8'):
            print('  !! grade not [已证] for', e); ok = False
        newsem = c[3]
        origsem = orig[3]
        if not newsem.startswith(origsem):
            print('  !! col4 not strict prefix for', e); ok = False
        if WITNESS.encode('utf-8') in origsem:
            print('  !! original already has witness for', e); ok = False
        ns = newsem.decode('utf-8', 'ignore')
        if WITNESS not in ns:
            print('  !! witness missing in new col4 for', e); ok = False
        # ④ 段（追加部分）必须有 §12.6，且不得有 §12.4
        added = ns[len(origsem.decode('utf-8', 'ignore')):]
        if '§12.6' not in added:
            print('  !! §12.6 missing in added ④ for', e); ok = False
        if '§12.4' in added:
            print('  !! §12.4 wrongly present in added ④ for', e); ok = False
        texts.append(added)
    print('delta byte-identity check:', 'PASS' if ok else 'FAIL')

    # fields.tsv 列数/行数/状态 + 改前④标记
    with open(FIELDS, 'rb') as f:
        flines = f.read().split(b'\n')
    fhdr = flines[0].decode('utf-8')
    frows = [ln for ln in flines[1:] if ln]
    print('fields header:', fhdr)
    print('fields data rows:', len(frows))
    assert fhdr == ('entry\tclass\tslot_no\tvtaddr\tsource_of_vtaddr\tcoladdr\t'
                    'col_offset\trtti_addr\trtti_mangled\tinstall_site\t'
                    'install_func\tstatus(OK|SKIP)\tsame_source\tnote')
    n_ok = n_skip = n_pre4_marker = 0
    field_entries = []
    pre4_yes = []
    for ln in frows:
        c = ln.split(b'\t')
        assert len(c) == 14, 'fields not 14 cols: %d' % len(c)
        field_entries.append(c[0].decode('ascii').upper())
        if c[11] == b'OK':
            n_ok += 1
        elif c[11] == b'SKIP':
            n_skip += 1
        note = c[13].decode('utf-8', 'ignore')
        if PRE4_MARK in note:
            n_pre4_marker += 1
            if '已含④=是' in note:
                pre4_yes.append(c[0].decode('ascii').upper())
        if c[12] != b'no':
            print('  !! same_source not no for', c[0]); ok = False
    print('fields OK/SKIP:', n_ok, '/', n_skip)
    print('fields note 改前④标记:', n_pre4_marker, '/', len(frows),
          ' pre-existing-④=yes rows:', pre4_yes)
    if n_pre4_marker != len(frows):
        ok = False

    # delta 与 fields entry 集合一致
    dents = [ln.split(b'\t')[0].decode('ascii').upper() for ln in rows]
    print('delta/fields entry sets equal:', set(dents) == set(field_entries))
    print('delta entries sorted asc:', dents == sorted(dents, key=lambda x: int(x, 16)))
    if set(dents) != set(field_entries):
        ok = False

    # entry 集 == 派生集合第 73-76 行
    with open(DERIVED, encoding='utf-8') as f:
        dl = f.read().splitlines()
    derived_ents = [ln.split('\t')[0].strip().upper() for ln in dl[1:] if ln.strip()]
    expect_b5 = derived_ents[72:76]
    print('delta entries == derived rows 73-76:', set(dents) == set(expect_b5), expect_b5)
    if set(dents) != set(expect_b5):
        ok = False

    # 与 B1/B2/B3/B4 无交集；并集 == 76 行
    prior_sets = [batch_entries(p) for p in BATCH_FIELDS]
    inter = set()
    all_prior = set()
    for k, bs in enumerate(prior_sets, 1):
        hi = set(dents) & bs
        print('B5 ∩ B%d(fields):' % k, sorted(hi))
        inter |= hi
        all_prior |= bs
    if inter:
        ok = False
    print('B1..B4 ∪ B5 covers all 76 derived rows:',
          (all_prior | set(dents)) == set(derived_ents))

    # 行行不同（全文 + entry 归一）
    full = list(set(texts))
    norm = list(set(re.sub(r'[0-9A-F]{8}', 'ENTRY', t) for t in texts))
    print('④ text distinct full %d/%d, entry-normalized %d/%d' % (
        len(full), len(texts), len(norm), len(texts)))
    if len(full) != len(texts) or len(norm) != len(texts):
        ok = False

    print('\nFINAL:', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
