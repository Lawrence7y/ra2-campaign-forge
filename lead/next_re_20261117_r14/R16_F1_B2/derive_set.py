# -*- coding: utf-8 -*-
"""
R16_F1_B2 — 独立派生 F1 缺口集合（判据见卡面 §3 第一步）。

权威输入：R16_PROBE_4GAP/scan_F1_audit.tsv
背景报告：R16_PROBE_4GAP/REPORT.md

四条判据（卡面 §3）：
  1) same_source == no
  2) ring4_at 能解析出装表指令 mov <mem>, imm32 且 imm32 指向该行活表
     —— TSV 代理列：n_install_decoded >= 1（audit_ring4_ctor_install）
  3) 装表点位于 entry 体外（装表点所在函数 != entry）
     —— TSV 代理列：n_install_outside_body >= 1
  4) 现盘 coverage.tsv grade==[已证] 且第 4 列不含 "④ 活表槽位见证"

按 entry 升序排序；B1=第1-18行，B2=第19-36行。报告各阶段计数 + 命中总数，
并与卡面转述的 76 比对。只读：不写 coverage.tsv / 任何他人目录。
"""
import os
import sys
import hashlib

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
AUDIT = os.path.join(R14, 'R16_PROBE_4GAP', 'scan_F1_audit.tsv')
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')

WITNESS = '④ 活表槽位见证'


def sha256p(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def load_cov():
    """entry -> (grade, sem4)。数据行是 TAB 分隔 8 列；表头是逗号（已知坑，跳过）。"""
    d = {}
    with open(COV, 'rb') as f:
        raw = f.read()
    for ln in raw.split(b'\n'):
        if not ln:
            continue
        c = ln.split(b'\t')
        if len(c) != 8:
            continue                      # 跳逗号表头
        e = c[0].decode('ascii', 'ignore').strip().upper()
        if not e:
            continue
        d.setdefault(e, (c[4].decode('utf-8', 'ignore'),
                         c[3].decode('utf-8', 'ignore')))
    return d


def main():
    cov_sha = sha256p(COV)
    cov_bytes = os.path.getsize(COV)
    cov = load_cov()

    with open(AUDIT, encoding='utf-8') as f:
        lines = f.read().splitlines()
    hdr = lines[0].split('\t')
    idx = {k: i for i, k in enumerate(hdr)}
    data = [ln.split('\t') for ln in lines[1:] if ln.strip()]
    print('audit data rows:', len(data))
    print('coverage.tsv sha256:', cov_sha, 'bytes:', cov_bytes)

    # 阶段计数
    s0 = data
    s1 = [r for r in s0 if r[idx['same_source']] == 'no']
    s2 = [r for r in s1 if int(r[idx['n_install_decoded']]) >= 1]
    s3 = [r for r in s2 if int(r[idx['n_install_outside_body']]) >= 1]

    def cov_ok(r):
        e = r[idx['entry']].upper()
        g, sem = cov.get(e, (None, None))
        return (g == '[已证]') and (WITNESS not in sem)

    s4 = [r for r in s3 if cov_ok(r)]

    print('stage counts:')
    print('  S0 all F1 gap rows            :', len(s0))
    print('  S1 same_source==no            :', len(s1))
    print('  S2 +ring4_at install decoded  :', len(s2))
    print('  S3 +install outside entry body:', len(s3))
    print('  S4 +coverage [已证] & no witness:', len(s4), '  <== derived set')

    # 被 criterion 4 剔除的行（若有）
    dropped4 = [r[idx['entry']] for r in s3 if not cov_ok(r)]
    print('  dropped by criterion 4:', len(dropped4), dropped4[:20])

    # 分布自检
    from collections import Counter
    print('  f_reason distribution in S4:', dict(Counter(r[idx['f_reason']] for r in s4)))
    print('  sem_unproved in S4:', dict(Counter(r[idx['sem_unproved']] for r in s4)))

    # entry 升序排序（数值）
    s4s = sorted(s4, key=lambda r: int(r[idx['entry']], 16))
    ents = [r[idx['entry']].upper() for r in s4s]
    assert len(ents) == len(set(ents)), 'duplicate entry in derived set'

    b1 = ents[0:18]
    b2 = ents[18:36]
    print('\nsorted derived set entries (1..%d):' % len(ents))
    for i, e in enumerate(ents, 1):
        tag = '  <== B1' if i <= 18 else ('  <== B2' if i <= 36 else '')
        r = next(x for x in s4s if x[idx['entry']].upper() == e)
        print('%2d %s  %-8s %-50s %s%s' % (
            i, e, r[idx['subsystem']], r[idx['name']][:50],
            r[idx['ring4_at']][:40], tag))

    print('\nB1 count:', len(b1), 'B2 count:', len(b2))
    print('B1∩B2:', sorted(set(b1) & set(b2)))
    print('B1 entries:', b1)
    print('B2 entries:', b2)
    print('\nDerived-set HIT COUNT:', len(ents), '(card transcribed 76)')
    print('B2 (rows 19-36) entries:', b2)


if __name__ == '__main__':
    main()
