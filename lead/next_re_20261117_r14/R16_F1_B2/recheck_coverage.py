# -*- coding: utf-8 -*-
"""
R16_F1_B2 — 并发改写留痕复核：coverage.tsv sha 从 0046BAD9... 变为 95DFAC9...
在本脚本中确认：(a) 当前盘派生集合仍 76 行、B2 仍同 18 行；(b) 当前盘本批 18 行
grade==[已证] 且原第 4 列不含 witness；(c) delta 第1/2/3/5/6/7/8 列仍与当前盘逐字节同。
只写本目录 recheck_coverage.json；只读 coverage.tsv / gamemd.exe。
"""
import os
import sys
import json
import hashlib

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
AUDIT = os.path.join(R14, 'R16_PROBE_4GAP', 'scan_F1_audit.tsv')
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
DELTA = os.path.join(HERE, 'delta.tsv')
OUT = os.path.join(HERE, 'recheck_coverage.json')

WITNESS = '④ 活表槽位见证'
SHA_AT_DERIVE = '0046BAD980E9055AF61CC94DB9DA72C5346E087A49A00BA0009705807AA6ACF9'
SHA_AT_GEN = '0046BAD980E9055AF61CC94DB9DA72C5346E087A49A00BA0009705807AA6ACF9'
B2_EXPECT = ['005FEAF0', '00629FD0', '0062D7A0', '0062D9A0',
             '0062FE90', '00630090', '00644960', '006457A0', '00645950',
             '006B5850', '006C2B10', '006C2C90', '006C2E10', '006C2F90',
             '006C3110', '006C3290', '006C3410', '006C3590']


def sha256p(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def main():
    cov_sha = sha256p(COV)
    cov_bytes = os.path.getsize(COV)

    # load coverage
    cov = {}
    with open(COV, 'rb') as f:
        raw = f.read()
    for ln in raw.split(b'\n'):
        c = ln.split(b'\t')
        if len(c) != 8:
            continue
        e = c[0].decode('ascii', 'ignore').strip().upper()
        if e:
            cov.setdefault(e, c)

    # re-derive with CURRENT coverage
    with open(AUDIT, encoding='utf-8') as f:
        lines = f.read().splitlines()
    hdr = lines[0].split('\t')
    idx = {k: i for i, k in enumerate(hdr)}
    rows = [ln.split('\t') for ln in lines[1:] if ln.strip()]

    def cov_ok(r):
        e = r[idx['entry']].upper()
        c = cov.get(e)
        g, sem = (c[4], c[3]) if c is not None else (None, b'')
        return g == '[已证]'.encode('utf-8') and WITNESS.encode('utf-8') not in sem

    derived = [r for r in rows
               if r[idx['same_source']] == 'no'
               and int(r[idx['n_install_decoded']]) >= 1
               and int(r[idx['n_install_outside_body']]) >= 1
               and cov_ok(r)]
    derived.sort(key=lambda r: int(r[idx['entry']], 16))
    ents = [r[idx['entry']].upper() for r in derived]
    b1, b2 = ents[:18], ents[18:36]

    # delta vs current coverage
    with open(DELTA, 'rb') as f:
        dl = [ln for ln in f.read().split(b'\n')[1:] if ln]
    col_ok = True
    grade_ok = True
    prefix_ok = True
    for ln in dl:
        c = ln.split(b'\t')
        e = c[0].decode('ascii').upper()
        o = cov.get(e)
        if o is None:
            col_ok = False
            continue
        for i in (0, 1, 2, 4, 5, 6, 7):
            if c[i] != o[i]:
                col_ok = False
        grade_ok = (c[4] == '[已证]'.encode('utf-8') and o[4] == '[已证]'.encode('utf-8'))
        if not c[3].startswith(o[3]):
            prefix_ok = False

    res = dict(
        sha_at_derive=SHA_AT_DERIVE, bytes_at_derive=4034144,
        sha_at_gen=SHA_AT_GEN, bytes_at_gen=4034144,
        sha_now=cov_sha, bytes_now=cov_bytes,
        sha_changed=(cov_sha != SHA_AT_GEN),
        derived_count_now=len(ents),
        b1_now=b1, b2_now=b2,
        b2_unchanged=(b2 == B2_EXPECT),
        b1_b2_intersect=sorted(set(b1) & set(b2)),
        criterion4_dropped_now=0,
        delta_cols_vs_current_coverage=col_ok,
        delta_grade_ok=grade_ok, delta_col4_prefix_ok=prefix_ok,
    )
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)

    print('sha at derive :', SHA_AT_DERIVE, '(4034144 B)')
    print('sha at gen    :', SHA_AT_GEN, '(4034144 B)')
    print('sha now       :', cov_sha, '(%d B)' % cov_bytes)
    print('sha changed   :', res['sha_changed'])
    print('derived count now :', len(ents))
    print('B2 unchanged  :', res['b2_unchanged'])
    print('B1∩B2         :', res['b1_b2_intersect'])
    print('delta cols vs current coverage :', col_ok)
    print('delta grade/prefix ok:', grade_ok, prefix_ok)
    print('wrote', OUT)
    return 0


if __name__ == '__main__':
    sys.exit(main())
