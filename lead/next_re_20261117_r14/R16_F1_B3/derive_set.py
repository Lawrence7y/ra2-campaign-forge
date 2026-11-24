# -*- coding: utf-8 -*-
"""
R16_F1_B3 — 独立派生 F1 缺口集合（判据见卡面 §3 第一步）。

权威输入：R16_PROBE_4GAP/scan_F1_audit.tsv
背景报告：R16_PROBE_4GAP/REPORT.md

四条判据（卡面 §3）：
  1) same_source == no
  2) ring4_at 能解析出装表指令 mov <mem>, imm32 且 imm32 指向该行活表
     —— TSV 代理列：n_install_decoded >= 1（f_reason=audit_ring4_ctor_install）
  3) 装表点位于 entry 体外（装表点所在函数 != entry）
     —— TSV 代理列：n_install_outside_body >= 1
  4) 现盘 coverage.tsv grade==[已证] 且第 4 列不含 "④ 活表槽位见证"

按 entry 升序排序；B1=第1-18行，B2=第19-36行，B3=第37-54行。
硬要求：B3 与 B1(R16_F1_B1/fields.tsv)、B2(R16_F1_B2/fields.tsv) 的 entry 集合交集为空。
只读：不写 coverage.tsv / 任何他人目录；只写本目录 derived_set.tsv + 控制台报告。
"""
import os
import sys
import hashlib

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
AUDIT = os.path.join(R14, 'R16_PROBE_4GAP', 'scan_F1_audit.tsv')
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
B1F = os.path.join(R14, 'R16_F1_B1', 'fields.tsv')
B2F = os.path.join(R14, 'R16_F1_B2', 'fields.tsv')
OUT = os.path.join(HERE, 'derived_set.tsv')

WITNESS = '④ 活表槽位见证'


def sha256p(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def load_cov():
    """entry -> (grade, sem4)。数据行 TAB 分隔 8 列；表头是逗号（已知坑，跳过）。"""
    d = {}
    with open(COV, 'rb') as f:
        raw = f.read()
    for ln in raw.split(b'\n'):
        if not ln:
            continue
        c = ln.split(b'\t')
        if len(c) != 8:
            continue
        e = c[0].decode('ascii', 'ignore').strip().upper()
        if not e:
            continue
        d.setdefault(e, (c[4].decode('utf-8', 'ignore'),
                         c[3].decode('utf-8', 'ignore')))
    return d


def load_batch_entries(path):
    """读 fields.tsv 第 1 列 entry 集合（跳表头）。"""
    out = set()
    with open(path, encoding='utf-8') as f:
        lines = f.read().splitlines()
    for ln in lines[1:]:
        if not ln.strip():
            continue
        e = ln.split('\t')[0].strip().upper()
        if e:
            out.add(e)
    return out


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
    print('  S0 all F1 gap rows             :', len(s0))
    print('  S1 same_source==no             :', len(s1))
    print('  S2 +ring4 install decoded      :', len(s2))
    print('  S3 +install outside entry body :', len(s3))
    print('  S4 +coverage [已证] & no witness:', len(s4), '  <== derived set')

    dropped4 = [r[idx['entry']] for r in s3 if not cov_ok(r)]
    print('  dropped by criterion 4:', len(dropped4), dropped4[:20])

    from collections import Counter
    print('  f_reason distribution in S4:', dict(Counter(r[idx['f_reason']] for r in s4)))
    print('  sem_unproved in S4:', dict(Counter(r[idx['sem_unproved']] for r in s4)))

    # entry 升序（数值）
    s4s = sorted(s4, key=lambda r: int(r[idx['entry']], 16))
    ents = [r[idx['entry']].upper() for r in s4s]
    assert len(ents) == len(set(ents)), 'duplicate entry in derived set'

    b1_set = load_batch_entries(B1F)
    b2_set = load_batch_entries(B2F)
    print('\nB1 fields entries:', len(b1_set))
    print('B2 fields entries:', len(b2_set))

    # 报告命中数与 B1/B2 的对应（B1=1..18, B2=19..36）
    print('\nsorted derived set entries (1..%d):' % len(ents))
    for i, r in enumerate(s4s, 1):
        tag = ''
        if i <= 18:
            tag = '  <== B1'
        elif i <= 36:
            tag = '  <== B2'
        elif i <= 54:
            tag = '  <== B3'
        print('%2d %s  %-5s %-52s %s%s' % (
            i, r[idx['entry']].upper(), r[idx['subsystem']],
            r[idx['name']][:52], r[idx['ring4_at']][:40], tag))

    b1_ents = ents[0:18]
    b2_ents = ents[18:36]
    b3_ents = ents[36:54]
    print('\nB1(1-18) matches fields.tsv:', set(b1_ents) == b1_set)
    print('B2(19-36) matches fields.tsv:', set(b2_ents) == b2_set)
    print('B1∩B2:', sorted(set(b1_ents) & set(b2_ents)))

    # 硬交集检查：B3 与 B1/B2 的 fields entry 集合交集必须为空
    b3s = set(b3_ents)
    inter_b1 = sorted(b3s & b1_set)
    inter_b2 = sorted(b3s & b2_set)
    print('B3 ∩ B1(fields):', inter_b1)
    print('B3 ∩ B2(fields):', inter_b2)
    assert not inter_b1 and not inter_b2, 'B3 intersects B1/B2!'
    assert b3s <= set(ents), 'B3 not subset of derived set'

    print('\n=== DERIVED SET HIT COUNT:', len(ents), '(card transcribed 76) ===')
    print('B3 (rows 37-54) entries (%d):' % len(b3_ents))
    for i, e in enumerate(b3_ents, 37):
        r = next(x for x in s4s if x[idx['entry']].upper() == e)
        print('  %2d %s  %-5s %s' % (i, e, r[idx['subsystem']], r[idx['name']]))

    # 写本目录 derived_set.tsv（供复核，不作为产物交付但留存）
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('entry\tsubsystem\tname\taudit_dir\tring4_at\n')
        for r in s4s:
            f.write('\t'.join([r[idx['entry']].upper(), r[idx['subsystem']],
                               r[idx['name']], r[idx['audit_dir']],
                               r[idx['ring4_at']]]) + '\n')
    print('wrote', OUT)
    return 0


if __name__ == '__main__':
    sys.exit(main())
