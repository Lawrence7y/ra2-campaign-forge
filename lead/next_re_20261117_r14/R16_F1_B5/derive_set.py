# -*- coding: utf-8 -*-
"""
R16_F1_B5 — 独立派生 F1 缺口集合（判据见卡面 §3 第一步）。收官批：第 73-76 行。

权威输入：R16_PROBE_4GAP/scan_F1_audit.tsv
背景报告：R16_PROBE_4GAP/REPORT.md

四条判据（卡面 §3）：
  1) same_source == no
  2) ring4_at 能解析出装表指令 mov <mem>, imm32 且 imm32 指向该行活表
     —— TSV 代理列：n_install_decoded >= 1（f_reason=audit_ring4_ctor_install）
  3) 装表点位于 entry 体外（装表点所在函数 != entry）
     —— TSV 代理列：n_install_outside_body >= 1
  4) 现盘 coverage.tsv grade==[已证] 且第 4 列不含 "④ 活表槽位见证"

按 entry 升序排序；B1=1..18, B2=19..36, B3=37..54, B4=55..72, **B5=73..76**（本批，收官）。
硬要求：B5 与 B1/B2/B3/B4 的 entry 集合（各 fields.tsv 第 1 列）交集均为空；
B1∪B2∪B3∪B4∪B5 == 76 行派生集合。
只读：不写 coverage.tsv / 任何他人目录；只写本目录 derived_set.tsv + 控制台报告。
"""
import os
import sys
import hashlib
from collections import Counter

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
AUDIT = os.path.join(R14, 'R16_PROBE_4GAP', 'scan_F1_audit.tsv')
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
BATCH_FIELDS = [os.path.join(R14, 'R16_F1_B%d' % k, 'fields.tsv') for k in (1, 2, 3, 4)]
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
    print('  S4 +coverage [已证] & no witness:', len(s4), '  <== clean-now count')
    dropped4 = [r[idx['entry']] for r in s3 if not cov_ok(r)]
    print('  dropped by criterion 4:', len(dropped4), dropped4[:20])

    print('  f_reason distribution in S3:', dict(Counter(r[idx['f_reason']] for r in s3)))
    print('  sem_unproved in S3:', dict(Counter(r[idx['sem_unproved']] for r in s3)))
    base = s3
    print('\n  [batch-defining base set = S3, criteria 1-3]:', len(base))
    print('  [criterion-4 clean-now subset]:', len(s4),
          '(dropped/already-merged:', len(dropped4), ')')

    s4s = sorted(base, key=lambda r: int(r[idx['entry']], 16))
    ents = [r[idx['entry']].upper() for r in s4s]
    assert len(ents) == len(set(ents)), 'duplicate entry in derived set'

    b5_check = [(r[idx['entry']].upper(), cov_ok(r)) for r in s4s[72:76]]
    print('  B5 rows clean on current disk:', sum(1 for _e, ok in b5_check if ok), '/', len(b5_check))

    batch_sets = [load_batch_entries(p) for p in BATCH_FIELDS]
    for k, s in enumerate(batch_sets, 1):
        print('B%d fields entries:' % k, len(s))

    def tag(i):
        if i <= 18:
            return '<== B1'
        if i <= 36:
            return '<== B2'
        if i <= 54:
            return '<== B3'
        if i <= 72:
            return '<== B4'
        if i <= 76:
            return '<== B5 (this batch)'
        return ''

    print('\nsorted derived set entries (1..%d):' % len(ents))
    for i, r in enumerate(s4s, 1):
        print('%2d %s  %-5s %-52s %s' % (
            i, r[idx['entry']].upper(), r[idx['subsystem']],
            r[idx['name']][:52], tag(i)))

    slices = {
        'B1': ents[0:18], 'B2': ents[18:36], 'B3': ents[36:54],
        'B4': ents[54:72], 'B5': ents[72:76],
    }
    for k in (1, 2, 3, 4):
        print('B%d(rows %d-%d) matches fields.tsv:' % (
            k, (k - 1) * 18 + 1, k * 18), set(slices['B%d' % k]) == batch_sets[k - 1])

    b5s = set(slices['B5'])
    print('\nB5(73-76) entries:', slices['B5'])
    all_prior = set()
    for k, bs in enumerate(batch_sets, 1):
        inter = sorted(b5s & bs)
        print('B5 ∩ B%d(fields):' % k, inter)
        assert not inter, 'B5 intersects B%d!' % k
        all_prior |= bs

    covered = all_prior | b5s
    print('\nB1∪B2∪B3∪B4∪B5 entries:', len(covered),
          '(derived base set:', len(ents), ')')
    print('union == derived base set:', covered == set(ents))
    print('B5 subset of derived set:', b5s <= set(ents))
    assert covered == set(ents), 'prior batches + B5 do not cover all 76 rows!'
    assert all(ok for _e, ok in b5_check), 'B5 rows not all clean on current disk!'

    print('\n=== BATCH-DEFINING BASE SET HIT COUNT:', len(ents), '(card transcribed 76) ===')
    print('B5 (rows 73-76) entries (%d):' % len(slices['B5']))
    for i, e in enumerate(slices['B5'], 73):
        r = next(x for x in s4s if x[idx['entry']].upper() == e)
        print('  %2d %s  %-5s %s' % (i, e, r[idx['subsystem']], r[idx['name']]))

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
