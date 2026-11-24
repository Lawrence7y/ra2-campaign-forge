# -*- coding: utf-8 -*-
"""
R16_F1_B3 — 独立复核 delta.tsv / fields.tsv（只读产物 + coverage.tsv）。
不写任何文件；只打印校验结果。
"""
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
DELTA = os.path.join(HERE, 'delta.tsv')
FIELDS = os.path.join(HERE, 'fields.tsv')

WITNESS = '④ 活表槽位见证'


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


def main():
    cov = load_cov_bytes()
    with open(DELTA, 'rb') as f:
        dlines = f.read().split(b'\n')
    hdr = dlines[0].decode('utf-8')
    rows = [ln for ln in dlines[1:] if ln]
    print('delta header:', hdr)
    print('delta data rows:', len(rows))

    ok = True
    for ln in rows:
        c = ln.split(b'\t')
        assert len(c) == 8, 'not 8 cols'
        e = c[0].decode('ascii').strip().upper()
        orig = cov.get(e)
        if orig is None:
            print('  !! entry not in coverage', e); ok = False; continue
        # 第 1/2/3/5/6/7/8 列逐字节相同
        for i in (0, 1, 2, 4, 5, 6, 7):
            if c[i] != orig[i]:
                print('  !! col%d differs for %s' % (i + 1, e)); ok = False
        # 第 4 列：原文严格前缀 + '；' + ④文本；原文不含 witness
        newsem = c[3]
        origsem = orig[3]
        if not newsem.startswith(origsem):
            print('  !! col4 not strict prefix for', e); ok = False
        if WITNESS.encode('utf-8') in origsem:
            print('  !! original already has witness for', e); ok = False
        if b'\xff' + WITNESS.encode('utf-8') not in newsem and WITNESS not in newsem.decode('utf-8', 'ignore'):
            print('  !! witness missing in new col4 for', e); ok = False
        # §12.6 指针必须存在，§12.4 不得出现（本条 ④ 段）
        if '§12.6' not in newsem.decode('utf-8', 'ignore'):
            print('  !! §12.6 missing for', e); ok = False
    print('delta byte-identity check:', 'PASS' if ok else 'FAIL')

    # fields.tsv 列数/行数/状态
    with open(FIELDS, 'rb') as f:
        flines = f.read().split(b'\n')
    fhdr = flines[0].decode('utf-8')
    frows = [ln for ln in flines[1:] if ln]
    print('fields header:', fhdr)
    print('fields data rows:', len(frows))
    n_ok = n_skip = 0
    field_entries = []
    for ln in frows:
        c = ln.split(b'\t')
        assert len(c) == 14, 'fields not 14 cols: %d' % len(c)
        field_entries.append(c[0].decode('ascii').upper())
        if c[11] == b'OK':
            n_ok += 1
        elif c[11] == b'SKIP':
            n_skip += 1
    print('fields OK/SKIP:', n_ok, '/', n_skip)

    # delta 与 fields entry 集合一致
    dents = [ln.split(b'\t')[0].decode('ascii').upper() for ln in rows]
    print('delta/fields entry sets equal:', set(dents) == set(field_entries))
    print('delta entries sorted asc:', dents == sorted(dents, key=lambda x: int(x, 16)))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
