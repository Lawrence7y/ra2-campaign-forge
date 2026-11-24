# -*- coding: utf-8 -*-
"""
R16_F1_B2 — 独立复核 delta.tsv / fields.tsv（只读 coverage.tsv / gamemd.exe）。
不写 coverage.tsv / 任何他人目录；只写本目录 verify_delta.json。
"""
import os
import sys
import json
import hashlib

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
EXE = os.path.join(os.path.dirname(os.path.dirname(R14)), 'ra2youli', 'gamemd.exe')
DELTA = os.path.join(HERE, 'delta.tsv')
FIELDS = os.path.join(HERE, 'fields.tsv')
OUT = os.path.join(HERE, 'verify_delta.json')

B2 = ['005FEAF0', '00629FD0', '0062D7A0', '0062D9A0',
      '0062FE90', '00630090', '00644960', '006457A0', '00645950',
      '006B5850', '006C2B10', '006C2C90', '006C2E10', '006C2F90',
      '006C3110', '006C3290', '006C3410', '006C3590']


def sha256p(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def loadcov():
    d = {}
    with open(COV, 'rb') as f:
        raw = f.read()
    for ln in raw.split(b'\n'):
        c = ln.split(b'\t')
        if len(c) != 8:
            continue
        e = c[0].decode('ascii', 'ignore').strip().upper()
        if e:
            d.setdefault(e, c)
    return d


def main():
    cov = loadcov()
    cov_sha = sha256p(COV)
    exe_sha = sha256p(EXE)

    with open(DELTA, 'rb') as f:
        dlines = f.read().split(b'\n')
    with open(FIELDS, 'rb') as f:
        flines = f.read().split(b'\n')

    # delta header 必须 TAB 8 列
    dh = dlines[0].decode('utf-8').split('\t')
    header_ok = (dh == ['entry', 'subsystem', 'name', 'one_line_semantics',
                        'grade', 'evidence_path', 'n_sources', 'conflict'])
    drows = [ln for ln in dlines[1:] if ln]
    entries = []
    errors = []
    for ln in drows:
        c = ln.split(b'\t')
        if len(c) != 8:
            errors.append(('col-count', len(c)))
            continue
        e = c[0].decode('ascii').upper()
        entries.append(e)
        if e not in cov:
            errors.append(('not-in-cov', e))
            continue
        orig = cov[e]
        for i in (0, 1, 2, 4, 5, 6, 7):
            if c[i] != orig[i]:
                errors.append(('col-diff', e, i + 1))
        if not c[3].startswith(orig[3]):
            errors.append(('col4-prefix', e))
        if len(c[3]) <= len(orig[3]):
            errors.append(('col4-empty-add', e))
        sem = c[3].decode('utf-8', 'ignore')
        if '④ 活表槽位见证' not in sem:
            errors.append(('no-witness', e))
        if '§12.6' not in sem:
            errors.append(('no-12.6', e))
        if '§12.4' in sem:
            errors.append(('has-12.4', e))
        if c[4] != '[已证]'.encode('utf-8'):
            errors.append(('grade-changed', e))

    # fields header 14 列（卡面 §5.2 含 same_source）
    fh = flines[0].decode('utf-8').split('\t')
    fields_header_ok = (fh == ['entry', 'class', 'slot_no', 'vtaddr',
                               'source_of_vtaddr', 'coladdr', 'col_offset',
                               'rtti_addr', 'rtti_mangled', 'install_site',
                               'install_func', 'status(OK|SKIP)', 'same_source',
                               'note'])
    frows = [ln for ln in flines[1:] if ln]
    fentries = []
    for ln in frows:
        c = ln.split(b'\t')
        if len(c) != 14:
            errors.append(('fields-col-count', len(c)))
            continue
        fentries.append(c[0].decode('ascii').upper())
        if c[11] != b'OK':
            errors.append(('fields-status', c[0], c[11]))
        if c[12] != b'no':
            errors.append(('fields-same_source', c[0], c[12]))

    print('delta header OK:', header_ok)
    print('fields header OK (14 col):', fields_header_ok)
    print('delta rows:', len(drows), 'entries:', len(entries), 'distinct:', len(set(entries)))
    print('fields rows:', len(frows), 'entries:', len(fentries), 'distinct:', len(set(fentries)))
    print('entry set == B2:', sorted(entries) == sorted(B2))
    print('fields entry set == delta entry set:', sorted(fentries) == sorted(entries))
    print('coverage.tsv sha256:', cov_sha, '(expect 0046BAD9...AA6ACF9)')
    print('gamemd.exe sha256:', exe_sha)
    print('ERRORS:', errors if errors else 'NONE')

    res = dict(delta_header_ok=header_ok, fields_header_ok=fields_header_ok,
               n_delta=len(drows), n_fields=len(frows),
               entry_set_eq_B2=(sorted(entries) == sorted(B2)),
               fields_eq_delta=(sorted(fentries) == sorted(entries)),
               cov_sha=cov_sha, exe_sha=exe_sha, errors=[str(e) for e in errors])
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print('wrote', OUT)
    return 0 if not errors and header_ok and fields_header_ok else 1


if __name__ == '__main__':
    sys.exit(main())
